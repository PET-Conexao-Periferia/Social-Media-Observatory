import math
import os
from pymongo import MongoClient

# Configurações do MongoDB
MONGO_URI = "mongodb://admin:secret@localhost:27018/?authSource=admin"
DB_NAME = "petri_database"
COLLECTION_NAME = "posts"

# Variáveis (Consistente com main.py)
PESO_LIKES = 0.7
PESO_COMMENTS = 0.43

def connect_mongo():
    try:
        client = MongoClient(MONGO_URI)
        return client[DB_NAME][COLLECTION_NAME]
    except Exception as e:
        print(f"Erro ao conectar ao MongoDB: {e}")
        return None

def gerar_ranking_no_banco(peso_likes=PESO_LIKES, peso_comments=PESO_COMMENTS, top_n=10):
    collection = connect_mongo()
    if collection is None:
        return

    # Pipeline de Agregação
    # A fórmula original é:
    # M = (likes * peso_likes) + (comments * peso_comments)
    # Score = (log(M + 1) / log(followers + 1)) * 100
    
    pipeline = [
        # Estágio 1: Filtrar documentos irrelevantes (opcional, mas recomendado)
        {
            "$match": {
                "likes": {"$exists": True},
                "comments_count": {"$exists": True}
            }
        },
        # Estágio 2: Calcular campos auxiliares para a fórmula
        {
            "$addFields": {
                "M": {
                    "$add": [
                        {"$multiply": ["$likes", peso_likes]},
                        {"$multiply": ["$comments_count", peso_comments]}
                    ]
                },
                # Se followers for 0 ou nulo, usar 1 para evitar divisão por zero no log
                "safe_followers": {
                    "$cond": {
                        "if": {"$gt": ["$followers", 0]}, 
                        "then": "$followers", 
                        "else": 1
                    }
                }
            }
        },
        # Estágio 3: Calcular o Score final
        {
            "$addFields": {
                "score_engajamento": {
                    "$multiply": [
                        {
                            "$divide": [
                                # log(M + 1)
                                {"$ln": {"$add": ["$M", 1]}},
                                # log(followers + 1) -> ln é log natural, base "e", 
                                # mas a divisão cancela a base, então funciona igual a log10
                                {"$ln": {"$add": ["$safe_followers", 1]}}
                            ]
                        },
                        100
                    ]
                }
            }
        },
        # Estágio 4: Ordenar pelo score (Decrescente)
        {
            "$sort": {"score_engajamento": -1}
        },
        # Estágio 5: Limitar o retorno (Paginação)
        {
            "$limit": top_n
        },
        # Estágio 6: Seleção final de campos (Projeção) para limpar a saída
        {
            "$project": {
                "_id": 0,
                "source_profile": 1,
                "likes": 1,
                "comments_count": 1,
                "followers": 1,
                "score_engajamento": {"$round": ["$score_engajamento", 2]}, # Arredondar para 2 casas
                "post_url": 1
            }
        }
    ]

    print(f"Executando Aggregation Pipeline no MongoDB (Top {top_n})...")
    
    # O parametro explain=True mostraria o plano de execução para análise do paper
    # cursor = collection.aggregate(pipeline) 
    
    import time
    start_time = time.time()
    
    resultados = list(collection.aggregate(pipeline))
    
    end_time = time.time()
    tempo_execucao = (end_time - start_time) * 1000 # ms

    print(f"Tempo de execução no Banco: {tempo_execucao:.2f} ms")
    print("-" * 80)
    print(f"{'PERFIL':<25} | {'SCORE':<8} | {'LIKES':<8} | {'COMMENTS':<8} | {'FOLLOWERS':<10}")
    print("-" * 80)

    for doc in resultados:
        print(f"{doc.get('source_profile', 'N/A')[:25]:<25} | "
              f"{doc.get('score_engajamento', 0):<8.2f} | "
              f"{doc.get('likes', 0):<8} | "
              f"{doc.get('comments_count', 0):<8} | "
              f"{doc.get('followers', 0):<10}")
    
    print("-" * 80)

if __name__ == "__main__":
    gerar_ranking_no_banco()
