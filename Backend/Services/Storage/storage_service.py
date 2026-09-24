import json
import time
import re
from Backend.Config.paths import PROFILES_DIR

def salvar_post_json(post):

    try:
        PROFILES_DIR.mkdir(parents=True, exist_ok=True)

        perfil = post.get("source_profile") or "unknown_profile"

        perfil_dir = PROFILES_DIR / perfil
        perfil_dir.mkdir(parents=True, exist_ok=True)

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

        filename = perfil_dir / f"{slug}.json"
        

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

        idx_file = PROFILES_DIR / "index.json"

        if idx_file.exists():

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
            "file":str(filename) 
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


def carregar_posts_para_ranking(base_dir=PROFILES_DIR):
    posts = []

    if not base_dir.exists():
        return posts

    for perfil_dir in base_dir.iterdir():


        if not perfil_dir.is_dir():
            continue

        for arquivo in perfil_dir.iterdir():

            if (
                    arquivo.suffix == ".json"
                    and arquivo.name != "index.json"
            ):

                try:

                    with open(
                        arquivo,
                        "r",
                        encoding="utf-8"
                    ) as f:

                        post = json.load(f)

                    posts.append(post)

                except Exception as e:
                    print(
                        f"Erro ao ler {arquivo}: {e}"
                    )

    return posts