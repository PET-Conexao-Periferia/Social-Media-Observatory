from pathlib import Path

BACKEND_DIR = Path(__file__).resolve().parent.parent

DATA_DIR = BACKEND_DIR / "Data"

PROFILES_DIR = DATA_DIR / "dados_por_perfil"

RANKINGS_DIR = DATA_DIR / "rankings_geral"

RANKING_BY_PROFILE_DIR = RANKINGS_DIR / "ranking_por_perfil"

AUTH_DIR = BACKEND_DIR / "Services" / "Auth"

COOKIES_FILE = AUTH_DIR / "cookies_instagram.json"

DEBUG_POST_FILE = BACKEND_DIR / "debug_post.html"

FRONTEND_RANKING_DIR = (
    BACKEND_DIR.parent
    / "Frontend"
    / "public"
    / "dados_ranking"
)