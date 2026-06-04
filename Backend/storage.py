import os
import json
import time
import re


def salvar_post_json(post):

    try:
        base_dir = "dados_por_perfil"
        os.makedirs(base_dir, exist_ok=True)

        perfil = post.get("source_profile") or "unknown_profile"

        perfil_dir = os.path.join(base_dir, perfil)
        os.makedirs(perfil_dir, exist_ok=True)

        post_url = post.get("post_url") or ""

        try:
            m = re.search(r"/p/([^/]+)/", post_url)

            if m:
                slug = m.group(1)
            else:
                slug = post_url.rstrip("/").split("/")[-1]

        except Exception:
            slug = str(int(time.time() * 1000))

        legenda = post.get("legenda_post") or ""

        likes = None
        comments_count = None

        if legenda:

            m = re.search(
                r"([\d\.,]+)\s*likes?[,;:\s]+([\d\.,]+)\s*comments?",
                legenda,
                re.I
            )

            if m:

                try:
                    likes = int(re.sub(r"[^0-9]", "", m.group(1)))
                except Exception:
                    likes = None

                try:
                    comments_count = int(
                        re.sub(r"[^0-9]", "", m.group(2))
                    )
                except Exception:
                    comments_count = None

                legenda = re.sub(
                    re.escape(m.group(0)),
                    "",
                    legenda
                ).strip(" -:\n")

            else:

                m2 = re.search(
                    r"([\d\.,]+)\s*likes?",
                    legenda,
                    re.I
                )

                if m2:
                    try:
                        likes = int(
                            re.sub(r"[^0-9]", "", m2.group(1))
                        )
                    except Exception:
                        likes = None

                    legenda = re.sub(
                        re.escape(m2.group(0)),
                        "",
                        legenda
                    ).strip(" -:\n")

                m3 = re.search(
                    r"([\d\.,]+)\s*comments?",
                    legenda,
                    re.I
                )

                if m3:
                    try:
                        comments_count = int(
                            re.sub(r"[^0-9]", "", m3.group(1))
                        )
                    except Exception:
                        comments_count = None

                    legenda = re.sub(
                        re.escape(m3.group(0)),
                        "",
                        legenda
                    ).strip(" -:\n")

        comentarios = post.get("comentarios", []) or []

        comentarios_proc = []

        for item in comentarios:

            c_user = item.get("username") or ""
            c_text = item.get("comment_text") or ""

            c_likes = item.get("likes", 0)

            comentarios_proc.append({
                "username": c_user,
                "comment_text": c_text,
                "likes": c_likes
            })

        seguidores = post.get("followers", 0)

        try:
            seguidores = int(seguidores)

            if seguidores <= 0:
                seguidores = 1

        except Exception:
            seguidores = 1

        post_obj = {
            "post_url": post_url,
            "slug": slug,
            "legenda_post": legenda,
            "likes": likes or 0,
            "comments_count": (
                comments_count
                if comments_count is not None
                else len(comentarios_proc)
            ),
            "comentarios": comentarios_proc,
            "source_profile": perfil,
            "followers": seguidores,
            "published_at": post.get("published_at"),
            "error": post.get("error")
        }

        filename = os.path.join(
            perfil_dir,
            f"{slug}.json"
        )

        with open(
            filename,
            "w",
            encoding="utf-8"
        ) as f:

            json.dump(
                post_obj,
                f,
                ensure_ascii=False,
                indent=2
            )

        print(f"Post salvo imediatamente: {filename}")

        atualizar_index(
            perfil=perfil,
            post_url=post_url,
            filename=filename
        )

    except Exception as e:
        print(f"Erro ao salvar post individual: {e}")


def atualizar_index(perfil, post_url, filename):

    try:

        base_dir = "dados_por_perfil"

        idx_file = os.path.join(
            base_dir,
            "index.json"
        )

        if os.path.exists(idx_file):

            with open(
                idx_file,
                "r",
                encoding="utf-8"
            ) as f:

                try:
                    index = json.load(f)
                except Exception:
                    index = []

        else:
            index = []

        novo_item = {
            "perfil": perfil,
            "post_url": post_url,
            "file": filename
        }

        ja_existe = any(
            item.get("post_url") == post_url
            for item in index
        )

        if not ja_existe:

            index.append(novo_item)

            with open(
                idx_file,
                "w",
                encoding="utf-8"
            ) as f:

                json.dump(
                    index,
                    f,
                    ensure_ascii=False,
                    indent=2
                )

    except Exception as e:
        print(f"Erro ao atualizar índice: {e}")


def salvar_json(dados):

    for post in dados:
        salvar_post_json(post)


def carregar_posts_para_ranking(
    base_dir="dados_por_perfil"
):
    posts = []

    if not os.path.exists(base_dir):
        return posts

    for perfil in os.listdir(base_dir):

        perfil_dir = os.path.join(
            base_dir,
            perfil
        )

        if not os.path.isdir(perfil_dir):
            continue

        for arquivo in os.listdir(perfil_dir):

            if (
                arquivo.endswith(".json")
                and arquivo != "index.json"
            ):

                caminho = os.path.join(
                    perfil_dir,
                    arquivo
                )

                try:

                    with open(
                        caminho,
                        "r",
                        encoding="utf-8"
                    ) as f:

                        post = json.load(f)

                    posts.append(post)

                except Exception as e:
                    print(
                        f"Erro ao ler {caminho}: {e}"
                    )

    return posts