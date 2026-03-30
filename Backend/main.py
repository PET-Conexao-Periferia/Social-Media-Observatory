# requisitos:
# pip install selenium pandas webdriver-manager python-dotenv

import os
import re
from datetime import datetime
from dotenv import load_dotenv

# VARIAVEIS 
PESO_LIKES = 1.4
PESO_COMMENTS = 8.6
quant_scrolagem = 5 # número de vezes que a página será rolada para carregar posts
rolagem_comentarios = 1  # número de vezes que a página será rolada para carregar mais comentários
total_posicoes = 20  # número de posições a exibir no ranking final

# Período para filtrar posts (especificar aqui no formato YYYY-MM-DD ou None)
PERIOD_START = "2026-02-01"  # exemplo: "2025-01-01" ou None
PERIOD_END = "2026-02-07"    # exemplo: "2025-01-31" ou None

from driver import create_driver
from auth import (
    carregar_cookies,
    salvar_cookies,
    is_logged_in,
    login_instagram,
)
from scraper import raspar_perfil
from storage import (
    salvar_json,
    carregar_posts_para_ranking,
)
from ranking import gerar_rankings



# CONFIGURAÇÕES GERAIS


load_dotenv()

USUARIO = os.getenv("USUARIO")
SENHA = os.getenv("SENHA")

PERFIS = os.getenv("PERFIS").split(",") if os.getenv("PERFIS") else []


# CARREGAR PERFIS DO TXT


try:
    with open("perfis.txt", "r", encoding="utf-8") as pf:
        file_perfis = [
            line.strip()
            for line in pf
            if line.strip() and not line.strip().startswith("#")
        ]
        if file_perfis:
            PERFIS = file_perfis
except FileNotFoundError:
    pass
except Exception as e:
    print(f"Erro ao ler perfis.txt: {e}")



# MAIN


def main():
    driver = create_driver(headless=False)

    try:
        loaded = carregar_cookies(driver)
        if loaded and is_logged_in(driver, USUARIO):
            print("Sessão restaurada via cookies. Pulando login.")
        else:
            print("Necessário efetuar login interativo.")
            ok = login_instagram(driver, USUARIO, SENHA)
            if ok:
                try:
                    salvar_cookies(driver)
                except Exception as e:
                    print(f"Não foi possível salvar cookies: {e}")
            else:
                print(
                    "Atenção: login não confirmado. "
                    "Você pode continuar manualmente no navegador aberto."
                )

        all_data = []

        # converter strings de período para objetos date (ou None)
        try:
            start_date = datetime.fromisoformat(PERIOD_START).date() if PERIOD_START else None
        except Exception:
            start_date = None
        try:
            end_date = datetime.fromisoformat(PERIOD_END).date() if PERIOD_END else None
        except Exception:
            end_date = None

        for perfil in PERFIS:
            print(f"\nIniciando raspagem do perfil: {perfil}")
            dados, seguidores = raspar_perfil(
                driver,
                perfil,
                quant_scrolagem=quant_scrolagem,
                rolagem_comentarios=rolagem_comentarios,
                start_date=start_date,
                end_date=end_date,
            )

            for post in dados:
                post["source_profile"] = perfil
                post["followers"] = seguidores

            all_data.extend(dados)

        salvar_json(all_data)

        posts = carregar_posts_para_ranking()
        gerar_rankings(
        posts,
        PESO_LIKES,
        PESO_COMMENTS,
        total_posicoes
        )


    finally:
        driver.quit()


if __name__ == "__main__":
    main()
