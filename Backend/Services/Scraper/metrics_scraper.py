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

        likes_text = None
        comments_text = None
        reposts_text = None

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
            try:
                likes_elements = driver.find_elements(
                    By.XPATH,
                    "//button[contains(@aria-label, 'curtida') or "
                    "contains(@aria-label, 'curtidas') or "
                    "contains(@aria-label, 'like') or "
                    "contains(@aria-label, 'likes')]"
                )

                for element in likes_elements:
                    aria_label = element.get_attribute("aria-label") or ""
                    texto = element.text.strip()

                    if aria_label:
                        likes_text = aria_label
                        break

                    if texto:
                        likes_text = texto
                        break

            except Exception:
                likes_text = None

            try:
                comments_element = driver.find_element(
                    By.XPATH,
                    f"{base_xpath}/span[3]"
                )
                comments_text = comments_element.text

            except Exception:
                comments_text = "0"

            try:
                reposts_element = driver.find_element(
                    By.XPATH,
                    f"{base_xpath}/span[4]"
                )
                reposts_text = reposts_element.text

            except Exception:
                reposts_text = None

        if likes_text is None:
            raise Exception("Não foi possível obter a quantidade de curtidas")

        if reposts_text is None:
            raise Exception("Não foi possível obter a quantidade de reposts")

        likes = converter_metrica(likes_text)
        comments = converter_metrica(comments_text)
        reposts = converter_metrica(reposts_text)

        return likes, comments, reposts

    except Exception as e:
        return None, None, None