import time
import re
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC


def obter_seguidores(driver):
    try:
        elem = driver.find_element(
            By.XPATH,
            "//span[@title and contains(@title, '.')]"
        )
        texto = elem.get_attribute("title")

        if not texto:
            return 0
        
        texto = texto.replace('.', '').replace(',', '').strip()
        return int(texto)

    except Exception as e:
        print(f"Erro ao obter seguidores: {e}")
        return 0
    
def raspar_perfil(driver, perfil_alvo, quant_scrolagem=1, rolagem_comentarios=1):
    perfil_url = f"https://www.instagram.com/{perfil_alvo}/"
    driver.get(perfil_url)
    print(f"Acessando perfil: {perfil_url}")
    time.sleep(10)

    seguidores = obter_seguidores(driver)
    print(f"Seguidores do perfil {perfil_alvo}: {seguidores}")

    # Rolar a página para carregar mais posts
    for i in range(quant_scrolagem): 
        driver.execute_script(
            "window.scrollTo(0, document.body.scrollHeight);")
        time.sleep(2)  
        print(f"Rolagem {i+1}/{quant_scrolagem} completada")

    # Encontrar todos os links de posts que levam para '/p/' e coletar URLs únicas
    try:
        wait = WebDriverWait(driver, 10) #pesquisar
        anchors = wait.until(
            EC.presence_of_all_elements_located((By.TAG_NAME, "a")))
        print(f"Encontrados {len(anchors)} links totais")
    except Exception as e:
        print(f"Erro ao procurar links: {e}")
        anchors = []

    seen = []
    seen_set = set()

    for a in anchors:
        href = a.get_attribute('href')
        if href and '/p/' in href:
            if href in seen_set:
                continue
            seen_set.add(href)
            seen.append(href)

    # iterar sobre cada post para extrair legenda e comentários
    dados_completos = []

    for idx, post_url in enumerate(seen):
        try:
            driver.get(post_url)
            time.sleep(5)

            # Salva o HTML do primeiro post para inspeção local (diagnóstico)
            if idx == 0:
                try:
                    with open('debug_post.html', 'w', encoding='utf-8') as f:
                        f.write(driver.page_source)
                except Exception as e:
                    print(f'Falha ao salvar debug_post.html: {e}')

            # Localizar o container do post
            try:
                article = WebDriverWait(driver, 10).until(
                    EC.presence_of_element_located((By.TAG_NAME, 'article'))
                )
            except Exception:
                article = None

            legenda = None # Capturar a legenda

            # 1) Fallback: tentar meta tag og:description (contém legenda + info)
            try:
                meta = driver.find_element(
                    By.CSS_SELECTOR, "meta[property='og:description']")
                if meta:
                    legenda = meta.get_attribute('content')
                    if legenda:
                        print('Legenda obtida via meta[og:description]')
            except Exception:
                pass

            # 2) Se não encontrou via meta, usar heurística dentro do article
            if not legenda and article is not None:
                try:
                    spans = article.find_elements(
                        By.XPATH, ".//span[@dir='auto']")
                    texts = [s.text.strip()
                             for s in spans if s.text and s.text.strip()]
                    if texts:
                        # legenda costuma ser o texto mais longo
                        legenda = max(texts, key=len)
                        print(f'Legenda obtida via spans (len={len(legenda)})')
                except Exception:
                    legenda = None

            lista_comentarios = []  # Preparar lista de comentários

            # Expandir comentários (botões com palavras-chave)
            try:
                keywords = [
                    'ver mais', 'mais comentários', 'ver comentários', 'ver tradução',
                    'view all comments', 'load more comments', 'view replies', 'load more',
                    'view more', 'see more', 'carregar mais', 'ver todos os comentários',
                ]
                # Criar regex para casar palavras/frases inteiras (case-insensitive)
                pattern = re.compile(
                    r"\\b(" + "|".join(re.escape(k) for k in keywords) + r")\\b", re.I)

                # Clicar em btn visíveis/ativos — evita clicar em perfis ou divs
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

                            # Pular se o botão contém links internos (provavelmente perfil)
                            try:
                                if elem.find_elements(By.TAG_NAME, 'a'):
                                    continue
                            except Exception:
                                pass

                            # Usar regex para evitar correspondências parciais
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
                                time.sleep(2)
                        except Exception:
                            continue

                    if not clicked:
                        break
                    print("Expandindo mais comentários...")
            except Exception as e:
                print(f"Erro ao expandir comentários: {e}")

            for _ in range(rolagem_comentarios):
                driver.execute_script(
                    "window.scrollTo(0, document.body.scrollHeight);")
                time.sleep(2)

            # Encontrar elementos que representem comentários
            comment_items = []
            if article is not None:
                # Tentativa 1: ul/li tradicional
                comment_items = article.find_elements(By.XPATH, ".//ul//li")

                # Tentativa 2: divs que contenham spans com dir='auto'
                if not comment_items:
                    comment_items = article.find_elements(
                        By.XPATH, ".//div[.//span[@dir='auto']]")

                # Tentativa 3: qualquer div que tenha uma estrutura típica de comentário
                if not comment_items:
                    comment_items = article.find_elements(
                        By.XPATH, ".//div[.//a and .//span[@dir='auto']]")

            # Fallback global: caso não tenhamos encontrado nada no article (ou article não existe),
            # procurar spans com dir='auto' em toda a página e inferir comentários por proximidade
            if not comment_items:
                try:
                    spans = driver.find_elements(
                        By.XPATH, "//span[@dir='auto']")
                    print(
                        f'Fallback: encontrados {len(spans)} spans com dir="auto" na página')
                    candidates = []
                    seen_ancestors = set()
                    for s in spans:
                        try:
                            # procurar um ancestor div que contenha um link (usuário)
                            ancestor = s.find_element(
                                By.XPATH, "./ancestor::div[.//a][1]")
                            # usar id(obj) ou text snapshot para deduplicar
                            key = (ancestor.get_attribute(
                                'innerText') or '')[:200]
                            if key in seen_ancestors:
                                continue
                            seen_ancestors.add(key)
                            candidates.append(ancestor)
                        except Exception:
                            continue
                    comment_items = candidates
                    print(
                        f'Fallback: candidatos a comentário obtidos: {len(comment_items)}')
                except Exception as e:
                    print(f'Erro no fallback de spans: {e}')

            print(
                f'Encontrados {len(comment_items)} itens possíveis de comentário no artigo')

            # Coletar todos os comentários do post (sem limite)
            comentarios_processados = 0
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
                        # Pode haver múltiplos spans; juntar todos para formar o comentário
                        # pegar spans que não estão dentro de um <a> (assim evitamos repetir o username)
                        span_comments = item.find_elements(
                            By.XPATH, ".//span[@dir='auto' and not(ancestor::a)]")
                        parts = [s.text.strip()
                                 for s in span_comments if s.text and s.text.strip()]
                        if parts:
                            comment_text = ' '.join(parts)
                            # função de limpeza local
                    except Exception:
                        comment_text = None
                    # Filtrar caso o texto contenha a legenda completa (às vezes a legenda aparece junto)
                    if comment_text and legenda and legenda.strip() and legenda.strip() in comment_text:
                        continue

                    # Evitar salvar apenas o nome do usuário como comentário
                    if comment_text:
                        if username and comment_text.strip() == username.strip():
                            continue

                        lista_comentarios.append(
                            {'username': username or '', 'comment_text': comment_text})
                    
                        comentarios_processados += 1  
                        # print(f"DEBUG: Comentário adicionado - {username}: {comment_text[:80]}...")
                except Exception:
                    continue
            print(f'Coletados {len(lista_comentarios)} comentários para {post_url}')

            dados_completos.append({
                'post_url': post_url,
                'legenda_post': legenda,
                'comentarios': lista_comentarios,
                'likes': 0,
                'comments_count': len(lista_comentarios)
            })

        except Exception as e:
            # caso de erro, registra informação mínima
            dados_completos.append(
                {'post_url': post_url, 'legenda_post': None, 'comentarios': [], 'error': str(e)})

    return dados_completos, seguidores