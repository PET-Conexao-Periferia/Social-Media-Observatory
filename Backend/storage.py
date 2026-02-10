import os
import json
import time
import re
import datetime
from pymongo import MongoClient

# Configurações do MongoDB
MONGO_URI = "mongodb://admin:secret@localhost:27018/?authSource=admin"
DB_NAME = "petri_database"
COLLECTION_NAME = "posts"

def get_mongo_collection():
    try:
        client = MongoClient(MONGO_URI)
        return client[DB_NAME][COLLECTION_NAME]
    except Exception as e:
        print(f"Erro ao conectar no MongoDB: {e}")
        return None

def salvar_no_mongo(dados, perfil_nome, verbose=True):
    """
    Salva ou atualiza lista de posts no MongoDB.
    Substitui a antiga função salvar_json.
    """
    collection = get_mongo_collection()
    if collection is None:
        return

    if verbose:
        print(f"\n[Storage] Iniciando salvamento de {len(dados)} posts para o perfil '{perfil_nome}' no MongoDB...")
    
    count_inserted = 0
    count_updated = 0

    for post in dados:
        # 1. Garantir campos essenciais
        post['source_profile'] = perfil_nome
        post['last_updated'] = datetime.datetime.utcnow()

        # 2. Tratamento de URL/Slug (Identificador Único)
        post_url = post.get('post_url') or ''
        slug = None

        if post_url:
            try:
                # Tenta extrair ID do /p/ID/
                m = re.search(r"/p/([^/]+)/", post_url)
                if m:
                    slug = m.group(1)
                else:
                    slug = post_url.rstrip('/').split('/')[-1]
            except Exception:
                pass
        
        # Se não achou slug na URL, cria um hash grosseiro ou pula
        if not slug:
            # Tentar usar timestamp se não tiver post_url valido, mas ideal é ter post_url
            slug = f"unknown_{int(time.time()*1000)}"

        post['slug'] = slug

        # 3. Tratamento de números (Likes/Comments como Int)
        legenda = post.get('legenda_post') or ''
        # Se o scraper já extraiu likes/comments limpos, ótimo. 
        # Se não, tentamos extrair da legenda como fallback.
        # (Assumindo que o scraper.py já tenta preencher, mas vamos garantir tipagem)
        
        # Lógica de extração de inteiros da legenda (mantida do original)
        if 'likes' not in post or post['likes'] is None:
             m = re.search(r"([\d\.,]+)\s*likes?", legenda, re.I)
             if m:
                 try: 
                    post['likes'] = int(re.sub(r"[^0-9]", "", m.group(1))) 
                 except: post['likes'] = 0
        
        # Garantir que seja int
        try:
            if post.get('likes'): post['likes'] = int(post['likes'])
        except: post['likes'] = 0

        try:
            if post.get('comments_count'): post['comments_count'] = int(post['comments_count'])
        except: post['comments_count'] = 0


        # 4. Operação de Upsert no Banco
        # Procura por 'slug'. Se achar, atualiza ($set). Se não, insere.
        filtro = {"slug": slug}
        
        try:
            # Usar $set para atualizar apenas os campos enviados, mantendo outros se existirem
            res = collection.update_one(filtro, {"$set": post}, upsert=True)
            if res.upserted_id:
                count_inserted += 1
            elif res.modified_count > 0:
                count_updated += 1
        except Exception as e:
            print(f"Erro ao salvar post {slug}: {e}")

    if verbose and (count_inserted > 0 or count_updated > 0):
        print(f"[Storage] Concluído: {count_inserted} novos, {count_updated} atualizados.")


def salvar_json(dados, nome_arquivo='dados_instagram.json'):
    # Função depreciada, mantendo apenas wrapper para não quebrar chamadas antigas se houver
    if not dados:
        return
    
    perfil = dados[0].get('source_profile') or 'unknown'
    salvar_no_mongo(dados, perfil)


