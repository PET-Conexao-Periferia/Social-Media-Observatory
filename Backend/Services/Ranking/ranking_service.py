import re
import math
import pandas as pd
from Backend.Config.paths import (
    RANKINGS_DIR,
    RANKING_BY_PROFILE_DIR,
    FRONTEND_RANKING_DIR,
)


def calcular_score(row, peso_likes, peso_comments):
    likes = row['likes']
    comments = row['comments_count']
    seguidores = row['followers']

    M = (likes * peso_likes) + (comments * peso_comments)

    seguidores_validos = max(seguidores, 1)

    score = (math.log(M + 1) / math.log(seguidores_validos + 1)) * 100
    return round(score, 2)

def gerar_resumo_legenda(texto, limite=50):
    if not texto:
        return ''
    palavras = texto.split()
    if len(palavras) <= limite:
        return texto
    return ' '.join(palavras[:limite]) + '...'


def gerar_rankings(posts, PESO_LIKES, PESO_COMMENTS, total_posicoes):
    if not posts:
        print("Nenhum post encontrado para ranking.")
        return

    df = pd.DataFrame([
        {
            'source_profile': p.get('source_profile', 'unknown_profile'),
            'post_url': p.get('post_url', ''),
            'published_at': p.get('published_at', None),
            'legenda_post': p.get('legenda_post', ''),
            'likes': p.get('likes', 0),
            'comments_count': p.get('comments_count', 0),
            'followers': p.get('followers', 1),
        }
        for p in posts
    ])

    df[['likes', 'comments_count', 'followers']] = df[
        ['likes', 'comments_count', 'followers']
    ].fillna(0)

    df['followers'] = df['followers'].replace(0, 1)


    df['legenda_resumo'] = df['legenda_post'].apply(gerar_resumo_legenda)


    df['score_engajamento'] = df.apply(
        calcular_score,
        axis=1,
        args=(PESO_LIKES, PESO_COMMENTS)
    )

    RANKINGS_DIR.mkdir(parents=True, exist_ok=True)
    RANKING_BY_PROFILE_DIR.mkdir(parents=True, exist_ok=True)
    FRONTEND_RANKING_DIR.mkdir(parents=True, exist_ok=True)

    ranking_por_perfil = {}

    for perfil, grupo in df.groupby('source_profile'):
        ranking = grupo.sort_values(
            by='score_engajamento',
            ascending=False
        ).reset_index(drop=True)

        ranking['position'] = ranking.index + 1
        ranking_por_perfil[perfil] = ranking

    for perfil, ranking in ranking_por_perfil.items():
        perfil_filename = re.sub(r'[^a-zA-Z0-9_-]', '_', perfil)

        csv_path = (
           RANKING_BY_PROFILE_DIR
            / f"ranking_{perfil_filename}.csv"
        )
        ranking.head(total_posicoes).to_csv(
            csv_path,
            index=False,
            encoding='utf-8-sig'
        )

        json_path = (
            FRONTEND_RANKING_DIR
            / f"ranking_{perfil_filename}.json"
        )
        ranking.head(10).to_json(
            json_path,
            orient='records',
            force_ascii=False,
            indent=2
        )

    df_rank = df.sort_values(
        by='score_engajamento',
        ascending=False
    ).reset_index(drop=True)

    df_rank['position'] = df_rank.index + 1

    tabela_final = df_rank[
        [
            'position',
            'source_profile',
            'post_url',
            'published_at',
            'legenda_post',
            'legenda_resumo',
            'likes',
            'comments_count',
            'followers',
            'score_engajamento',
        ]
    ]

    print(tabela_final.head(total_posicoes).to_string(index=False))

    tabela_final.head(total_posicoes).to_csv(
    RANKINGS_DIR / "ranking_posts_geral.csv",
        index=False,
        encoding='utf-8-sig'
    )

    tabela_final.head(total_posicoes).to_json(
        FRONTEND_RANKING_DIR / "ranking_posts_geral.json",
        orient='records',
        force_ascii=False,
        indent=2
    )

    print(f"\nTotal de posts processados: {len(df)}")