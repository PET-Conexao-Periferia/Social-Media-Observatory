from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time
import pandas as pd

# Variáveis de configuração
USUARIO = "userteste747"
SENHA = "kelle123"
PERFIL_ALVO = "igarassuordinarioo"  # exemplo de perfil

# Configuração do WebDriver para o Chrome
def create_driver(headless=False):
    options = Options()
    if headless:
        options.add_argument("--headless")
    options.add_argument("--start-maximized")
    options.add_argument("--disable-notifications")
    # Tenta usar webdriver-manager para baixar o chromedriver automaticamente
    try:
        from webdriver_manager.chrome import ChromeDriverManager
        service = Service(ChromeDriverManager().install())
        driver = webdriver.Chrome(service=service, options=options)
    except Exception:
        # Caso webdriver-manager não esteja disponível, tenta usar chromedriver do PATH
        driver = webdriver.Chrome(options=options)
    return driver

# Função de login
def login_instagram(driver, usuario, senha):
    login_url = "https://www.instagram.com/accounts/login/"
    driver.get(login_url)

    # Espera os campos de login aparecerem
    try:
        wait = WebDriverWait(driver, 15)
        username_input = wait.until(EC.presence_of_element_located((By.NAME, "username")))
        password_input = driver.find_element(By.NAME, "password")

        username_input.clear()
        username_input.send_keys(usuario)
        password_input.clear()
        password_input.send_keys(senha)

        # Clicar no botão de login
        login_button = driver.find_element(By.XPATH, "//button[@type='submit']")
        login_button.click()

        # Tempo para completar o login e permitir interação manual com pop-ups (ex: "Salvar informações de login")
        time.sleep(10)
    except Exception as e:
        print(f"Erro durante o login: {e}")

# Função para raspar dados do perfil
def raspar_perfil(driver, perfil_alvo):
    perfil_url = f"https://www.instagram.com/{perfil_alvo}/"
    driver.get(perfil_url)

    # Espera a página carregar
    time.sleep(5)

    # Rolar a página para baixo 3 vezes para carregar mais posts
    for _ in range(3):
        driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
        time.sleep(3)

    # Encontrar todos os links de posts (â€<a>â€ que levam para '/p/')
    anchors = driver.find_elements(By.TAG_NAME, "a")
    post_links = []
    seen = set()

    for a in anchors:
        href = a.get_attribute('href')
        if href and '/p/' in href:
            if href in seen:
                continue
            seen.add(href)
            caption = None
            try:
                img = a.find_element(By.TAG_NAME, 'img')
                caption = img.get_attribute('alt')
            except Exception:
                # Se não houver imagem direta dentro do link, ignoramos a legenda
                caption = None

            post_links.append({'url': href, 'caption': caption})

    return post_links

if __name__ == "__main__":
    driver = create_driver(headless=False)

    try:
        # 1) Fazer login
        login_instagram(driver, USUARIO, SENHA)

        # 2) Raspar dados do perfil alvo
        dados = raspar_perfil(driver, PERFIL_ALVO)

        # Converter em DataFrame e imprimir
        df = pd.DataFrame(dados)
        print(df)
    finally:
        # Fechar o driver ao final
        driver.quit()
