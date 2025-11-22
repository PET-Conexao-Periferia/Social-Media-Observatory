# requisitos:
# pip install selenium pandas webdriver-manager python-dotenv

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.keys import Keys
import time
import json
import re
import pandas as pd
import os
from dotenv import load_dotenv
import logging

# CARREGAR VARIÁVEIS DO .ENV
load_dotenv()
USUARIO = os.getenv("USUARIO")
SENHA = os.getenv("SENHA")
PERFIS = os.getenv("PERFIS").split(",") if os.getenv("PERFIS") else []


# Opcional: carregar perfis de um arquivo 'perfis.txt' (uma linha por perfil)
# try:
#     with open('perfis.txt', 'r', encoding='utf-8') as pf:
#         file_perfis = [line.strip() for line in pf if line.strip() and not line.strip().startswith('#')]
#         if file_perfis:
#             PERFIS = file_perfis
#             print(f'Perfis carregados de perfis.txt: {PERFIS}')
# except FileNotFoundError:
#     pass
# except Exception as e:
#     print(f'Erro ao ler perfis de perfis.txt: {e}')

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


def salvar_cookies(driver, caminho='cookies_instagram.json'):
    try:
        cookies = driver.get_cookies()
        with open(caminho, 'w', encoding='utf-8') as f:
            json.dump(cookies, f, ensure_ascii=False, indent=2)
        print(f'Cookies salvos em {caminho}')
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
                # continuar se cookie falhar
                continue
        driver.refresh()
        time.sleep(3)
        print(f'Cookies carregados de {caminho}')
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
            links = driver.find_elements(By.XPATH, f"//a[contains(@href, '/{usuario}/')]")
            if links:
                return True
        except Exception:
            pass

        try:
            avatar = driver.find_elements(By.CSS_SELECTOR, 'svg[aria-label="Profile"]')
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
        try:
            driver.execute_script("arguments[0].click();", login_button)
        except Exception:
            login_button.click()

        # Primeiro verificar se o login foi confirmado rapidamente (sem 2FA)
        if wait_for_login_confirmation(driver, usuario, timeout=12, poll=2):
            print('Login confirmado sem 2FA.')
            return True

        # Caso não confirmado, aguardar e tratar 2FA interativo
        print('Aguardando possível prompt de 2FA (até 5 minutos)...')
        code_input = None
        try:
            # Aguarda até 5 minutos pela presença de um campo de verificação
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
                    code_input = driver.find_element(By.XPATH, "//input[@type='text' and (@maxlength='6' or contains(@aria-label, 'Código') or contains(@placeholder, 'Código'))]")
                    break
                except Exception:
                    time.sleep(poll)
                    elapsed += poll

        if code_input:
            # Pausar para input do usuário (interativo). O usuário pode demorar para receber o código.
            codigo = input("Insira o código 2FA recebido (SMS/Authenticator) e pressione Enter quando pronto: ").strip()
            try:
                code_input.clear()
                code_input.send_keys(codigo)
            except Exception:
                pass

            # tentar clicar no botão de confirmação (vários textos possíveis)
            try:
                btn = driver.find_element(By.XPATH, "//button[contains(., 'Confirm') or contains(., 'Enviar') or contains(., 'Next') or contains(., 'Confirmar') or contains(., 'Submit')]")
                try:
                    driver.execute_script("arguments[0].click();", btn)
                except Exception:
                    btn.click()
            except Exception:
                try:
                    code_input.send_keys(Keys.ENTER)
                except Exception:
                    pass

            # Aguardar confirmação de login (checar cookies/elementos)
            if wait_for_login_confirmation(driver, usuario, timeout=60, poll=2):
                print('Login confirmado após 2FA.')
                return True
            else:
                print('Aviso: não foi possível confirmar o login imediatamente após 2FA.')
                return False

        else:
            # Se não houver campo de 2FA detectado, aguardar alguns segundos para pop-ups manuais
            time.sleep(5)
            # tentar uma última vez confirmar login
            if wait_for_login_confirmation(driver, usuario, timeout=10, poll=2):
                print('Login confirmado (fallback).')
                return True
            return False
    except Exception as e:
        print(f"Erro durante o login: {e}")

