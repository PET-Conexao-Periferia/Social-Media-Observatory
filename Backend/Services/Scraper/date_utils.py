from datetime import datetime
from selenium.webdriver.common.by import By


# Converte diferentes formatos de data para um objeto datetime.
def _parse_datetime_str(s):
    if not s:
        return None

    s = s.strip()

    # Ajusta o formato Z para ser compatível com fromisoformat.
    if s.endswith('Z'):
        s = s[:-1] + '+00:00'

    try:
        return datetime.fromisoformat(s)
    except Exception:
        # Tenta formatos sem timezone quando o formato ISO falhar.
        for fmt in ("%Y-%m-%dT%H:%M:%S", "%Y-%m-%dT%H:%M:%S.%f", "%Y-%m-%d"):
            try:
                return datetime.strptime(s.split('+')[0], fmt)
            except Exception:
                continue

    return None


# Tenta obter a data de publicação do post através de diferentes elementos.
def _obter_data_post(driver):
    # Tenta obter a data através da meta article:published_time.
    try:
        meta = driver.find_element(
            By.CSS_SELECTOR, "meta[property='article:published_time']")
        if meta:
            dt = meta.get_attribute('content')
            parsed = _parse_datetime_str(dt)
            if parsed:
                return parsed
    except Exception:
        pass

    # Tenta obter a data através da meta og:updated_time.
    try:
        meta = driver.find_element(
            By.CSS_SELECTOR, "meta[property='og:updated_time']")
        if meta:
            dt = meta.get_attribute('content')
            parsed = _parse_datetime_str(dt)
            if parsed:
                return parsed
    except Exception:
        pass

    # Tenta obter a data através do elemento <time>.
    try:
        time_el = driver.find_element(By.TAG_NAME, 'time')
        if time_el:
            dt = time_el.get_attribute('datetime') or time_el.text
            parsed = _parse_datetime_str(dt)
            if parsed:
                return parsed
    except Exception:
        pass

    return None