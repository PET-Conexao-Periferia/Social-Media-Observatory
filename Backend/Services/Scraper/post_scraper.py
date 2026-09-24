import time
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

from Backend.Services.Scraper.date_utils import _obter_data_post
from Backend.Services.Scraper.metrics_scraper import obter_metricas_post
from Backend.Services.Scraper.comment_scraper import (
    expandir_comentarios,
    obter_elementos_comentarios,
    coletar_comentarios
)


# Processa um único post e retorna os dados coletados.
def raspar_post(
    driver,
    post_url,
    perfil_alvo,
    seguidores,
    rolagem_comentarios=1,
    start_date=None,
    end_date=None
):
    driver.get(post_url)
    time.sleep(5)

    # Obtém a data do post para aplicar o filtro de período.
    post_dt = None
    try:
        post_dt = _obter_data_post(driver)
    except Exception:
        post_dt = None

    if (start_date or end_date):
        if not post_dt:
            print(
                f"Data do post não encontrada para {post_url}; "
                "pulando devido ao filtro de período"
            )
            return None

        post_date = post_dt.date()

        if start_date and post_date < start_date:
            print(
                f"Post {post_url} publicado em {post_date} "
                "é anterior ao início do período; pulando"
            )
            return None

        if end_date and post_date > end_date:
            print(
                f"Post {post_url} publicado em {post_date} "
                "é posterior ao fim do período; pulando"
            )
            return None

    print(f"\nProcessando post: {post_url}")
    print(f"Data de publicação: {post_dt}")

    # Obtém as métricas do post.
    likes, comments_count, reposts = obter_metricas_post(driver)

    print(f"Curtidas: {likes}")
    print(f"Comentários: {comments_count}")
    print(f"Reposts: {reposts}")

    # Localiza o container principal do post.
    try:
        article = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.TAG_NAME, 'article'))
        )
    except Exception:
        article = None

    # Captura a legenda através da descrição Open Graph do post.
    legenda = None

    try:
        meta = driver.find_element(
            By.CSS_SELECTOR,
            "meta[property='og:description']"
        )
        if meta:
            legenda = meta.get_attribute('content')
    except Exception:
        pass

    # Expande os comentários antes de tentar coletá-los.
    expandir_comentarios(driver)

    for _ in range(rolagem_comentarios):
        driver.execute_script(
            "window.scrollTo(0, document.body.scrollHeight);"
        )
        time.sleep(4)

    # Localiza os elementos que representam os comentários.
    comment_items = obter_elementos_comentarios(driver, article)

    # Extrai e filtra os comentários encontrados.
    lista_comentarios = coletar_comentarios(
        comment_items,
        legenda
    )

    post_data = {
        'post_url': post_url,
        'legenda_post': legenda,
        'comentarios': lista_comentarios,
        'likes': likes,
        'comments_count': comments_count,
        'reposts': reposts,
        'published_at': post_dt.isoformat() if post_dt else None,
        'source_profile': perfil_alvo,
        'followers': seguidores,
    }

    return post_data