# Função para raspar dados do perfil
def raspar_perfil(driver, perfil_alvo):
    perfil_url = f"https://www.instagram.com/{perfil_alvo}/"
    driver.get(perfil_url)
    print(f"Acessando perfil: {perfil_url}")

    # Espera a página carregar
    time.sleep(10)  # Aumentado para 10 segundos

    # Rolar a página para baixo 100 vezes para carregar mais posts
    for i in range(5):  # Aumentado para 100 vezes
        driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
        time.sleep(2)  # Reduzido para 2 segundos para acelerar
        print(f"Rolagem {i+1}/100 completada")

    # Encontrar todos os links de posts que levam para '/p/' e coletar URLs únicas
    try:
        wait = WebDriverWait(driver, 10)
        anchors = wait.until(EC.presence_of_all_elements_located((By.TAG_NAME, "a")))
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

    # Agora iterar sobre cada post para extrair legenda e comentários
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
                    print('Salvo debug_post.html para inspeção local')
                except Exception as e:
                    print(f'Falha ao salvar debug_post.html: {e}')

            # Tenta localizar o container do post
            try:
                article = WebDriverWait(driver, 10).until(
                    EC.presence_of_element_located((By.TAG_NAME, 'article'))
                )
            except Exception:
                article = None

            # Capturar a legenda principal do post
            legenda = None

            # 1) Fallback: tentar meta tag og:description (contém legenda + info)
            try:
                meta = driver.find_element(By.CSS_SELECTOR, "meta[property='og:description']")
                if meta:
                    legenda = meta.get_attribute('content')
                    if legenda:
                        print('Legenda obtida via meta[og:description]')
            except Exception:
                pass

            # 2) Se não encontrou via meta, usar heurística dentro do article
            if not legenda and article is not None:
                try:
                    spans = article.find_elements(By.XPATH, ".//span[@dir='auto']")
                    texts = [s.text.strip() for s in spans if s.text and s.text.strip()]
                    if texts:
                        # legenda costuma ser o texto mais longo
                        legenda = max(texts, key=len)
                        print(f'Legenda obtida via spans (len={len(legenda)})')
                except Exception:
                    legenda = None

            # Preparar lista de comentários
            lista_comentarios = []

            # Tentar expandir comentários clicando em botões que contenham palavras-chave
            try:
                # Palavras/expressões alvo (não usar palavras curtas como 'more')
                keywords = [
                    'ver mais', 'mais comentários', 'ver comentários', 'ver tradução',
                    'view all comments', 'load more comments', 'view replies', 'load more',
                    'view more', 'see more', 'carregar mais'
                ]
                # Construir regex para casar palavras/frases inteiras (case-insensitive)
                pattern = re.compile(r"\\b(" + "|".join(re.escape(k) for k in keywords) + r")\\b", re.I)

                # Tentar apenas em botões visíveis/ativos — evita clicar em perfis ou divs
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

                            # Usar regex para evitar correspondências parciais (ex: 'moreira')
                            if pattern.search(txt_l):
                                print(f"Tentando clicar em botão: {txt_l}")
                                try:
                                    driver.execute_script("arguments[0].click();", elem)
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

            # Rolar a página 2 vezes para tentar carregar mais comentários
            for _ in range(2):
                driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
                time.sleep(2)

            # Encontrar elementos que representem comentários (tentando múltiplos seletores)
            comment_items = []
            if article is not None:
                # Tentativa 1: ul/li tradicional
                comment_items = article.find_elements(By.XPATH, ".//ul//li")

                # Tentativa 2: divs que contenham spans com dir='auto'
                if not comment_items:
                    comment_items = article.find_elements(By.XPATH, ".//div[.//span[@dir='auto']]")

                # Tentativa 3: qualquer div que tenha uma estrutura típica de comentário
                if not comment_items:
                    comment_items = article.find_elements(By.XPATH, ".//div[.//a and .//span[@dir='auto']]")

            # Fallback global: caso não tenhamos encontrado nada no article (ou article não existe),
            # procurar spans com dir='auto' em toda a página e inferir comentários por proximidade
            if not comment_items:
                try:
                    spans = driver.find_elements(By.XPATH, "//span[@dir='auto']")
                    print(f'Fallback: encontrados {len(spans)} spans com dir="auto" na página')
                    candidates = []
                    seen_ancestors = set()
                    for s in spans:
                        try:
                            # procurar um ancestor div que contenha um link (usuário)
                            ancestor = s.find_element(By.XPATH, "./ancestor::div[.//a][1]")
                            # usar id(obj) ou text snapshot para deduplicar
                            key = (ancestor.get_attribute('innerText') or '')[:200]
                            if key in seen_ancestors:
                                continue
                            seen_ancestors.add(key)
                            candidates.append(ancestor)
                        except Exception:
                            continue
                    comment_items = candidates
                    print(f'Fallback: candidatos a comentário obtidos: {len(comment_items)}')
                except Exception as e:
                    print(f'Erro no fallback de spans: {e}')

            print(f'Encontrados {len(comment_items)} itens possíveis de comentário no artigo')

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
                        span_comments = item.find_elements(By.XPATH, ".//span[@dir='auto' and not(ancestor::a)]")
                        parts = [s.text.strip() for s in span_comments if s.text and s.text.strip()]
                        if parts:
                            comment_text = ' '.join(parts)
                            # função de limpeza local
                            def clean_text(txt, user, legenda_text):
                                if not txt:
                                    return txt
                                t = txt
                                # remover ocorrências repetidas do username no início/fim
                                if user:
                                    try:
                                        uname = user.strip()
                                        # remover quando aparece seguido de espaços/novas linhas
                                        t = re.sub(r"(?i)^" + re.escape(uname) + r"[\s:-]*", "", t)
                                        t = re.sub(r"(?i)[\s:-]*" + re.escape(uname) + r"$", "", t)
                                    except Exception:
                                        pass
                                # remover tokens comuns de UI
                                t = re.sub(r"(?i)\b(responder|respostas?|ver todas( as)?( as)?|editar|editado|reply)\b", "", t)
                                # remover marcações de tempo como '3 sem', '1 h', '2d', '3w', 'ago'
                                t = re.sub(r"\b\d+\s*(sem|h|m|d|w|mes(es)?|ano(s)?|s|min)\b", "", t)
                                t = re.sub(r"\b(\d+)\s*curtid[ao]s?\b", "", t, flags=re.I)
                                # remover palavras soltas como 'Curtir', 'Responder', 'Curtir\n'
                                t = re.sub(r"(?i)\b(Curtir|Curtir|Curtir\n|Curtir )\b", "", t)
                                # remover pontos de separação e bullets soltos
                                t = t.replace('•', ' ')
                                # remover múltiplas quebras de linha e espaços extras
                                t = re.sub(r"\n{2,}", "\n", t)
                                t = re.sub(r"[ ]{2,}", " ", t)
                                return t.strip()

                            comment_text = clean_text(comment_text, username, legenda)
                    except Exception:
                        comment_text = None

                    # Filtrar caso o texto contenha a legenda completa (às vezes a legenda aparece junto)
                    if comment_text and legenda and legenda.strip() and legenda.strip() in comment_text:
                        # pular este item
                        continue

                    # Evitar salvar apenas o nome do usuário como comentário
                    if comment_text:
                        # se o comment_text reduzido for igual ao username, pular
                        if username and comment_text.strip() == username.strip():
                            # pular
                            continue

                        lista_comentarios.append({'username': username or '', 'comment_text': comment_text})
                        comentarios_processados += 1  # Incrementar contador
                        print(f"DEBUG: Comentário adicionado - {username}: {comment_text[:80]}...")
                except Exception:
                    # Ignora itens que não correspondam ao padrão esperado
                    continue

            print(f'Coletados {len(lista_comentarios)} comentários para {post_url}')

            dados_completos.append({
                'post_url': post_url,
                'legenda_post': legenda,
                'comentarios': lista_comentarios
            })

        except Exception as e:
            # Em caso de erro com um post, registra entrada com informação mínima
            dados_completos.append({'post_url': post_url, 'legenda_post': None, 'comentarios': [], 'error': str(e)})

    return dados_completos

