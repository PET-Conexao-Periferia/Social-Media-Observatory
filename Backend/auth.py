import os
import json
import time
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.keys import Keys


def salvar_cookies(driver, caminho='cookies_instagram.json'):
    try:
        cookies = driver.get_cookies()
        with open(caminho, 'w', encoding='utf-8') as f:
            json.dump(cookies, f, ensure_ascii=False, indent=2)
    except Exception as e:
        print(f'Falha ao salvar cookies: {e}')
        
def carregar_cookies(driver, caminho='cookies_instagram.json'):
    if not os.path.exists(caminho):
        return False
    try:
        driver.get('https://www.instagram.com/')
        time.sleep(2)
        with open(caminho, 'r', encoding='utf-8') as f:
            cookies = json.load(f)
        for c in cookies:
            # remover chaves que podem causar erro no add_cookie
            c.pop('sameSite', None)
            try:
                driver.add_cookie(c)
            except Exception:
                continue

        driver.refresh()
        time.sleep(3)
        return True
    
    except Exception as e:
        print(f'Falha ao carregar cookies: {e}')
        return False
    
def is_logged_in(driver, usuario):
    try:
        # Não navegar aqui de novo para não interromper o fluxo atual
        # Tentar checar cookies primeiro
        try:
            cookies = driver.get_cookies()
            for c in cookies:
                if c.get('name') == 'sessionid' and c.get('value'):
                    return True
        except Exception:
            pass

        # Caso não haja cookie visível, tentar encontrar indicador de login na página carregada
        try:
            links = driver.find_elements(
                By.XPATH, f"//a[contains(@href, '/{usuario}/')]")
            if links:
                return True
        except Exception:
            pass

        try:
            avatar = driver.find_elements(
                By.CSS_SELECTOR, 'svg[aria-label="Profile"]')
            if avatar:
                return True
        except Exception:
            pass

        return False
    except Exception:
        return False

def wait_for_login_confirmation(driver, usuario, timeout=60, poll=2):
    """Aguarda até que a sessão esteja ativa por meio de cookies ou elementos da UI."""
    waited = 0
    while waited < timeout:
        try:
            if is_logged_in(driver, usuario):
                return True
        except Exception:
            pass
        time.sleep(poll)
        waited += poll
    return False

def login_instagram(driver, usuario, senha):
    login_url = "https://www.instagram.com/accounts/login/"
    driver.get(login_url)

    # Espera os campos de login aparecerem
    try:
        wait = WebDriverWait(driver, 15)
        username_input = wait.until(
            EC.presence_of_element_located((By.NAME, "email")))
        password_input = driver.find_element(By.NAME, "pass")

        username_input.clear()
        username_input.send_keys(usuario)
        password_input.clear()
        password_input.send_keys(senha)

        password_input.send_keys(Keys.ENTER)
      
        if wait_for_login_confirmation(driver, usuario, timeout=12, poll=2):
            print('Login confirmado sem 2FA.')
            return True

        print('Aguardando possível prompt de 2FA (até 5 minutos)...')
        code_input = None
        try:
            # Aguarda pela presença de um campo de verificação
            code_input = WebDriverWait(driver, 300).until(
                EC.presence_of_element_located((By.NAME, "verificationCode"))
            )
        except Exception:
            # Se não apareceu com esse name, tentar localizar por outros seletores em loop
            elapsed = 0
            poll = 2
            max_wait = 300
            while elapsed < max_wait and code_input is None:
                try:
                    code_input = driver.find_element(
                        By.XPATH, "//input[@type='text' and (@maxlength='6' or contains(@aria-label, 'Código') or contains(@placeholder, 'Código'))]")
                    break
                except Exception:
                    time.sleep(poll)
                    elapsed += poll

        if code_input:
            # Pausar para input do usuário (interativo). O usuário pode demorar para receber o código.
            codigo = input(
                "Insira o código 2FA recebido (SMS/Authenticator) e pressione Enter quando pronto: ").strip()
            try:
                code_input.clear()
                code_input.send_keys(codigo)
            except Exception:
                pass

            # tentar clicar no botão de confirmação
            try:
                btn = driver.find_element(
                    By.XPATH, "//button[contains(., 'Confirm') or contains(., 'Enviar') or contains(., 'Next') or contains(., 'Confirmar') or contains(., 'Submit')]")
                try:
                    driver.execute_script("arguments[0].click();", btn)
                except Exception:
                    btn.click()
            except Exception:
                try:
                    code_input.send_keys(Keys.ENTER)
                except Exception:
                    pass

            if wait_for_login_confirmation(driver, usuario, timeout=60, poll=2):
                print('Login confirmado após 2FA.')
                return True
            else:
                print(
                    'Aviso: não foi possível confirmar o login imediatamente após 2FA.')
                return False

        else:
            # Se não houver campo de 2FA detectado, aguardar alguns segundos para pop-ups manuais
            time.sleep(5)
            if wait_for_login_confirmation(driver, usuario, timeout=10, poll=2):
                print('Login confirmado (fallback).')
                return True
            return False
    except Exception as e:
        print(f"Erro durante o login: {e}")