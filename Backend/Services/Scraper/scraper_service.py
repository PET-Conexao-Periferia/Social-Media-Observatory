from Backend.Services.Scraper.profile_scraper import obter_urls_posts
from Backend.Services.Scraper.post_scraper import raspar_post
from Backend.Services.Storage.storage_service import salvar_post_json


# Coordena a coleta dos posts de um perfil e salva os resultados encontrados.
def raspar_perfil(
    driver,
    perfil_alvo,
    quant_scrolagem=1,
    rolagem_comentarios=1,
    start_date=None,
    end_date=None
):
    # Carrega o perfil e obtém os URLs dos posts e os seguidores.
    seen, seguidores = obter_urls_posts(
        driver,
        perfil_alvo,
        quant_scrolagem
    )

    dados_completos = []

    # Processa cada post encontrado individualmente.
    for idx, post_url in enumerate(seen):
        try:
            post_data = raspar_post(
                driver,
                post_url,
                perfil_alvo,
                seguidores,
                rolagem_comentarios,
                start_date,
                end_date
            )

            # Posts fora do período não são salvos nem adicionados aos resultados.
            if post_data is None:
                continue

            salvar_post_json(post_data)
            dados_completos.append(post_data)

        except Exception as e:
            # Em caso de erro, mantém o registro mínimo do post.
            post_data = {
                'post_url': post_url,
                'legenda_post': None,
                'comentarios': [],
                'error': str(e),
                'published_at': None,
                'source_profile': perfil_alvo,
                'followers': seguidores,
            }

            salvar_post_json(post_data)
            dados_completos.append(post_data)

    return dados_completos, seguidores