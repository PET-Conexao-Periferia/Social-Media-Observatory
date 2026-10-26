import csv
import json
import re
from datetime import date, datetime, timedelta
from pathlib import Path

from nltk.corpus import stopwords
from sklearn.cluster import KMeans
from sklearn.feature_extraction.text import TfidfVectorizer

from Backend.Config.paths import DATA_DIR, RANKINGS_DIR

CUSTOM_STOP_WORDS = {
    # Palavras genéricas e verbos comuns
    "gente", "fazer", "sempre", "verdade", "aqui", "hoje", "talvez", "tudo", "vai", "ser",
    "ter", "ver", "todas", "todos", "assim", "pode", "sobre", "ainda", "só", "so",
    "simbora", "juntos", "vamos", "cada", "responder", "continue", "chama",
    
    # Coloquialismos e contrações
    "tá", "ta", "pra", "pro", "cadê", "cade", "vc", "vcs", "né", "ne", "já", "ja", "aí", "ai",
    
    # Metadados e interface do Instagram em Português
    "curtidas", "curtida", "respostas", "resposta", "comentários", "comentário", 
    "post", "posts", "tradução", "traducao", "ver", "mais", "menos",
    
    # Metadados e interface do Instagram em Inglês
    "reply", "replies", "all", "view", "likes", "like", "translation", "see", 
    "comment", "comments", "share", "follow", "followed", "profile", "edited",
    "english", "and", "others", "hidden", "offensive", "misleading", "tap", 
    "sensitive", "content", "information",
}


def _posts_dir():
    for name in ("posts coletados", "dados_por_perfil", "Posts-Coletados"):
        candidate = DATA_DIR / name
        if candidate.exists():
            return candidate
    return DATA_DIR / "posts coletados"


def _read_json_objects(path):
    try:
        with path.open("r", encoding="utf-8") as file:
            content = json.load(file)
    except (OSError, json.JSONDecodeError):
        return []
    return content if isinstance(content, list) else [content]


def _post_key(post):
    return post.get("post_url") or post.get("slug") or post.get("id")


def _load_posts():
    posts = []
    posts_root = _posts_dir()
    if not posts_root.exists():
        return posts

    for profile_dir in (path for path in posts_root.iterdir() if path.is_dir()):
        for path in profile_dir.rglob("*.json"):
            if path.name == "index.json":
                continue
            posts.extend(
                item for item in _read_json_objects(path)
                if isinstance(item, dict)
            )
    return posts


def _get_profile_stopwords():
    """Extrai automaticamente todos os usernames de perfis da base para que não virem clusters."""
    posts = _load_posts()
    profiles = set()
    for post in posts:
        prof = str(post.get("source_profile") or "").lower().strip()
        if prof and prof != "-":
            profiles.add(prof)
            clean_prof = re.sub(r"[^\w\s]", "", prof)
            if clean_prof:
                profiles.add(clean_prof)
    return profiles


def _stop_words():
    """ÚNICA definição de stop words: PT + EN + Custom + Perfis."""
    try:
        words_pt = stopwords.words("portuguese")
        words_en = stopwords.words("english")
    except LookupError as error:
        raise RuntimeError(
            "Os dados de stop words do NLTK não foram instalados. "
            "Execute nltk.download('stopwords')."
        ) from error
        
    return set(words_pt) | set(words_en) | CUSTOM_STOP_WORDS | _get_profile_stopwords()


def _load_scores():
    scores = {}
    for path in RANKINGS_DIR.rglob("*.json"):
        for item in _read_json_objects(path):
            key = _post_key(item)
            if key is not None and item.get("score_engajamento") is not None:
                scores[key] = float(item["score_engajamento"])

    for path in RANKINGS_DIR.rglob("*.csv"):
        try:
            with path.open("r", encoding="utf-8-sig", newline="") as file:
                for item in csv.DictReader(file):
                    key = _post_key(item)
                    if key is not None and item.get("score_engajamento"):
                        scores[key] = float(item["score_engajamento"])
        except (OSError, ValueError):
            continue
    return scores


def _clean_text(text):
    text = str(text or "").lower().replace("\n", " ")
    
    # 1. Remove qualquer menção (@usuario) ou hashtag (#tag) até o próximo espaço
    text = re.sub(r'[@#]\S+', ' ', text)
    
    # 2. Remove pontuações e caracteres especiais
    text = re.sub(r"[^\w\s]", " ", text, flags=re.UNICODE)
    
    # 3. Remove números isolados ou em sequência
    text = re.sub(r"\d+", " ", text)
    
    # 4. Remove palavras com underline (handles/usernames sem o símbolo @)
    words = [w for w in text.split() if '_' not in w]
    
    return " ".join(words)


