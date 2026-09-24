import re
import time
from selenium.webdriver.common.by import By


# Expande os comentários disponíveis através dos botões de carregamento.
def expandir_comentarios(driver):
    try:
        keywords = [
            'ver mais', 'mais comentários', 'ver comentários', 'ver tradução',
            'view all comments', 'load more comments', 'view replies', 'load more',
            'view more', 'see more', 'carregar mais', 'ver todos os comentários',
        ]

        # Cria um padrão para identificar os botões relacionados aos comentários.
        pattern = re.compile(
            r"\\b(" + "|".join(re.escape(k) for k in keywords) + r")\\b", re.I)

        for _ in range(5):
            buttons = driver.find_elements(By.TAG_NAME, 'button')
            clicked = False

            for elem in buttons:
                try:
                    if not elem.is_displayed() or not elem.is_enabled():
                        continue

                    txt = elem.text.strip()
                    if not txt:
                        continue

                    txt_l = txt.lower()

                    # Evita clicar em botões que contenham links para perfis.
                    try:
                        if elem.find_elements(By.TAG_NAME, 'a'):
                            continue
                    except Exception:
                        pass

                    if pattern.search(txt_l):
                        print(f"Tentando clicar em botão: {txt_l}")

                        try:
                            driver.execute_script(
                                "arguments[0].click();", elem)
                        except Exception:
                            try:
                                elem.click()
                            except Exception:
                                pass

                        clicked = True
                        time.sleep(4)

                except Exception:
                    continue

            if not clicked:
                break

            print("Expandindo mais comentários...")

    except Exception as e:
        print(f"Erro ao expandir comentários: {e}")


# Localiza os elementos que podem representar comentários no post.
def obter_elementos_comentarios(driver, article):
    comment_items = []

    if article is not None:
        # Tenta primeiro a estrutura tradicional de comentários em ul/li.
        comment_items = article.find_elements(By.XPATH, ".//ul//li")

        # Tenta encontrar comentários através de spans com dir='auto'.
        if not comment_items:
            comment_items = article.find_elements(
                By.XPATH, ".//div[.//span[@dir='auto']]")

        # Tenta uma estrutura mais ampla contendo usuário e texto.
        if not comment_items:
            comment_items = article.find_elements(
                By.XPATH, ".//div[.//a and .//span[@dir='auto']]")

    # Usa toda a página como fallback quando o article não contém comentários.
    if not comment_items:
        try:
            spans = driver.find_elements(
                By.XPATH, "//span[@dir='auto']")

            candidates = []
            seen_ancestors = set()

            for s in spans:
                try:
                    # Procura o primeiro ancestral que contenha um link de usuário.
                    ancestor = s.find_element(
                        By.XPATH, "./ancestor::div[.//a][1]")

                    key = (ancestor.get_attribute(
                        'innerText') or '')[:200]

                    if key in seen_ancestors:
                        continue

                    seen_ancestors.add(key)
                    candidates.append(ancestor)

                except Exception:
                    continue

            comment_items = candidates

        except Exception as e:
            print(f'Erro no fallback de spans: {e}')

    return comment_items


# Extrai os usuários e textos dos comentários encontrados no post.
def coletar_comentarios(comment_items, legenda):
    lista_comentarios = []

    for item in comment_items:
        try:
            username = None
            comment_text = None

            try:
                a_user = item.find_element(By.XPATH, ".//a")
                username = a_user.text
            except Exception:
                username = None

            try:
                # Junta os spans que representam o texto do comentário.
                span_comments = item.find_elements(
                    By.XPATH, ".//span[@dir='auto' and not(ancestor::a)]")

                parts = [
                    s.text.strip()
                    for s in span_comments
                    if s.text and s.text.strip()
                ]

                if parts:
                    comment_text = ' '.join(parts)

            except Exception:
                comment_text = None

            # Ignora elementos que contenham a legenda completa do post.
            if comment_text and legenda and legenda.strip() and legenda.strip() in comment_text:
                continue

            # Evita salvar somente o nome do usuário como comentário.
            if comment_text:
                if username and comment_text.strip() == username.strip():
                    continue

                lista_comentarios.append({
                    'username': username or '',
                    'comment_text': comment_text
                })

        except Exception:
            continue

    print(f'Comentários Coletados {len(lista_comentarios)} ')

    return lista_comentarios