import re
import math
import pandas as pd
from Backend.Config.paths import (
    RANKINGS_DIR,
    RANKING_BY_PROFILE_DIR,
    FRONTEND_RANKING_DIR,
)


# Calcula o score de engajamento proporcional aos seguidores.
def calcular_score(row):
    likes = row['likes']
    comments = row['comments_count']
    reposts = row['reposts']
    seguidores = row['followers']

    M = (likes * 1) + (comments * 3) + (reposts * 6)

    seguidores_validos = max(seguidores, 1)

    score = (math.log(M + 1) / math.log(seguidores_validos + 1)) * 100
    return round(score, 2)


# Gera um resumo da legenda para exibição no ranking.
def gerar_resumo_legenda(texto, limite=50):
    if not texto:
        return ''
    palavras = texto.split()
    if len(palavras) <= limite:
        return texto
    return ' '.join(palavras[:limite]) + '...'


# Remove duplicidades mantendo a ocorrência com mais seguidores.
def remover_posts_duplicados(df):
    if df.empty:
        return df

    df = df.copy()

    df['post_url'] = df['post_url'].fillna('').astype(str).str.strip()

    posts_com_url = df[df['post_url'] != ''].copy()
    posts_sem_url = df[df['post_url'] == ''].copy()

    if posts_com_url.empty:
        return df

    posts_com_url = posts_com_url.sort_values(
        by=['post_url', 'followers'],
        ascending=[True, False]
    )

    posts_com_url = posts_com_url.drop_duplicates(
        subset='post_url',
        keep='first'
    )

    return pd.concat(
        [posts_com_url, posts_sem_url],
        ignore_index=True
    )


# Gera os rankings geral e por perfil.
def gerar_rankings(posts):
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
            'reposts': p.get('reposts', 0),
            'followers': p.get('followers', 1),
        }
        for p in posts
    ])

    df[['likes', 'comments_count', 'reposts', 'followers']] = df[
        ['likes', 'comments_count', 'reposts', 'followers']
    ].fillna(0)

    df['followers'] = df['followers'].replace(0, 1)

    total_antes = len(df)

    # Remove duplicidades antes de calcular o score.
    df = remover_posts_duplicados(df)

    total_depois = len(df)

    duplicados_removidos = total_antes - total_depois

    if duplicados_removidos > 0:
        print(
            f"Posts duplicados removidos do ranking: "
            f"{duplicados_removidos}"
        )

    df['legenda_resumo'] = df['legenda_post'].apply(
        gerar_resumo_legenda
    )

    df['score_engajamento'] = df.apply(
        calcular_score,
        axis=1
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
        perfil_filename = re.sub(
            r'[^a-zA-Z0-9_-]',
            '_',
            perfil
        )

        csv_path = (
            RANKING_BY_PROFILE_DIR
            / f"ranking_{perfil_filename}.csv"
        )

        ranking.to_csv(
            csv_path,
            index=False,
            encoding='utf-8-sig'
        )

        json_path = (
            FRONTEND_RANKING_DIR
            / f"ranking_{perfil_filename}.json"
        )

        ranking.to_json(
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
            'reposts',
            'followers',
            'score_engajamento',
        ]
    ]

    tabela_final.to_csv(
        RANKINGS_DIR / "ranking_posts_geral.csv",
        index=False,
        encoding='utf-8-sig'
    )

    tabela_final.to_json(
        FRONTEND_RANKING_DIR / "ranking_posts_geral.json",
        orient='records',
        force_ascii=False,
        indent=2
    )

    print(f"\nTotal de posts processados: {len(df)}")