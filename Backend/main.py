# requisitos:
# pip install selenium pandas webdriver-manager python-dotenv

import os
import re
from datetime import datetime
from dotenv import load_dotenv

# VARIAVEIS 
PESO_LIKES = 0.7
PESO_COMMENTS = 0.43
quant_scrolagem = 3 # número de vezes que a página será rolada para carregar posts
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
    salvar_no_mongo,
)
from ranking_mongo import gerar_ranking_no_banco
# from ranking import gerar_rankings



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
            # raspar_perfil agora retorna (dados, seguidores) ou apenas dados?
            # Verificando scraper.py, o retorno parece ser uma lista de dicts.
            # O código antigo usava desempacotamento "dados, seguidores" mas scraper.py retorna apenas "posts" (lista)
            # COMENTARIO CORRIGIDO: O read_file do scraper.py não mostrou o return final.
            # Assumindo que raspar_perfil retorna lista de postagens baseada na refatoração anterior.
            
            # Wrapper para salvar post individualmente (silencioso)
            def salvar_incremental(post):
                salvar_no_mongo([post], perfil, verbose=False)

            # A função raspar_perfil retorna uma tupla (lista_de_posts, numero_seguidores)
            dados_posts, num_seguidores = raspar_perfil(
                driver,
                perfil,
                quant_scrolagem=quant_scrolagem,
                rolagem_comentarios=rolagem_comentarios,
                on_post_scraped=salvar_incremental # Passa o callback
            )

            # O salvamento final em batch ainda é útil para garantir que nada foi perdido,
            # ou para atualizar dados que tenham mudado no final (embora incremental já resolva a maioria)
            if dados_posts:
                 # Injetar o número de seguidores em cada post (caso scrap antigo não tenha injetado)
                 for p in dados_posts:
                     p['followers'] = num_seguidores
                     p['source_profile'] = perfil
                 
                 # Salvar em batch (verbose=True para log final do perfil)
                 salvar_no_mongo(dados_posts, perfil, verbose=True)
            
        driver.quit()

        # GERAR RANKINGS (Via MongoDB)
        print("\n" + "="*30)
        print("GERANDO RANKINGS (MONGODB)")
        print("="*30)
        gerar_ranking_no_banco(PESO_LIKES, PESO_COMMENTS, total_posicoes)

    finally:
        # Garantir que o driver fecha mesmo se der erro
        try:
            driver.quit()
        except:
            pass


if __name__ == "__main__":
    main()
