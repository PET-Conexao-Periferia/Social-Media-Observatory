import time
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC


# Obtém a quantidade de seguidores exibida no perfil.
def obter_seguidores(driver):
    try:
        elem = driver.find_element(
            By.XPATH,
            "//header//span[contains(., 'followers') or contains(., 'seguidores')]"
        )
        texto = elem.text

        if not texto:
            return 0
        
        texto = texto.lower().replace('followers', '').replace('seguidores', '').strip()

        # Trata "mil" (pt-BR).
        if 'mil' in texto:
            numero = texto.replace('mil', '').replace(',', '.').strip()
            return int(float(numero) * 1000)

        # Trata "mi" (milhões pt-BR).
        if 'mi' in texto:
            numero = texto.replace('mi', '').replace(',', '.').strip()
            return int(float(numero) * 1_000_000)

        # Trata "k".
        if texto.endswith('k'):
            numero = texto[:-1].replace(',', '.').strip()
            return int(float(numero) * 1000)

        # Trata "m" (milhões).
        if texto.endswith('m'):
            numero = texto[:-1].replace(',', '.').strip()
            return int(float(numero) * 1_000_000)
        
        # Trata números sem abreviação.
        texto = texto.replace('.', '').replace(',', '').strip()
        return int(texto)

    except Exception as e:
        print(f"Erro ao obter seguidores: {e}")
        return 0


# Abre o perfil, realiza as rolagens e retorna os URLs dos posts encontrados.
def obter_urls_posts(driver, perfil_alvo, quant_scrolagem=1):
    perfil_url = f"https://www.instagram.com/{perfil_alvo}/"
    driver.get(perfil_url)
    print(f"Acessando perfil: {perfil_url}")
    time.sleep(10)

    # Obtém a quantidade de seguidores antes de coletar os posts.
    seguidores = obter_seguidores(driver)
    print(f"Seguidores do perfil {perfil_alvo}: {seguidores}")

    # Rola a página para carregar mais posts.
    for i in range(quant_scrolagem):
        driver.execute_script(
            "window.scrollTo(0, document.body.scrollHeight);")
        time.sleep(5)
        print(f"Rolagem {i+1}/{quant_scrolagem} completada")

    # Localiza os links carregados na página do perfil.
    try:
        wait = WebDriverWait(driver, 10)
        anchors = wait.until(
            EC.presence_of_all_elements_located((By.TAG_NAME, "a")))
    except Exception as e:
        print(f"Erro ao procurar links: {e}")
        anchors = []

    seen = []
    seen_set = set()

    # Mantém apenas URLs de posts e evita processar o mesmo post duas vezes.
    for a in anchors:
        href = a.get_attribute('href')
        if href and any(x in href for x in ('/p/', '/reel/')):
            if href in seen_set:
                continue
            seen_set.add(href)
            seen.append(href)

    return seen, seguidores