def _post_text(post):
    # Foca EXCLUSIVAMENTE na legenda do post (ignora comentários)
    return _clean_text(post.get("legenda_post", ""))


def _gerar_log_debug(rows, stop_words_usadas):
    """Gera um arquivo de log com os textos limpos para verificação."""
    try:
        log_path = DATA_DIR / "debug_processamento.log"
        with log_path.open("w", encoding="utf-8") as f:
            f.write("=== LOG DE PROCESSAMENTO SEMÂNTICO DE POSTS ===\n")
            f.write(f"Total de posts processados: {len(rows)}\n")
            f.write(f"Total de Stop Words ativas: {len(stop_words_usadas)}\n\n")
            f.write("--- PERFIS IDENTIFICADOS COMO STOP WORDS ---\n")
            perfis = sorted(list(_get_profile_stopwords()))
            f.write(", ".join(perfis) + "\n\n")
            f.write("--- AMOSTRA DOS TEXTOS APÓS LIMPEZA ---\n")
            for i, row in enumerate(rows[:50], 1):
                f.write(f"[{i}] Perfil: {row['source_profile']} | URL: {row['post_url']}\n")
                f.write(f"    Texto Limpo: {row['text']}\n\n")
    except Exception as e:
        print(f"Aviso: Não foi possível salvar o arquivo de log: {e}")


def _resolve_period(posts, start_date=None, end_date=None):
    if start_date is not None or end_date is not None:
        return start_date, end_date

    published_dates = []
    for post in posts:
        try:
            published_dates.append(
                datetime.fromisoformat(
                    post.get("published_at", "").replace("Z", "+00:00")
                ).date()
            )
        except (AttributeError, TypeError, ValueError):
            continue

    if not published_dates:
        return None, None

    end_date = max(published_dates)
    return end_date - timedelta(days=6), end_date


def _dataset(start_date=None, end_date=None):
    posts = _load_posts()
    start_date, end_date = _resolve_period(posts, start_date, end_date)
    scores = _load_scores()
    rows = []
    for post in posts:
        published_at = post.get("published_at")
        if start_date or end_date:
            try:
                published_date = datetime.fromisoformat(
                    published_at.replace("Z", "+00:00")
                ).date()
            except (AttributeError, TypeError, ValueError):
                continue
            if start_date and published_date < start_date:
                continue
            if end_date and published_date > end_date:
                continue

        text = _post_text(post)
        if text.strip():
            rows.append({
                "id": _post_key(post) or str(len(rows)),
                "text": text,
                "score_engajamento": scores.get(_post_key(post), 0.0),
                "post_url": post.get("post_url", ""),
                "legenda_post": post.get("legenda_post", ""),
                "source_profile": post.get("source_profile", "-"),
                "published_at": post.get("published_at"),
            })
            
    if len(rows) < 2:
        raise ValueError("São necessários pelo menos dois posts com texto para agrupar.")
        
    # Gera o arquivo de log para auditoria dos textos limpos
    _gerar_log_debug(rows, _stop_words())
    
    return rows


def _vectorize(rows):
    vectorizer = TfidfVectorizer(
        max_df=0.8,
        min_df=3,
        stop_words=list(_stop_words()),
    )
    try:
        matrix = vectorizer.fit_transform([row["text"] for row in rows])
    except ValueError as error:
        raise ValueError(
            "Não há termos suficientes após o pré-processamento para criar o TF-IDF."
        ) from error
    return vectorizer, matrix


def _encontrar_k_ideal(ks, inertias):
    if not ks or not inertias or len(ks) != len(inertias):
        raise ValueError("A curva do cotovelo precisa ter pontos válidos.")

    if len(ks) == 1:
        return ks[0]

    x1, y1 = ks[0], inertias[0]
    x2, y2 = ks[-1], inertias[-1]
    maior_distancia = -1
    k_ideal = ks[0]

    for x0, y0 in zip(ks, inertias):
        distancia = abs(
            (y2 - y1) * x0
            - (x2 - x1) * y0
            + x2 * y1
            - y2 * x1
        )
        if distancia > maior_distancia:
            maior_distancia = distancia
            k_ideal = x0

    return k_ideal


