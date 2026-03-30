from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options


def create_driver(headless=True): #headless=False para rodar com a janela do navegador
    if headless:
        options.add_argument("--headless=new")
        options.add_argument("--window-size=1920,1080")
    options.add_argument("--disable-notifications")
    try:
        from webdriver_manager.chrome import ChromeDriverManager
        service = Service(ChromeDriverManager().install())
        driver = webdriver.Chrome(service=service, options=options)
    except Exception:
        driver = webdriver.Chrome(options=options)
    return driver