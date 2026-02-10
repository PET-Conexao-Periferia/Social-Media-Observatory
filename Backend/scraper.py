import time
import re
from datetime import datetime, date
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
    
def _parse_datetime_str(s):
    if not s:
        return None
    s = s.strip()
    # ajustar Z para offset compatível com fromisoformat
    if s.endswith('Z'):
        s = s[:-1] + '+00:00'
    try:
        return datetime.fromisoformat(s)
    except Exception:
        # tentar formatos sem timezone
        for fmt in ("%Y-%m-%dT%H:%M:%S", "%Y-%m-%dT%H:%M:%S.%f", "%Y-%m-%d"):
            try:
                return datetime.strptime(s.split('+')[0], fmt)
            except Exception:
                continue
    return None

def obter_likes(contexto):
    """
    Tenta extrair o número de likes do DOM do post.
    Aceita 'article' ou 'driver' como contexto.
    """
    if contexto is None:
        return 0

    try:
        # Estratégia 1: Busca por tag <a> que leva para a lista de curtidas ('liked_by')
        # Ex: "Curtido por fulano e outras 15.300 pessoas"
        links_likes = contexto.find_elements(By.XPATH, ".//a[contains(@href, 'liked_by')]")
        for link in links_likes:
            txt = link.get_attribute('innerText').replace('.', '').replace(',', '')
            # Procura por "outras X pessoas" ou "others X people"
            # Regex captura o número após 'outras'/'others'
            m = re.search(r'(?:outras|others)\s*(\d+)', txt, re.I)
            if m:
                # Se achou "outras X", soma 1 (o "fulano" citado)
                return int(m.group(1)) + 1
            
            # Se for apenas "500 likes"
            m2 = re.search(r'(\d+)\s*(?:likes|curtidas)', txt, re.I)
            if m2:
                return int(m2.group(1))

        # Estratégia 2: Busca genérica por spans com classe de contagem ou texto solto
        # Procura qualquer span que diga "X likes" ou "X curtidas"
        spans = contexto.find_elements(By.XPATH, ".//span[contains(text(), 'likes') or contains(text(), 'curtidas')]")
        for s in spans:
            txt = s.text.lower().replace('.', '').replace(',', '')
            m = re.search(r'(\d+)', txt)
            if m:
                return int(m.group(1))

        # Estratégia 3: Tentar pegar do meta tag (funciona se contexto for driver e não article)
        # Infelizmente 'contexto' pode ser article, que não tem find_element(meta). 
        # Essa estratégia deixamos para o caller se quiser.

    except Exception as e:
        print(f"Erro ao extrair likes: {e}")
    
    return 0

def obter_comentarios_total(contexto):
    """
    Tenta extrair o contador total de comentários (ex: 'Ver todos os 1.500 comentários')
    """
    if contexto is None:
        return 0
        
    try:
        # Procura por links ou botões que tenham "comments" ou "comentários" no texto
        elementos = contexto.find_elements(By.XPATH, ".//a | .//button") + \
                    contexto.find_elements(By.XPATH, ".//span[contains(text(), 'coment')]")
                    
        for el in elementos:
            try:
                txt = el.text.replace('.', '').replace(',', '')
                # Padrão: "View all 150 comments" ou "Ver todos os 200 comentários"
                if 'ver' in txt.lower() or 'view' in txt.lower():
                     m = re.search(r'(\d+)', txt)
                     if m:
                         val = int(m.group(1))
                         if val > 0:
                             return val
            except: 
                pass
    except Exception as e:
        print(f"Erro ao extrair total comentários: {e}")
        
    return 0

def _obter_data_post(driver):
    # Tenta meta article:published_time
    try:
        meta = driver.find_element(By.CSS_SELECTOR, "meta[property='article:published_time']")
        if meta:
            dt = meta.get_attribute('content')
            parsed = _parse_datetime_str(dt)
            if parsed:
                return parsed
    except Exception:
        pass

    # Tenta meta og:updated_time
    try:
        meta = driver.find_element(By.CSS_SELECTOR, "meta[property='og:updated_time']")
        if meta:
            dt = meta.get_attribute('content')
            parsed = _parse_datetime_str(dt)
            if parsed:
                return parsed
    except Exception:
        pass

    # Tenta encontrar <time datetime="...">
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


def raspar_perfil(driver, perfil_alvo, quant_scrolagem=1, rolagem_comentarios=1, start_date=None, end_date=None, on_post_scraped=None):
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

            # tentar obter data de publicação do post e aplicar filtro de período
            post_dt = None
            try:
                post_dt = _obter_data_post(driver)
            except Exception:
                post_dt = None

            if (start_date or end_date):
                if not post_dt:
                    print(f"Data do post não encontrada para {post_url}; pulando devido ao filtro de período")
                    continue
                post_date = post_dt.date()
                if start_date and post_date < start_date:
                    print(f"Post {post_url} publicado em {post_date} é anterior ao início do período; pulando")
                    continue
                if end_date and post_date > end_date:
                    print(f"Post {post_url} publicado em {post_date} é posterior ao fim do período; pulando")
                    continue

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

            # Tenta pegar likes e contagem real de comentários
            # Usa 'article' se existir, senão usa 'driver' como fallback
            contexto_busca = article if article is not None else driver
            
            extracted_likes = obter_likes(contexto_busca)
            total_comments_visual = obter_comentarios_total(contexto_busca)
            
            # Se não achou contador visual, usa o len() dos coletados como fallback mínimo
            final_comments_count = max(total_comments_visual, len(lista_comentarios))

            post_data_obj = {
                'post_url': post_url,
                'slug': post_url.rstrip('/').split('/')[-1] if post_url else None, # Pre-calcula slug
                'legenda_post': legenda,
                'comentarios': lista_comentarios,
                'likes': extracted_likes,
                'comments_count': final_comments_count,
                'published_at': post_dt.isoformat() if post_dt else None,
                'source_profile': perfil_alvo, # Injeta metadata
                'followers': seguidores # Injeta metadata
            }

            dados_completos.append(post_data_obj)
            
            # Notifica callback em tempo real
            if on_post_scraped:
                try:
                    on_post_scraped(post_data_obj)
                    print(" > Salvo em tempo real.")
                except Exception as ex_cb:
                    print(f"Erro no callback de salvamento: {ex_cb}")

        except Exception as e:
            # caso de erro, registra informação mínima
            err_obj = {
                'post_url': post_url, 
                'legenda_post': None, 
                'comentarios': [], 
                'error': str(e), 
                'published_at': None,
                'source_profile': perfil_alvo,
                'followers': seguidores
            }
            dados_completos.append(err_obj)

    return dados_completos, seguidores