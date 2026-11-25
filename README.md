# Observatório das Mídias Sociais do Litoral Norte

## 📌 Sobre

O **Observatório das Mídias Sociais do Litoral Norte** utiliza técnicas de **Inteligência Artificial**, **Recuperação de Informação** e **Ciência de Dados** para monitorar mídias sociais da região do Litoral Norte.  
O objetivo é identificar conteúdos com alto engajamento, detectar possíveis casos de **desinformação** e apoiar a equipe do **PET – Conexão Periferia** nas nossas atividades de integridade da informação.

A versão atual do projeto consiste em um **web scraping em Python**, responsável por coletar e ranquear informações de perfis do **Instagram** com maior engajamento da região do Litoral Norte.

---

## 🧰 Tecnologias utilizadas

- Python 3.x
- Selenium
- Pandas
- WebDriver (Chrome)
---

## 📦 Dependências do projeto

Para executar o projeto, é necessário instalar as seguintes bibliotecas Python:
```bash
pip install selenium pandas python-dotenv
````
---

## ▶️ Como testar o projeto

1. Faça uma cópia do arquivo .env.exemplo e renomeie para .env:
```bash
cp .env.exemplo .env
```
2. Substitua as informações do arquivo .env com seus próprios dados.

3. Crie um arquivo chamado perfils.txt contendo os perfis que deseja analisar (um perfil por linha).
Utilize este método caso tenha uma lista grande de perfis.

4. Caso queira analisar poucos perfis, você pode adicioná-los diretamente na variável PERFILS dentro do arquivo .env.

5. Execute o script principal:
```bash
python scrapper_instagram.py
```

## Executar a aplicação web

Requisitos: Python 3.10 ou superior e Node.js 20.19+ (ou 22.12+).

### Backend

No PowerShell, na raiz do repositório, crie e ative o ambiente virtual, instale
as dependências e baixe as stopwords do NLTK:

```powershell
py -m venv venv
.\venv\Scripts\Activate.ps1
python -m pip install -r Backend\requirements.txt
python -c "import nltk; nltk.download('stopwords')"
```

Inicie a API:

```powershell
python -m uvicorn Backend.api:app --reload --host 127.0.0.1 --port 8000
```

### Frontend

Abra um segundo terminal na raiz do repositório e execute:

```powershell
cd Frontend
npm install
npm run dev
```

Abra o endereço mostrado pelo Vite (normalmente `http://localhost:5173`). A
opção **Análise de Clusters** abre a página em `/clusters`.

### Dados locais

Os arquivos com posts, rankings e resultados de análise são dados locais e não
devem ser enviados ao repositório. Coloque os dados necessários em
`Backend/Data/` e `Frontend/public/`; essas pastas são ignoradas pelo Git. O
backend salva a última clusterização em `Backend/Data/ultima_clusterizacao.json`.