def calcular_cotovelo(start_date=None, end_date=None):
    rows = _dataset(start_date, end_date)
    _, matrix = _vectorize(rows)
    max_k = min(50, matrix.shape[0])
    ks = list(range(2, max_k + 1))
    
    inertias = [
        float(KMeans(n_clusters=k, random_state=42, n_init=10).fit(matrix).inertia_)
        for k in ks
    ]
    k_sugerido = _encontrar_k_ideal(ks, inertias)
    
    resolved_start, resolved_end = _resolve_period(
        _load_posts(), start_date, end_date
    )
    return {
        "k_sugerido": k_sugerido,
        "elbow": [{"k": k, "inertia": inertia} for k, inertia in zip(ks, inertias)],
        "periodo": {
            "start_date": resolved_start.isoformat() if resolved_start else None,
            "end_date": resolved_end.isoformat() if resolved_end else None,
        },
    }


def clusterizar(k_escolhido, start_date=None, end_date=None):
    rows = _dataset(start_date, end_date)
    vectorizer, matrix = _vectorize(rows)
    if not 2 <= k_escolhido <= min(50, len(rows)):
        raise ValueError(f"k deve estar entre 2 e {min(50, len(rows))}.")

    model = KMeans(n_clusters=k_escolhido, random_state=42, n_init=10)
    labels = model.fit_predict(matrix)
    terms = vectorizer.get_feature_names_out()
    groups = []
    
    for cluster_id in range(k_escolhido):
        indexes = [index for index, label in enumerate(labels) if label == cluster_id]
        keywords = [terms[index] for index in model.cluster_centers_[cluster_id].argsort()[::-1][:10]]
        cluster_posts = [{key: row[key] for key in (
            "id", "post_url", "legenda_post", "source_profile", "published_at", "score_engajamento"
        )} for index in indexes for row in [rows[index]]]
        
        average = sum(post["score_engajamento"] for post in cluster_posts) / len(cluster_posts)
        groups.append({
            "cluster_id": cluster_id,
            "engajamento_medio": round(average, 2),
            "total_posts": len(cluster_posts),
            "palavras_chave": keywords,
            "posts": cluster_posts,
        })
        
    groups.sort(key=lambda group: group["engajamento_medio"], reverse=True)
    resolved_start, resolved_end = _resolve_period(
        _load_posts(), start_date, end_date
    )
    return {
        "k_escolhido": k_escolhido,
        "total_clusters": len(groups),
        "total_posts": len(rows),
        "periodo": {
            "start_date": resolved_start.isoformat() if resolved_start else None,
            "end_date": resolved_end.isoformat() if resolved_end else None,
        },
        "clusters": groups,
    }


def clusterizar(k_escolhido, start_date=None, end_date=None):
    rows = _dataset(start_date, end_date)
    vectorizer, matrix = _vectorize(rows)
    if not 2 <= k_escolhido <= min(50, len(rows)):
        raise ValueError(f"k deve estar entre 2 e {min(50, len(rows))}.")

    model = KMeans(n_clusters=k_escolhido, random_state=42, n_init=10)
    labels = model.fit_predict(matrix)
    terms = vectorizer.get_feature_names_out()
    groups = []
    
    for cluster_id in range(k_escolhido):
        indexes = [index for index, label in enumerate(labels) if label == cluster_id]
        keywords = [terms[index] for index in model.cluster_centers_[cluster_id].argsort()[::-1][:10]]
        cluster_posts = [{key: row[key] for key in (
            "id", "post_url", "legenda_post", "source_profile", "published_at", "score_engajamento"
        )} for index in indexes for row in [rows[index]]]
        
        # Cálculos de engajamento
        total_engajamento = sum(post["score_engajamento"] for post in cluster_posts)
        average = total_engajamento / len(cluster_posts)
        
        groups.append({
            "cluster_id": cluster_id,
            "engajamento_medio": round(average, 2),
            "engajamento_somado": round(total_engajamento, 2),
            "total_posts": len(cluster_posts),
            "palavras_chave": keywords,
            "posts": cluster_posts,
        })
        
    # Mantém a ordenação por engajamento médio
    groups.sort(key=lambda group: group["engajamento_medio"], reverse=True)
    resolved_start, resolved_end = _resolve_period(
        _load_posts(), start_date, end_date
    )
    return {
        "k_escolhido": k_escolhido,
        "total_clusters": len(groups),
        "total_posts": len(rows),
        "periodo": {
            "start_date": resolved_start.isoformat() if resolved_start else None,
            "end_date": resolved_end.isoformat() if resolved_end else None,
        },
        "clusters": groups,
    }