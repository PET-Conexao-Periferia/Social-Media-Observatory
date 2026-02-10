# PETri - Observatório das Mídias Sociais

Este projeto é uma ferramenta de analytics desenvolvida para monitorar, coletar e classificar o engajamento de perfis do Instagram. O projeto utiliza uma arquitetura moderna orientada a dados, substituindo o processamento tradicional em memória por **Pipelines de Agregação no MongoDB**.

## 🚀 Arquitetura

*   **Coleta (Scraper):** Python + Selenium (Extrai dados em tempo real).
*   **Armazenamento:** MongoDB (Dockerizado).
*   **API:** Flask (Serve os rankings processados pelo banco).
*   **Frontend:** Vue.js + TailwindCSS (Visualização dos dados).

---

## 📋 Pré-requisitos

*   **Docker Desktop** (Obrigatório para o banco de dados).
*   **Python 3.10+**.
*   **Node.js 16+**.
*   **Google Chrome** (Para o Selenium).

---

## 🛠️ Instalação e Execução

Para rodar o projeto completo, você precisará de **3 terminais** abertos.

### Passo 1: Subir o Banco de Dados (Terminal 1)
O banco de dados roda em um container Docker. Execute na raiz do projeto:

```powershell
# Sobe o container do MongoDB em segundo plano
docker-compose up -d
```
*Nota: O banco estará acessível externamente na porta **27018** para não conflitar com instalações locais do Mongo.*

### Passo 2: Rodar a API Backend (Terminal 2)
Este servidor disponibiliza os dados para o site.

1.  Acesse a pasta do backend:
    ```powershell
    cd Backend
    ```
2.  Instale as dependências:
    ```powershell
    pip install selenium pymongo python-dotenv flask flask-cors pandas
    ```
3.  Configure as variáveis de ambiente:
    *   Renomeie o arquivo `.env.example` para `.env`.
    *   Edite o `.env` e coloque seu **usuário e senha do Instagram** (necessário para o scraper).
4.  Suba o servidor:
    ```powershell
    python server.py
    ```
    *O servidor rodará em `http://localhost:5000`.*

### Passo 3: Rodar o Frontend (Terminal 3)
A interface gráfica para visualizar os rankings.

1.  Acesse a pasta do frontend:
    ```powershell
    cd Frontend/Frontend
    ```
2.  Instale as dependências:
    ```powershell
    npm install
    ```
3.  Rode o servidor de desenvolvimento:
    ```powershell
    npm run dev
    ```
    *Acesse o link que aparecerá (geralmente `http://localhost:5173`).*

---

## 🕷️ Como Coletar Dados (Rodar o Scraper)

Com o **passo 1 e 2 rodando**, você pode iniciar a coleta de dados. Abra um **novo terminal** na pasta `Backend` e rode:

```powershell
cd Backend
python main.py
```

*   O navegador abrirá automaticamente.
*   O sistema fará login no Instagram.
*   Os posts serão raspados e salvos no MongoDB **em tempo real**.
*   Se você estiver com o Frontend aberto, verá os dados aparecendo automaticamente na tabela.

---

## 🧹 Comandos Úteis

### Limpar o Banco de Dados
Caso os dados estejam corrompidos ou você queira iniciar uma coleta limpa, use este comando no PowerShell (na raiz do projeto):

```powershell
docker exec petri_mongo mongosh "mongodb://admin:secret@localhost:27017/petri_database?authSource=admin" --eval "db.posts.deleteMany({})"
```

### Reiniciar o Banco de Dados (Reset Total)
Se tiver problemas de conexão ou autenticação com o Docker:

```powershell
docker-compose down -v
docker-compose up -d
```

### Verificar Logs do Banco
```powershell
docker logs petri_mongo
```

---

## 🧪 Estrutura de Diretórios Importantes

*   `Backend/scraper.py`: Lógica de extração do Instagram (Selenium).
*   `Backend/storage.py`: Lógica de conexão e salvamento no MongoDB.
*   `Backend/server.py`: API Flask que executa o Aggregation Pipeline para gerar o ranking.
*   `Backend/main.py`: Orquestrador principal da coleta.
*   `Frontend/Frontend/src/App.vue`: Componente principal que consome a API.
