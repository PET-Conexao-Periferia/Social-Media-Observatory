import os
import re
import math
import pandas as pd


def calcular_score(row, peso_likes, peso_comments):
    likes = row['likes']
    comments = row['comments_count']
    seguidores = row['followers']

    M = (likes * peso_likes) + (comments * peso_comments)

    seguidores_validos = max(seguidores, 1)

    score = (math.log(M + 1) / math.log(seguidores_validos + 1)) * 100
    return round(score, 2)


def gerar_rankings(posts, PESO_LIKES, PESO_COMMENTS, total_posicoes):
    if not posts:
        print("Nenhum post encontrado para ranking.")
        return

    df = pd.DataFrame([
        {
            'source_profile': p.get('source_profile', 'unknown_profile'),
            'post_url': p.get('post_url', ''),
            'published_at': p.get('published_at', None),
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

    df['score_engajamento'] = df.apply(
        calcular_score,
        axis=1,
        args=(PESO_LIKES, PESO_COMMENTS)
    )

    base_ranking_dir = 'rankings_geral'
    ranking_por_perfil_dir = os.path.join(
        base_ranking_dir,
        'ranking_por_perfil'
    )
    os.makedirs(ranking_por_perfil_dir, exist_ok=True)

    frontend_public_dir = os.path.join(
        '..',
        'Frontend',
        'Frontend',
        'public',
        'dados_ranking'
    )
    os.makedirs(frontend_public_dir, exist_ok=True)

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

        csv_path = os.path.join(
            ranking_por_perfil_dir,
            f'ranking_{perfil_filename}.csv'
        )
        ranking.head(total_posicoes).to_csv(
            csv_path,
            index=False,
            encoding='utf-8-sig'
        )

        json_path = os.path.join(
            frontend_public_dir,
            f'ranking_{perfil_filename}.json'
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
            'likes',
            'comments_count',
            'followers',
            'score_engajamento',
        ]
    ]

    print(tabela_final.head(total_posicoes).to_string(index=False))

    tabela_final.head(total_posicoes).to_csv(
        os.path.join(
            base_ranking_dir,
            'ranking_posts_geral.csv',
        ),
        index=False,
        encoding='utf-8-sig'
    )

    tabela_final.head(total_posicoes).to_json(
        os.path.join(
            frontend_public_dir,
            'ranking_posts_geral.json'
        ),
        orient='records',
        force_ascii=False,
        indent=2
    )

    print(f"\nTotal de posts processados: {len(df)}")