# Função para salvar dados em arquivo JSON
def salvar_json(dados, nome_arquivo='dados_instagram.json'):
    """
    Salva cada post em um arquivo JSON separado, organizando por pasta de perfil.
    Também separa metadados (likes, comments_count) da legenda e adiciona likes por comentário quando possível.
    """
    try:
        base_dir = 'dados_instagram_por_perfil'
        os.makedirs(base_dir, exist_ok=True)

        total_comentarios = sum(len(post.get('comentarios', [])) for post in dados)
        print(f'\nDEBUG: Total de comentários a processar: {total_comentarios}')

        index = []

        for post in dados:
            perfil = post.get('source_profile') or 'unknown_profile'
            perfil_dir = os.path.join(base_dir, perfil)
            os.makedirs(perfil_dir, exist_ok=True)

            # Extrair slug do post para nome do arquivo
            post_url = post.get('post_url') or ''
            slug = None
            try:
                m = re.search(r"/p/([^/]+)/", post_url)
                if m:
                    slug = m.group(1)
                else:
                    # fallback: usar parte final da URL
                    slug = post_url.rstrip('/').split('/')[-1]
            except Exception:
                slug = str(int(time.time() * 1000))

            # Separar metadados da legenda
            legenda = post.get('legenda_post') or ''
            likes = None
            comments_count = None
            if legenda:
                # procurar padrões como '699 likes, 8 comments' (insensível a maiúsculas)
                m = re.search(r"([\d\.,]+)\s*likes?[,;:\s]+([\d\.,]+)\s*comments?", legenda, re.I)
                if m:
                    try:
                        likes = int(re.sub(r"[^0-9]", "", m.group(1)))
                    except Exception:
                        likes = None
                    try:
                        comments_count = int(re.sub(r"[^0-9]", "", m.group(2)))
                    except Exception:
                        comments_count = None
                    # remover essa parte da legenda
                    legenda = re.sub(re.escape(m.group(0)), '', legenda).strip(' -:\n')
                else:
                    # tentar achar apenas likes ou apenas comments
                    m2 = re.search(r"([\d\.,]+)\s*likes?", legenda, re.I)
                    if m2:
                        try:
                            likes = int(re.sub(r"[^0-9]", "", m2.group(1)))
                        except Exception:
                            likes = None
                        legenda = re.sub(re.escape(m2.group(0)), '', legenda).strip(' -:\n')
                    m3 = re.search(r"([\d\.,]+)\s*comments?", legenda, re.I)
                    if m3:
                        try:
                            comments_count = int(re.sub(r"[^0-9]", "", m3.group(1)))
                        except Exception:
                            comments_count = None
                        legenda = re.sub(re.escape(m3.group(0)), '', legenda).strip(' -:\n')

            # Processar comentários: tentar extrair curtidas por comentário
            comentarios = post.get('comentarios', []) or []
            comentarios_proc = []
            for item in comentarios:
                c_user = item.get('username') or ''
                c_text = item.get('comment_text') or ''
                c_likes = item.get('likes') if 'likes' in item else None

                # Se não houver likes já extraído, tentar inferir de campos possivelmente presentes
                if c_likes is None:
                    # procurar padrão numérico isolado no texto residual (por exemplo '2' em elemento separado)
                    # já que aqui trabalhamos com dados extraídos previamente, tentaremos inferir de 'comment_text'
                    mlike = re.search(r"\b([\d\.,]+)\b", c_text)
                    if mlike:
                        # somente aceitar como likes se parecer plausível (pequeno número)
                        try:
                            v = int(re.sub(r"[^0-9]", "", mlike.group(1)))
                            if v >= 1 and v <= 100000:
                                c_likes = v
                                # remover do texto se era um token separado
                                c_text = re.sub(re.escape(mlike.group(0)), '', c_text).strip()
                        except Exception:
                            c_likes = None

                comentarios_proc.append({'username': c_user, 'comment_text': c_text, 'likes': c_likes or 0})

            # Montar dicionário final para o post
            post_obj = {
                'post_url': post_url,
                'slug': slug,
                'legenda_post': legenda,
                'likes': likes or 0,
                'comments_count': comments_count if comments_count is not None else len(comentarios_proc),
                'comentarios': comentarios_proc,
                'source_profile': perfil
            }

            # Salvar em arquivo por post
            filename = os.path.join(perfil_dir, f"{slug}.json")
            try:
                with open(filename, 'w', encoding='utf-8') as f:
                    json.dump(post_obj, f, ensure_ascii=False, indent=2)
                print(f'Salvo post em {filename}')
            except Exception as e:
                print(f'Erro ao salvar post {slug}: {e}')

            index.append({'perfil': perfil, 'post_url': post_url, 'file': filename})

        # Salvar índice geral
        try:
            idx_file = os.path.join(base_dir, 'index.json')
            with open(idx_file, 'w', encoding='utf-8') as f:
                json.dump(index, f, ensure_ascii=False, indent=2)
            print(f'Índice salvo em {idx_file}')
        except Exception as e:
            print(f'Erro ao salvar índice: {e}')

    except Exception as e:
        print(f'Erro ao salvar arquivos JSON por post: {e}')

