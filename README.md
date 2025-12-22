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
