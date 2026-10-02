import re
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC


# Converte métricas do Instagram para números inteiros.
def converter_metrica(texto):
    if not texto:
        return 0

    texto = str(texto).lower()
    texto = re.sub(r'\s+', ' ', texto).strip()
    texto = texto.replace(',', '.')

    # Trata valores no formato "mil".
    if 'mil' in texto:
        numero = texto.replace('mil', '').strip()
        return int(float(numero) * 1000)

    # Trata valores no formato "mi".
    if 'mi' in texto:
        numero = texto.replace('mi', '').strip()
        return int(float(numero) * 1_000_000)

    # Trata valores no formato "k".
    if texto.endswith('k'):
        numero = texto[:-1].strip()
        return int(float(numero) * 1000)

    # Trata valores no formato "m".
    if texto.endswith('m'):
        numero = texto[:-1].strip()
        return int(float(numero) * 1_000_000)

    return int(texto.replace('.', ''))


# Obtém curtidas, comentários e reposts do post aberto.
def obter_metricas_post(driver):
    try:
        base_xpath = (
            "//main/div/div[1]/div/div[2]/div/div[3]"
            "/section[1]/div[1]"
        )

        # Tenta primeiro o layout que exibe a quantidade de curtidas.
        try:
            likes_element = WebDriverWait(driver, 5).until(
                EC.presence_of_element_located((
                    By.XPATH,
                    f"{base_xpath}/span[2]"
                ))
            )

            likes_text = likes_element.text

            comments_text = driver.find_element(
                By.XPATH,
                f"{base_xpath}/span[4]"
            ).text

            reposts_text = driver.find_element(
                By.XPATH,
                f"{base_xpath}/span[5]"
            ).text

        except Exception:
            # Quando curtidas não aparecem, os XPaths das outras métricas mudam.
            likes_text = "0"

            comments_text = driver.find_element(
                By.XPATH,
                f"{base_xpath}/span[3]"
            ).text

            reposts_text = driver.find_element(
                By.XPATH,
                f"{base_xpath}/span[4]"
            ).text

        likes = converter_metrica(likes_text)
        comments = converter_metrica(comments_text)
        reposts = converter_metrica(reposts_text)

        return likes, comments, reposts

    except Exception as e:
        print(f"Erro ao obter métricas do post: {e}")
        return 0, 0, 0