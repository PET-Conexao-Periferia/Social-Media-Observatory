import os
import json
import time
import re

def salvar_json(dados, nome_arquivo='dados_instagram.json'):
    try:
        base_dir = 'dados_por_perfil'
        os.makedirs(base_dir, exist_ok=True)

        total_comentarios = sum(len(post.get('comentarios', []))
                                for post in dados)
        print(
            f'\nDEBUG: Total de comentários a processar: {total_comentarios}')

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

            legenda = post.get('legenda_post') or ''
            likes = None
            comments_count = None
            if legenda:
                # procurar padrões como '699 likes, 8 comments' (insensível a maiúsculas)
                m = re.search(
                    r"([\d\.,]+)\s*likes?[,;:\s]+([\d\.,]+)\s*comments?", legenda, re.I)
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
                    legenda = re.sub(re.escape(m.group(0)),
                                     '', legenda).strip(' -:\n')
                else:
                    # tentar achar apenas likes ou apenas comments
                    m2 = re.search(r"([\d\.,]+)\s*likes?", legenda, re.I)
                    if m2:
                        try:
                            likes = int(re.sub(r"[^0-9]", "", m2.group(1)))
                        except Exception:
                            likes = None
                        legenda = re.sub(re.escape(m2.group(0)),
                                         '', legenda).strip(' -:\n')
                    m3 = re.search(r"([\d\.,]+)\s*comments?", legenda, re.I)
                    if m3:
                        try:
                            comments_count = int(
                                re.sub(r"[^0-9]", "", m3.group(1)))
                        except Exception:
                            comments_count = None
                        legenda = re.sub(re.escape(m3.group(0)),
                                         '', legenda).strip(' -:\n')

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
                                c_text = re.sub(
                                    re.escape(mlike.group(0)), '', c_text).strip()
                        except Exception:
                            c_likes = None

                comentarios_proc.append(
                    {'username': c_user, 'comment_text': c_text, 'likes': c_likes or 0})

                seguidores = post.get('followers', 0)
                try:
                    seguidores = int(seguidores)
                    if seguidores <= 0:
                        seguidores = 1
                except Exception:
                    seguidores = 1

            # Montar dicionário final para o post
            post_obj = {
                'post_url': post_url,
                'slug': slug,
                'legenda_post': legenda,
                'likes': likes or 0,
                'comments_count': comments_count if comments_count is not None else len(comentarios_proc),
                'comentarios': comentarios_proc,
                'source_profile': perfil,
                'followers': seguidores,
                'published_at': post.get('published_at') if post.get('published_at') else None,
            }

            # Salvar em arquivo por post
            filename = os.path.join(perfil_dir, f"{slug}.json")
            try:
                with open(filename, 'w', encoding='utf-8') as f:
                    json.dump(post_obj, f, ensure_ascii=False, indent=2)
                print(f'Salvo post em {filename}')
            except Exception as e:
                print(f'Erro ao salvar post {slug}: {e}')

            index.append(
                {'perfil': perfil, 'post_url': post_url, 'file': filename})

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
        
def carregar_posts_para_ranking(base_dir='dados_por_perfil'):
    posts = []

    if not os.path.exists(base_dir):
        return posts

    for perfil in os.listdir(base_dir):
        perfil_dir = os.path.join(base_dir, perfil)

        if not os.path.isdir(perfil_dir):
            continue

        for arquivo in os.listdir(perfil_dir):
            if arquivo.endswith('.json') and arquivo != 'index.json':
                caminho = os.path.join(perfil_dir, arquivo)
                try:
                    with open(caminho, 'r', encoding='utf-8') as f:
                        post = json.load(f)
                        posts.append(post)
                except Exception:
                    pass

    return posts
