<script setup>
import { ref, computed, onMounted } from 'vue'

const ranking = ref([])
const loading = ref(true)
const startDate = ref(null)
const endDate = ref(null)
const quantidadePosts = ref(10)
const expanded = ref({})

const toggleExpand = (index) => {
  expanded.value[index] = !expanded.value[index]
}

const formatDateInput = (date) => {
  const year = date.getFullYear()
  const month = String(date.getMonth() + 1).padStart(2, '0')
  const day = String(date.getDate()).padStart(2, '0')

  return `${year}-${month}-${day}`
}

const rankingFiltrado = computed(() => {
  if (!startDate.value || !endDate.value) {
    return []
  }

  const inicio = new Date(`${startDate.value}T00:00:00`)
  const fim = new Date(`${endDate.value}T23:59:59`)

  return ranking.value
    .filter((item) => {
      if (!item.published_at) return false

      const dataPost = new Date(item.published_at)

      return dataPost >= inicio && dataPost <= fim
    })
    .sort((a, b) => {
      return Number(b.score_engajamento) - Number(a.score_engajamento)
    })
    .map((item, index) => ({
      ...item,
      position: index + 1
    }))
})

const rankingExibido = computed(() => {
  return rankingFiltrado.value.slice(0, quantidadePosts.value)
})

onMounted(async () => {
  try {
    const response = await fetch('/dados_ranking/ranking_posts_geral.json')
    ranking.value = await response.json()

    const hoje = new Date()
    const seteDiasAtras = new Date(hoje)

    seteDiasAtras.setDate(hoje.getDate() - 6)

    startDate.value = formatDateInput(seteDiasAtras)
    endDate.value = formatDateInput(hoje)
  } catch (error) {
    console.error('Erro ao carregar ranking:', error)
  } finally {
    loading.value = false
  }
})

const formatLegenda = (texto, limite = 150) => {
  if (!texto) return '-'

  let resultado = texto

  if (resultado.includes(':')) {
    resultado = resultado.split(':').slice(1).join(':').trim()
  }

  const match = resultado.match(/["“](.*?)["”]/)

  if (match) {
    resultado = match[1]
  }

  resultado = resultado.replace(/\n/g, ' ')

  if (resultado.length > limite) {
    resultado = resultado.substring(0, limite) + '...'
  }

  return resultado
}

const getLegendaCompleta = (texto) => {
  if (!texto) return '-'

  let resultado = texto

  if (resultado.includes(':')) {
    resultado = resultado.split(':').slice(1).join(':').trim()
  }

  const match = resultado.match(/["“](.*?)["”]/)

  if (match) {
    resultado = match[1]
  }

  return resultado.replace(/\n/g, ' ')
}
</script>

