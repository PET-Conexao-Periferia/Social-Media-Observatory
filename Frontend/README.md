# Frontend

This template should help get you started developing with Vue 3 in Vite.

## Recommended IDE Setup

[VS Code](https://code.visualstudio.com/) + [Vue (Official)](https://marketplace.visualstudio.com/items?itemName=Vue.volar) (and disable Vetur).

## Recommended Browser Setup

- Chromium-based browsers (Chrome, Edge, Brave, etc.):
  - [Vue.js devtools](https://chromewebstore.google.com/detail/vuejs-devtools/nhdogjmejiglipccpnnnanhbledajbpd)
  - [Turn on Custom Object Formatter in Chrome DevTools](http://bit.ly/object-formatters)
- Firefox:
  - [Vue.js devtools](https://addons.mozilla.org/en-US/firefox/addon/vue-js-devtools/)
  - [Turn on Custom Object Formatter in Firefox DevTools](https://fxdx.dev/firefox-devtools-custom-object-formatters/)

## Customize configuration

See [Vite Configuration Reference](https://vite.dev/config/).

## Project Setup

```sh
npm install
```

### Compile and Hot-Reload for Development

```sh
npm run dev
```

### Compile and Minify for Production

```sh
npm run build
```

A última clusterização realizada é salva pelo backend em
`Backend/Data/ultima_clusterizacao.json` e restaurada automaticamente ao abrir
`/clusters`. O `localStorage` do navegador permanece apenas como fallback para
análises antigas.

### Executar o backend

Na raiz do repositório, inicie a API:

```powershell
python -m uvicorn Backend.api:app --reload --host 127.0.0.1 --port 8000
```

### Executar o frontend

Em outro terminal, na raiz do repositório:

```powershell
cd Frontend
npm install
npm run dev
```

## Organização das páginas

`src/App.vue` mantém a navegação e seleciona a página pela URL. A análise de
clusters fica isolada em `src/pages/ClusterAnalysis.vue`; funções de formatação
compartilhadas ficam em `src/utils/legenda.js`.