if __name__ == "__main__":
    driver = create_driver(headless=False)

    try:
        # 1) Tentar carregar sessão salva (cookies) para evitar re-login e 2FA
        loaded = carregar_cookies(driver)
        if loaded and is_logged_in(driver, USUARIO):
            print('Sessão restaurada via cookies. Pulando login.')
        else:
            print('Necessário efetuar login interativo (pode requerer 2FA).')
            ok = login_instagram(driver, USUARIO, SENHA)
            if ok:
                try:
                    salvar_cookies(driver)
                except Exception as e:
                    print(f'Não foi possível salvar cookies: {e}')
            else:
                print('Atenção: login não confirmado. Você pode continuar manualmente no navegador aberto.')

        # 2) Raspar dados de múltiplos perfis
        all_data = []
        for perfil in PERFIS:
            print(f'\nIniciando raspagem do perfil: {perfil}')
            dados = raspar_perfil(driver, perfil)
            # Anotar origem do perfil em cada post
            for post in dados:
                post['source_profile'] = perfil
            all_data.extend(dados)

        # Salvar dados em JSON
        salvar_json(all_data)

        # Converter em DataFrame e imprimir
        df = pd.DataFrame(all_data)
        # Configurar pandas para mostrar todas as linhas
        pd.set_option('display.max_rows', None)
        pd.set_option('display.max_columns', None)
        pd.set_option('display.width', None)
        print(df)
        # Mostrar resumo
        print(f"\nTotal de posts processados: {len(df)}")
    finally:
        driver.quit()
