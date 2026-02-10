from flask import Flask, jsonify
from flask_cors import CORS
from pymongo import MongoClient

app = Flask(__name__)
CORS(app)  # Habilitar CORS para o Frontend acessar

# Configurações do MongoDB
MONGO_URI = "mongodb://admin:secret@localhost:27018/?authSource=admin"
DB_NAME = "petri_database"
COLLECTION_NAME = "posts"

def connect_mongo():
    try:
        client = MongoClient(MONGO_URI)
        return client[DB_NAME][COLLECTION_NAME]
    except Exception as e:
        print(f"Erro ao conectar ao MongoDB: {e}")
        return None

@app.route('/ranking', methods=['GET'])
def get_ranking():
    # Parâmetros fixos por enquanto (podem virar query params no futuro)
    PESO_LIKES = 0.7
    PESO_COMMENTS = 0.43
    TOP_N = 50 

    collection = connect_mongo()
    if collection is None:
        return jsonify({"error": "Database connection failed"}), 500

    pipeline = [
        # Match apenas posts com dados válidos
        {"$match": { "likes": {"$exists": True}, "comments_count": {"$exists": True} } },
        
        # Calcular M e Safe Followers
        {"$addFields": {
            "M": { "$add": [ {"$multiply": ["$likes", PESO_LIKES]}, {"$multiply": ["$comments_count", PESO_COMMENTS]} ] },
            "safe_followers": { "$cond": { "if": {"$gt": ["$followers", 0]}, "then": "$followers", "else": 1 } }
        }},
        
        # Calcular Score
        {"$addFields": {
            "score_engajamento": {
                "$multiply": [
                    { "$divide": [
                        {"$ln": {"$add": ["$M", 1]}},
                        {"$ln": {"$add": ["$safe_followers", 1]}}
                    ]},
                    100
                ]
            }
        }},
        
        # Ordenar e Limitar
        {"$sort": {"score_engajamento": -1}},
        {"$limit": TOP_N},
        
        # Projetar apenas o necessário
        {"$project": {
            "_id": 0,
            "source_profile": 1,
            "likes": 1,
            "comments_count": 1,
            "followers": 1,
            "score_engajamento": {"$round": ["$score_engajamento", 2]},
            "post_url": 1,
            "slug": 1
        }}
    ]

    try:
        resultados = list(collection.aggregate(pipeline))
        return jsonify(resultados)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    print("Servidor rodando em http://localhost:5000")
    app.run(debug=True, port=5000)
