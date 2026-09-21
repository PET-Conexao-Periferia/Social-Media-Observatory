<script setup>
import { ref, onMounted } from 'vue'

const ranking = ref([])
const loading = ref(true)
const startDate = ref(null)
const endDate = ref(null)
const expanded = ref({})

const toggleExpand = (index) => {
  expanded.value[index] = !expanded.value[index]
}

onMounted(async () => {
  try {
    const response = await fetch('/dados_ranking/ranking_posts_geral.json')
    ranking.value = await response.json()

    const published = ranking.value
      .map((i) => i.published_at)
      .filter(Boolean)
      .map((s) => new Date(s))

    if (published.length) {
      const times = published.map((d) => d.getTime())
      const min = new Date(Math.min(...times))
      const max = new Date(Math.max(...times))
      const fmt = (d) => d.toISOString().split('T')[0]
      startDate.value = fmt(min)
      endDate.value = fmt(max)
    }
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

      <p v-if="!loading && startDate && endDate" class="text-center text-gray-600 mb-4 text-xs sm:text-sm md:text-base">
        Período: {{ new Date(startDate).toLocaleDateString('pt-BR') }} — {{ new Date(endDate).toLocaleDateString('pt-BR') }}
      </p>

      <p v-else-if="!loading" class="text-center text-gray-600 mb-4 text-xs sm:text-sm md:text-base">
        Período: -
      </p>

      <p v-if="loading" class="text-center text-gray-500">
        Carregando dados...
      </p>

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
            <tr v-for="(item, index) in ranking" :key="item.source_profile" class="hover:bg-gray-50 transition">
              <td data-label="Posição" class="px-1 sm:px-2 py-2 font-semibold text-gray-600">
                {{ item.position }}
              </td>

              <td data-label="Perfil" class="px-1 sm:px-2 py-2 font-medium text-gray-800">
                {{ item.source_profile }}
              </td>

              <td data-label="Curtidas" class="px-1 sm:px-2 py-2">
                {{ item.likes }}
              </td>

              <td data-label="Comentários" class="px-1 sm:px-2 py-2">
                {{ item.comments_count }}
              </td>

              <td data-label="Reposts" class="px-1 sm:px-2 py-2">
                {{ Number(item.reposts || 0).toLocaleString('pt-BR') }}
              </td>

              <td data-label="Seguidores" class="px-1 sm:px-2 py-2 col-followers">
                {{ Number(item.followers).toLocaleString('pt-BR') }}
              </td>

              <td data-label="Engajamento" class="px-1 sm:px-2 py-2 font-semibold text-green-600">
                {{ item.score_engajamento.toFixed(2) }}
              </td>

              <td data-label="Data" class="px-1 sm:px-2 py-2 col-date">
                {{ item.published_at ? new Date(item.published_at).toLocaleDateString('pt-BR') : '-' }}
              </td>

              <td data-label="Legenda" class="px-1 sm:px-2 py-2">
                <div class="text-xs sm:text-sm text-gray-700 legenda-conteudo" :class="expanded[index]
                  ? 'whitespace-normal'
                  : 'whitespace-nowrap overflow-hidden text-ellipsis'">
                  {{
                    expanded[index]
                      ? getLegendaCompleta(item.legenda_post)
                      : formatLegenda(item.legenda_post, 150)
                  }}
                </div>

                <button v-if="getLegendaCompleta(item.legenda_post).length > 150" @click="toggleExpand(index)"
                  class="mt-1 text-blue-500 hover:underline text-xs font-medium">
                  {{ expanded[index] ? 'ver menos' : 'ver mais' }}
                </button>
              </td>

              <td data-label="Post" class="px-1 sm:px-2 py-2">
                <a :href="item.post_url" target="_blank" class="text-blue-500 hover:underline font-medium whitespace-nowrap">
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