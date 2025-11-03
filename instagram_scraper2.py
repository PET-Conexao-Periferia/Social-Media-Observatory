from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time
import pandas as pd

# Variáveis de configuração
USUARIO = ""
SENHA = ""
PERFIL_ALVO = "igarassuordinarioo"  # exemplo de perfil

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
        login_button.click()

        # Tempo para completar o login e permitir interação manual com pop-ups (ex: "Salvar informações de login")
        time.sleep(10)
    except Exception as e:
        print(f"Erro durante o login: {e}")

# Função para raspar dados do perfil
def raspar_perfil(driver, perfil_alvo):
    perfil_url = f"https://www.instagram.com/{perfil_alvo}/"
    driver.get(perfil_url)
    print(f"Acessando perfil: {perfil_url}")

    # Espera a página carregar
    time.sleep(10)  # Aumentado para 10 segundos

    # Rolar a página para baixo 5 vezes para carregar mais posts
    for i in range(5):  # Aumentado para 5 vezes
        driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
        time.sleep(5)  # Aumentado para 5 segundos
        print(f"Rolagem {i+1}/5 completada")

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
                keywords = ['ver mais', 'mais comentários', 'coment', 'more', 'view all', 'load more', 'view replies']
                for _ in range(3):  # Aumentado para 5 tentativas
                    buttons = driver.find_elements(By.TAG_NAME, 'button')
                    divs = driver.find_elements(By.TAG_NAME, 'div')
                    elementos_clicaveis = buttons + divs
                    clicked = False
                    
                    for elem in elementos_clicaveis:
                        try:
                            txt = elem.text.strip().lower()
                            if any(k in txt for k in keywords):
                                print(f"Tentando clicar em botão: {txt}")
                                driver.execute_script("arguments[0].click();", elem)
                                clicked = True
                                time.sleep(2)  # Aumentado para 2 segundos
                        except Exception as e:
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

            print(f'Encontrados {len(comment_items)} itens possíveis de comentário no artigo')

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
                        span_comments = item.find_elements(By.XPATH, ".//span[@dir='auto']")
                        parts = [s.text.strip() for s in span_comments if s.text and s.text.strip()]
                        if parts:
                            comment_text = ' '.join(parts)
                    except Exception:
                        comment_text = None

                    # Filtrar caso o texto seja igual à legenda (algumas vezes a legenda aparece como primeiro li)
                    if comment_text and legenda and comment_text.strip() == legenda.strip():
                        # pular
                        continue

                    if comment_text:
                        lista_comentarios.append({'username': username, 'comment_text': comment_text})
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

if __name__ == "__main__":
    driver = create_driver(headless=False)

    try:
        # 1) Fazer login
        login_instagram(driver, USUARIO, SENHA)

        # 2) Raspar dados do perfil alvo
        dados = raspar_perfil(driver, PERFIL_ALVO)

        # Converter em DataFrame e imprimir
        df = pd.DataFrame(dados)
        # Configurar pandas para mostrar todas as linhas
        pd.set_option('display.max_rows', None)
        pd.set_option('display.max_columns', None)
        pd.set_option('display.width', None)
        print(df)
        # Mostrar resumo
        print(f"\nTotal de posts encontrados: {len(seen)}")
        print(f"Total de posts processados: {len(df)}")
    finally:
        # Fechar o driver ao final
        driver.quit()
