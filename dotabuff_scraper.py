import time
import pandas as pd
import undetected_chromedriver as uc
from selenium.webdriver.common.by import By
from selenium.common.exceptions import NoSuchElementException, TimeoutException
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

# --- Configuração ---
PLAYER_IDS = ['1457931980', '254577873']
BASE_URL = 'https://www.dotabuff.com/players/{player_id}/matches?page={page}'


def setup_driver():
    """Configura e retorna uma instância do WebDriver do Chrome com opções para rodar em modo headless."""
    options = uc.ChromeOptions()
    # --- MUDANÇA: Adiciona o modo headless para rodar sem abrir a janela do navegador ---
    options.add_argument('--headless')
    options.add_argument('--window-size=1920,1080')  # Garante uma resolução consistente

    # Opções para evitar detecção
    options.add_argument("--disable-blink-features=AutomationControlled")

    # Usamos version_main para garantir compatibilidade com a versão do seu Chrome
    driver = uc.Chrome(options=options, version_main=138)

    return driver


def scrape_player_matches(driver, player_id, account_number):  # <--- Esta é a função para substituir
    """
    Raspa os dados de todas as partidas de um jogador, de forma totalmente automática.
    """
    player_matches = []
    page = 1

    first_page_url = BASE_URL.format(player_id=player_id, page=1)
    # --- MUDANÇA: Mensagem de progresso ajustada para ficar mais pessoal ---
    print(f"\nIniciando coleta da sua Conta {account_number} (ID: {player_id}).")
    print(f"Navegando para a primeira página...")
    driver.get(first_page_url)

    try:
        WebDriverWait(driver, 45).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, 'table.sortable tbody tr'))
        )
        print("Acesso bem-sucedido! Iniciando a coleta de dados...")
    except TimeoutException:
        print("\n" + "!" * 50)
        print(f"!! ERRO: A página para a conta com ID {player_id} não carregou a tabela de partidas a tempo.")
        print("!! O site pode estar lento ou bloqueando o acesso. Pulando para a próxima conta.")
        print("!" * 50)
        return []

    # Loop para coletar dados de todas as páginas
    while True:
        if page > 1:
            url = BASE_URL.format(player_id=player_id, page=page)
            print(f"Navegando para a página {page}...")
            driver.get(url)
            time.sleep(2)

        match_rows = driver.find_elements(By.CSS_SELECTOR, 'table.sortable tbody tr')

        if not match_rows:
            print(f"Não foram encontradas mais partidas. Finalizando para a Conta {account_number}.")
            break

        for row in match_rows:
            try:
                cols = row.find_elements(By.TAG_NAME, 'td')
                if not cols or len(cols) < 6: continue

                hero = cols[1].find_element(By.TAG_NAME, 'a').text
                result = cols[3].find_element(By.TAG_NAME, 'a').text
                game_mode = cols[4].text.split('\n')[0]
                duration = cols[5].text
                start_time = cols[3].find_element(By.TAG_NAME, 'time').get_attribute('datetime')

                player_matches.append({
                    'Conta': f'Conta {account_number}',
                    'ID da Conta': player_id, 'Herói': hero,
                    'Resultado': 'Vitória' if result == 'Won Match' else 'Derrota',
                    'Modo de Jogo': game_mode, 'Duração': duration,
                    'Horário de Início': start_time,
                })
            except (IndexError, NoSuchElementException):
                continue

        print(f"Coletadas {len(match_rows)} partidas da página {page} da Conta {account_number}.")
        page += 1
        time.sleep(1.5)

    return player_matches


if __name__ == '__main__':
    all_data = []
    driver = setup_driver()

    try:
        # --- MUDANÇA: Usamos enumerate para obter o número da conta (1, 2, ...) ---
        for account_number, pid in enumerate(PLAYER_IDS, start=1):
            # --- MUDANÇA: Passamos o número da conta para a função ---
            data = scrape_player_matches(driver, pid, account_number)
            all_data.extend(data)
    finally:
        print("\nScraping finalizado. Fechando o navegador em segundo plano...")
        driver.quit()

    if all_data:
        df = pd.DataFrame(all_data)
        output_filename = 'historico_partidas_dota2.xlsx'
        df.to_excel(output_filename, index=False, engine='openpyxl')
        print(f"\n✅ Sucesso! Os dados de {len(all_data)} partidas foram salvos em '{output_filename}'")
    else:
        print("\nNenhum dado foi coletado.")