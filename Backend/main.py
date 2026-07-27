# requisitos: pip install selenium pandas webdriver-manager python-dotenv

# importante: se quiser rodar com a janela do navegador, certifique-se de que headless=False nos arquivos main.py e driver.py nas linhas 71 e 6, respectivamente. Por padrão, roda sem a janela.

import os
import re
from datetime import datetime
from dotenv import load_dotenv

# VARIAVEIS 
PESO_LIKES = 1.4
PESO_COMMENTS = 8.6
quant_scrolagem =  1 #quanto maior o número, mais antigo será o post
rolagem_comentarios = 1
total_posicoes = 10 #número de posições a exibir no ranking final

# Período para filtrar posts 
PERIOD_START = "2000-01-01"    # exemplo: "2025-01-01" ou None
PERIOD_END = "2026-12-31"

from Backend.Services.Browser.driver_service import create_driver
from Backend.Services.Auth.auth_service import (
    carregar_cookies,
    salvar_cookies,
    is_logged_in,
    login_instagram,
)
from Backend.Services.Collector.scraper_service import raspar_perfil
from Backend.Services.Storage.storage_service import (
    carregar_posts_para_ranking,
)
from Backend.Services.Ranking.ranking_service import gerar_rankings



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
    driver = create_driver(headless=False)  #headless=False para rodar com a janela do navegador

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

            print(
                f"{len(dados)} posts processados para {perfil}"
            )


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
