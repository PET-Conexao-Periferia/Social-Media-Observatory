import os
import re
from dotenv import load_dotenv

# VARIAVEIS 
PESO_LIKES = 0.7
PESO_COMMENTS = 0.43
quant_scrolagem = 1 # número de vezes que a página será rolada para carregar posts
rolagem_comentarios = 1  # número de vezes que a página será rolada para carregar mais comentários
total_posicoes = 2  # número de posições a exibir no ranking final

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

        for perfil in PERFIS:
            print(f"\nIniciando raspagem do perfil: {perfil}")
            dados, seguidores = raspar_perfil(driver, perfil)

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