<template>
  <nav class="w-full bg-white shadow-md px-3 sm:px-6 py-3 sm:py-4 flex flex-col sm:flex-row items-center justify-between gap-3 sm:gap-4">
    <img src="@/assets/logo-pet-horizontal.svg" alt="Logo" class="h-10 sm:h-14 md:h-16 sm:ml-2 md:ml-8 mt-1 sm:mt-3" />

    <h1 class="text-sm sm:text-lg md:text-xl font-bold text-center text-gray-700 leading-tight px-2">
      Observatório das Mídias Sociais do Litoral Norte - PE
    </h1>

    <ul class="flex text-gray-700 font-medium sm:mr-2 md:mr-8">
      <li>
        <a href="/" class="hover:text-blue-600 transition">Sobre</a>
      </li>
    </ul>
  </nav>

  <div class="w-full max-w-[1600px] mx-auto mt-4 sm:mt-6 md:mt-8 px-2 sm:px-4 lg:px-6">
    <div class="bg-white rounded-xl shadow-lg p-2 sm:p-4 md:p-6">
      <h2 class="text-lg sm:text-2xl font-medium text-center text-gray-800 mb-4 sm:mb-6">
        Ranking de Engajamento geral
      </h2>

      <div v-if="!loading" class="flex flex-col sm:flex-row items-center justify-center gap-3 sm:gap-4 mb-4 sm:mb-6">
        <div class="flex flex-col w-full sm:w-auto">
          <label for="start-date" class="text-xs sm:text-sm font-medium text-gray-600 mb-1">
            Data inicial
          </label>

          <input
            id="start-date"
            v-model="startDate"
            type="date"
            class="border border-gray-300 rounded-lg px-3 py-2 text-sm text-gray-700 focus:outline-none focus:ring-2 focus:ring-blue-400 w-full sm:w-auto"
          />
        </div>

        <div class="flex flex-col w-full sm:w-auto">
          <label for="end-date" class="text-xs sm:text-sm font-medium text-gray-600 mb-1">
            Data final
          </label>

          <input
            id="end-date"
            v-model="endDate"
            type="date"
            class="border border-gray-300 rounded-lg px-3 py-2 text-sm text-gray-700 focus:outline-none focus:ring-2 focus:ring-blue-400 w-full sm:w-auto"
          />
        </div>

        <div class="flex flex-col w-full sm:w-auto">
          <label for="quantidade-posts" class="text-xs sm:text-sm font-medium text-gray-600 mb-1">
            Quantidade de posts
          </label>

          <select
            id="quantidade-posts"
            v-model.number="quantidadePosts"
            class="border border-gray-300 rounded-lg px-3 py-2 text-sm text-gray-700 bg-white focus:outline-none focus:ring-2 focus:ring-blue-400 w-full sm:w-auto"
          >
            <option :value="5">5</option>
            <option :value="10">10</option>
            <option :value="20">20</option>
            <option :value="30">30</option>
            <option :value="50">50</option>
            <option :value="100">100</option>
          </select>
        </div>
      </div>

      <p v-if="!loading && startDate && endDate" class="text-center text-gray-600 mb-4 text-xs sm:text-sm md:text-base">
        Período: {{ new Date(`${startDate}T00:00:00`).toLocaleDateString('pt-BR') }} — {{ new Date(`${endDate}T00:00:00`).toLocaleDateString('pt-BR') }}
      </p>

      <p v-if="!loading && rankingFiltrado.length > 0" class="text-center text-gray-500 mb-4 text-xs sm:text-sm">
        Exibindo {{ Math.min(quantidadePosts, rankingFiltrado.length) }} de {{ rankingFiltrado.length }} posts encontrados no período.
      </p>

      <p v-if="loading" class="text-center text-gray-500">
        Carregando dados...
      </p>

      <div v-else-if="rankingFiltrado.length === 0" class="text-center text-gray-500 py-8">
        Nenhum post encontrado no período selecionado.
      </div>

      <div v-else class="w-full">
        <table class="ranking-table w-full border border-gray-200 rounded-lg overflow-hidden">
          <thead class="bg-gray-100 text-gray-700 text-[10px] sm:text-xs lg:text-sm uppercase">
            <tr>
              <th class="px-1 sm:px-2 py-2 text-left">Pos.</th>
              <th class="px-1 sm:px-2 py-2 text-left">Perfil</th>
              <th class="px-1 sm:px-2 py-2 text-left">Curtidas</th>
              <th class="px-1 sm:px-2 py-2 text-left">Comentários</th>
              <th class="px-1 sm:px-2 py-2 text-left">Reposts</th>
              <th class="px-1 sm:px-2 py-2 text-left col-followers">Seguidores</th>
              <th class="px-1 sm:px-2 py-2 text-left">Engajamento</th>
              <th class="px-1 sm:px-2 py-2 text-left col-date">Data</th>
              <th class="px-1 sm:px-2 py-2 text-left">Legenda</th>
              <th class="px-1 sm:px-2 py-2 text-left">Post</th>
            </tr>
          </thead>

          <tbody class="divide-y divide-gray-200">
            <tr v-for="(item, index) in rankingExibido" :key="item.post_url || `${item.source_profile}-${item.published_at}-${index}`" class="hover:bg-gray-50 transition">
              <td data-label="Posição" class="px-1 sm:px-2 py-2 font-semibold text-gray-600">
                {{ item.position }}
              </td>

              <td data-label="Perfil" class="px-1 sm:px-2 py-2 font-medium text-gray-800">
                {{ item.source_profile }}
              </td>

              <td data-label="Curtidas" class="px-1 sm:px-2 py-2">
                {{ Number(item.likes || 0).toLocaleString('pt-BR') }}
              </td>

              <td data-label="Comentários" class="px-1 sm:px-2 py-2">
                {{ Number(item.comments_count || 0).toLocaleString('pt-BR') }}
              </td>

              <td data-label="Reposts" class="px-1 sm:px-2 py-2">
                {{ Number(item.reposts || 0).toLocaleString('pt-BR') }}
              </td>

              <td data-label="Seguidores" class="px-1 sm:px-2 py-2 col-followers">
                {{ Number(item.followers || 0).toLocaleString('pt-BR') }}
              </td>

              <td data-label="Engajamento" class="px-1 sm:px-2 py-2 font-semibold text-green-600">
                {{ Number(item.score_engajamento || 0).toFixed(2) }}
              </td>

              <td data-label="Data" class="px-1 sm:px-2 py-2 col-date">
                {{ item.published_at ? new Date(item.published_at).toLocaleDateString('pt-BR') : '-' }}
              </td>

              <td data-label="Legenda" class="px-1 sm:px-2 py-2">
                <div
                  class="text-xs sm:text-sm text-gray-700 legenda-conteudo"
                  :class="expanded[index]
                    ? 'whitespace-normal'
                    : 'whitespace-nowrap overflow-hidden text-ellipsis'"
                >
                  {{
                    expanded[index]
                      ? getLegendaCompleta(item.legenda_post)
                      : formatLegenda(item.legenda_post, 150)
                  }}
                </div>

                <button
                  v-if="getLegendaCompleta(item.legenda_post).length > 150"
                  @click="toggleExpand(index)"
                  class="mt-1 text-blue-500 hover:underline text-xs font-medium"
                >
                  {{ expanded[index] ? 'ver menos' : 'ver mais' }}
                </button>
              </td>

              <td data-label="Post" class="px-1 sm:px-2 py-2">
                <a
                  :href="item.post_url"
                  target="_blank"
                  rel="noopener noreferrer"
                  class="text-blue-500 hover:underline font-medium whitespace-nowrap"
                >
                  Ver Post
                </a>
              </td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>
  </div>
</template>