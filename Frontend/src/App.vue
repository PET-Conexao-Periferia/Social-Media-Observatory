<script setup>
import { computed, ref, onMounted } from 'vue'

const ranking = ref([])
const loading = ref(true)
const availableStartDate = ref(null)
const availableEndDate = ref(null)
const selectedStartDate = ref('')
const selectedEndDate = ref('')
const expanded = ref({})
const isClusters = window.location.pathname === '/clusters'
const elbow = ref([])
const selectedK = ref(27)
const suggestedK = ref(null)
const clusters = ref([])
const clusterLoading = ref(false)
const clusterError = ref('')
const elbowReady = ref(false)
const useAllClusterPosts = ref(false)
const clusterStartDate = ref('')
const clusterEndDate = ref('')
const activeRanking = ref('average')

// Ordenações computadas para a visualização dividida em duas colunas
const clustersByAverage = computed(() => {
  return [...clusters.value].sort((a, b) => (b.engajamento_medio || 0) - (a.engajamento_medio || 0))
})

const clustersByTotal = computed(() => {
  return [...clusters.value].sort((a, b) => (b.engajamento_somado || 0) - (a.engajamento_somado || 0))
})

const activeClusters = computed(() => {
  return activeRanking.value === 'average' ? clustersByAverage.value : clustersByTotal.value
})

// Configuração completa do gráfico SVG no estilo Matplotlib
const chartConfig = computed(() => {
  if (!elbow.value || !elbow.value.length) return null

  const data = elbow.value
  const inertias = data.map((item) => item.inertia)

  const minVal = Math.min(...inertias)
  const maxVal = Math.max(...inertias)

  const rangeVal = maxVal - minVal || 1
  const paddingY = rangeVal * 0.1

  let yMin = Math.max(0, Math.floor(minVal - paddingY))
  let yMax = Math.ceil(maxVal + paddingY)

  if (yMax > 100) {
    yMin = Math.max(0, Math.floor(yMin / 50) * 50)
    yMax = Math.ceil(yMax / 50) * 50
  }

  const width = 850
  const height = 450
  const margin = { top: 45, right: 35, bottom: 65, left: 75 }

  const plotWidth = width - margin.left - margin.right
  const plotHeight = height - margin.top - margin.bottom

  const points = data.map((item, index) => {
    const x = margin.left + (index / Math.max(data.length - 1, 1)) * plotWidth
    const y = margin.top + plotHeight - ((item.inertia - yMin) / Math.max(yMax - yMin, 1)) * plotHeight
    return { x, y, k: item.k, inertia: item.inertia }
  })

  const pointsString = points.map((p) => `${p.x},${p.y}`).join(' ')

  const yTickCount = 6
  const yTicks = []
  for (let i = 0; i < yTickCount; i++) {
    const val = yMin + (i / (yTickCount - 1)) * (yMax - yMin)
    const y = margin.top + plotHeight - ((val - yMin) / Math.max(yMax - yMin, 1)) * plotHeight
    yTicks.push({ val: Math.round(val), y })
  }

  return {
    width,
    height,
    margin,
    plotWidth,
    plotHeight,
    points,
    pointsString,
    yTicks,
    yMin,
    yMax
  }
})

const toggleExpand = (index) => {
  expanded.value[index] = !expanded.value[index]
}

const filteredRanking = computed(() => {
  const hasFilter = selectedStartDate.value || selectedEndDate.value
  const start = selectedStartDate.value ? new Date(`${selectedStartDate.value}T00:00:00`) : null
  const end = selectedEndDate.value ? new Date(`${selectedEndDate.value}T23:59:59.999`) : null

  if (start && end && start > end) return []

  const posts = hasFilter
    ? ranking.value.filter((item) => {
        if (!item.published_at) return false
        const published = new Date(item.published_at)
        return (!start || published >= start) && (!end || published <= end)
      })
    : ranking.value

  return posts.slice(0, 10).map((item, index) => ({
    ...item,
    position: index + 1,
  }))
})

const clearDateFilter = () => {
  selectedStartDate.value = ''
  selectedEndDate.value = ''
}

const selectAllClusterPosts = () => {
  if (useAllClusterPosts.value) {
    clusterStartDate.value = ''
    clusterEndDate.value = ''
  }
  elbowReady.value = false
  elbow.value = []
  suggestedK.value = null
  clusters.value = []
}

const updateClusterPeriod = () => {
  useAllClusterPosts.value = false
  elbowReady.value = false
  elbow.value = []
  suggestedK.value = null
  clusters.value = []
}

const clusterPeriodQuery = () => {
  const params = new URLSearchParams()
  if (!useAllClusterPosts.value && clusterStartDate.value) params.set('start_date', clusterStartDate.value)
  if (!useAllClusterPosts.value && clusterEndDate.value) params.set('end_date', clusterEndDate.value)
  return params.toString()
}

const initializeClusters = async () => {
  await calculateElbow()
  if (elbowReady.value && suggestedK.value) {
    await generateClusters()
  }
}

onMounted(async () => {
  if (isClusters) {
    await initializeClusters()
    return
  }
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
      availableStartDate.value = fmt(min)
      availableEndDate.value = fmt(max)
    }
  } catch (error) {
    console.error('Erro ao carregar ranking:', error)
  } finally {
    loading.value = false
  }
})

const calculateElbow = async () => {
  clusterLoading.value = true
  clusterError.value = ''
  try {
    const query = clusterPeriodQuery()
    const response = await fetch(`/api/clusters/elbow${query ? `?\${query}` : ''}`)
    if (!response.ok) throw new Error((await response.json()).detail || 'Não foi possível calcular o cotovelo.')
    const result = await response.json()
    elbow.value = result.elbow
    suggestedK.value = result.k_sugerido
    selectedK.value = result.k_sugerido
    if (result.periodo) {
      clusterStartDate.value = result.periodo.start_date || ''
      clusterEndDate.value = result.periodo.end_date || ''
    }
    elbowReady.value = true
  } catch (error) {
    clusterError.value = error.message
  } finally {
    clusterLoading.value = false
  }
}

const generateClusters = async () => {
  clusterLoading.value = true
  clusterError.value = ''
  try {
    const response = await fetch('/api/clusters', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        k: Number(selectedK.value),
        start_date: useAllClusterPosts.value ? null : clusterStartDate.value || null,
        end_date: useAllClusterPosts.value ? null : clusterEndDate.value || null,
      }),
    })
    if (!response.ok) throw new Error((await response.json()).detail || 'Não foi possível agrupar os posts.')
    clusters.value = (await response.json()).clusters
  } catch (error) {
    clusterError.value = error.message
  } finally {
    clusterLoading.value = false
  }
}

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
  <nav class="w-full bg-white shadow-md px-6 py-4 flex items-center justify-between">
    <img src="@/assets/logo-pet-horizontal.svg" alt="Logo" class="h-16 ml-8 mt-3" />

    <h1 class="text-xl font-bold text-center text-gray-700">
      Observatório das Mídias Sociais do Litoral Norte - PE
    </h1>

    <ul class="flex gap-6 text-gray-700 font-medium mr-8">
      <li>
        <a href="/clusters" class="hover:text-blue-600 transition">Análise de Clusters</a>
      </li>
      <li>
        <a href="/" class="hover:text-blue-600 transition">Sobre</a>
      </li>
    </ul>
  </nav>

  <div v-if="isClusters" class="max-w-7xl mx-auto mt-10 p-6 bg-white rounded-xl shadow-lg">
    <div class="flex flex-wrap items-start justify-between gap-4 mb-8">
      <div>
        <p class="text-sm font-semibold uppercase tracking-wide text-blue-600">Machine Learning</p>
        <h2 class="text-3xl font-bold text-gray-800 mt-1">Análise de Clusters</h2>
        <p class="text-gray-600 mt-2">Descubra os temas dos posts e compare o engajamento médio de cada grupo.</p>
      </div>
      <button @click="calculateElbow" :disabled="clusterLoading" class="px-5 py-3 rounded-lg bg-blue-600 text-white font-semibold hover:bg-blue-700 disabled:opacity-50">
        {{ clusterLoading && !elbowReady ? 'Gerando gráfico...' : 'Gerar gráfico' }}
      </button>
    </div>

    <p v-if="clusterError" class="mb-5 rounded-lg bg-red-50 p-4 text-red-700">{{ clusterError }}</p>

    <div class="mb-8 rounded-lg border border-blue-100 bg-blue-50 p-4">
      <h3 class="mb-3 font-semibold text-gray-800">Período das postagens</h3>
      <label class="mb-4 flex items-center gap-2 text-sm font-medium text-gray-700">
        <input v-model="useAllClusterPosts" @change="selectAllClusterPosts" type="checkbox" class="h-4 w-4 accent-blue-600" />
        Todos os posts
      </label>
      <div class="flex flex-wrap items-end gap-4">
        <label class="flex flex-col gap-1 text-sm font-semibold text-gray-700">
          De
          <input v-model="clusterStartDate" @input="updateClusterPeriod" :disabled="useAllClusterPosts" type="date" class="rounded-md border border-gray-300 bg-white px-3 py-2 font-normal disabled:cursor-not-allowed disabled:bg-gray-100" />
        </label>
        <label class="flex flex-col gap-1 text-sm font-semibold text-gray-700">
          Até
          <input v-model="clusterEndDate" @input="updateClusterPeriod" :disabled="useAllClusterPosts" type="date" class="rounded-md border border-gray-300 bg-white px-3 py-2 font-normal disabled:cursor-not-allowed disabled:bg-gray-100" />
        </label>
        <span class="text-sm text-gray-600">
          {{ useAllClusterPosts ? 'A análise usará todos os posts disponíveis.' : 'A análise usará somente o período selecionado.' }}
        </span>
      </div>
    </div>

    <!-- CONTROLES DE CLUSTERIZAÇÃO -->
    <div class="mb-8 flex flex-wrap items-end gap-4 border-b border-gray-100 pb-6">
      <label class="flex flex-col gap-1 text-sm font-semibold text-gray-700">
        Número de clusters (k)
        <input v-model.number="selectedK" type="number" min="2" max="50" class="w-36 rounded-lg border border-gray-300 px-3 py-2 text-base font-normal focus:border-blue-500 focus:outline-none" />
      </label>
      <button @click="generateClusters" :disabled="clusterLoading || !selectedK" class="rounded-lg bg-emerald-600 px-5 py-3 font-semibold text-white hover:bg-emerald-700 disabled:opacity-50">
        {{ clusterLoading ? 'Processando...' : 'Clusterizar e Gerar Ranking' }}
      </button>
      <span v-if="suggestedK" class="text-sm font-semibold text-blue-700">
        k sugerido pelo cotovelo: {{ suggestedK }}
      </span>
    </div>

    <!-- SEÇÃO DO GRÁFICO DE RSS ESTILO MATPLOTLIB -->
    <section v-if="elbowReady && chartConfig" class="border-t border-gray-100 pt-6 mb-8">
      <h3 class="text-xl font-semibold text-gray-800 mb-4">Curva de RSS</h3>
      <div class="overflow-x-auto rounded-xl bg-white border border-gray-200 p-4 shadow-sm">
        <svg
          :viewBox="`0 0 ${chartConfig.width} ${chartConfig.height}`"
          class="w-full h-auto min-w-[750px]"
          role="img"
          aria-label="Gráfico do Método do Cotovelo"
        >
          <!-- Fundo Branco -->
          <rect width="100%" height="100%" fill="#ffffff" />

          <!-- Título do Gráfico -->
          <text
            :x="chartConfig.width / 2"
            y="25"
            text-anchor="middle"
            font-size="15"
            font-weight="700"
            fill="#1e293b"
          >
            Método do Cotovelo (Elbow Method) - Dados Reais
          </text>

          <!-- Grade Horizontal (Y) -->
          <line
            v-for="tick in chartConfig.yTicks"
            :key="'grid-y-' + tick.val"
            :x1="chartConfig.margin.left"
            :y1="tick.y"
            :x2="chartConfig.width - chartConfig.margin.right"
            :y2="tick.y"
            stroke="#e2e8f0"
            stroke-dasharray="3 3"
          />

          <!-- Grade Vertical (X) -->
          <line
            v-for="p in chartConfig.points"
            :key="'grid-x-' + p.k"
            :x1="p.x"
            :y1="chartConfig.margin.top"
            :x2="p.x"
            :y2="chartConfig.height - chartConfig.margin.bottom"
            stroke="#f1f5f9"
            stroke-dasharray="2 2"
          />

          <!-- Eixo X Principal -->
          <line
            :x1="chartConfig.margin.left"
            :y1="chartConfig.height - chartConfig.margin.bottom"
            :x2="chartConfig.width - chartConfig.margin.right"
            :y2="chartConfig.height - chartConfig.margin.bottom"
            stroke="#334155"
            stroke-width="1.5"
          />

          <!-- Eixo Y Principal -->
          <line
            :x1="chartConfig.margin.left"
            :y1="chartConfig.margin.top"
            :x2="chartConfig.margin.left"
            :y2="chartConfig.height - chartConfig.margin.bottom"
            stroke="#334155"
            stroke-width="1.5"
          />

          <!-- Rótulos e Traços do Eixo Y -->
          <g v-for="tick in chartConfig.yTicks" :key="'label-y-' + tick.val">
            <line
              :x1="chartConfig.margin.left - 5"
              :y1="tick.y"
              :x2="chartConfig.margin.left"
              :y2="tick.y"
              stroke="#334155"
              stroke-width="1.5"
            />
            <text
              :x="chartConfig.margin.left - 8"
              :y="tick.y + 4"
              text-anchor="end"
              font-size="11"
              font-weight="500"
              fill="#475569"
            >
              {{ tick.val }}
            </text>
          </g>

          <!-- Título do Eixo Y -->
          <text
            :transform="`rotate(-90, 22, ${chartConfig.margin.top + chartConfig.plotHeight / 2})`"
            :x="22"
            :y="chartConfig.margin.top + chartConfig.plotHeight / 2"
            text-anchor="middle"
            font-size="12"
            font-weight="600"
            fill="#334155"
          >
            Inércia (Soma dos Quadrados)
          </text>

          <!-- Rótulos e Traços do Eixo X (Para cada k de 2 a 50) -->
          <g v-for="p in chartConfig.points" :key="'label-x-' + p.k">
            <line
              :x1="p.x"
              :y1="chartConfig.height - chartConfig.margin.bottom"
              :x2="p.x"
              :y2="chartConfig.height - chartConfig.margin.bottom + 5"
              stroke="#334155"
              stroke-width="1"
            />
            <text
              :x="p.x"
              :y="chartConfig.height - chartConfig.margin.bottom + 18"
              text-anchor="middle"
              font-size="9.5"
              font-weight="500"
              fill="#475569"
            >
              {{ p.k }}
            </text>
          </g>

          <!-- Título do Eixo X -->
          <text
            :x="chartConfig.margin.left + chartConfig.plotWidth / 2"
            :y="chartConfig.height - 15"
            text-anchor="middle"
            font-size="12"
            font-weight="600"
            fill="#334155"
          >
            Número de Clusters (k)
          </text>

          <!-- Linha Tracejada do Gráfico -->
          <polyline
            :points="chartConfig.pointsString"
            fill="none"
            stroke="#2563eb"
            stroke-width="2.2"
            stroke-dasharray="5 3"
            stroke-linecap="round"
            stroke-linejoin="round"
          />

          <!-- Marcadores (Pontos Azuis com Borda Branca) -->
          <circle
            v-for="p in chartConfig.points"
            :key="'dot-' + p.k"
            :cx="p.x"
            :cy="p.y"
            r="4"
            fill="#1d4ed8"
            stroke="#ffffff"
            stroke-width="1.5"
          >
            <title>k = {{ p.k }} | Inércia: {{ p.inertia.toFixed(2) }}</title>
          </circle>
        </svg>
      </div>
    </section>

    <!-- RANKING DOS CLUSTERS -->
    <section v-if="clusters.length" class="border-t border-gray-100 pt-6">
      <div class="mb-6 flex border-b border-gray-200" role="tablist" aria-label="Rankings de engajamento">
        <button
          type="button"
          role="tab"
          :aria-selected="activeRanking === 'average'"
          @click="activeRanking = 'average'"
          :class="activeRanking === 'average'
            ? 'border-b-2 border-emerald-600 text-emerald-700'
            : 'text-gray-500 hover:border-gray-300 hover:text-gray-700'"
          class="flex-1 px-4 py-3 text-sm font-semibold transition"
        >
          📊 Ranking de Engajamento Médio
        </button>
        <button
          type="button"
          role="tab"
          :aria-selected="activeRanking === 'total'"
          @click="activeRanking = 'total'"
          :class="activeRanking === 'total'
            ? 'border-b-2 border-blue-600 text-blue-700'
            : 'text-gray-500 hover:border-gray-300 hover:text-gray-700'"
          class="flex-1 px-4 py-3 text-sm font-semibold transition"
        >
          📈 Ranking de Engajamento Somado
        </button>
      </div>

      <div class="space-y-3">
        <details
          v-for="(cluster, index) in activeClusters"
          :key="`${activeRanking}-${cluster.cluster_id}`"
          class="rounded-lg border border-gray-200 bg-white shadow-sm"
        >
          <summary class="cursor-pointer list-none px-4 py-3 hover:bg-gray-50">
            <div class="flex flex-wrap items-center justify-between gap-2">
              <span class="font-bold text-gray-800 text-sm">#{{ index + 1 }} - Cluster {{ cluster.cluster_id }}</span>
              <div class="flex items-center gap-2">
                <span
                  v-if="activeRanking === 'average'"
                  class="rounded border border-emerald-200 bg-emerald-50 px-2.5 py-0.5 text-xs font-semibold text-emerald-700"
                >
                  Média: {{ cluster.engajamento_medio.toFixed(2) }}
                </span>
                <span
                  v-else
                  class="rounded border border-blue-200 bg-blue-50 px-2.5 py-0.5 text-xs font-semibold text-blue-700"
                >
                  Total: {{ (cluster.engajamento_somado || 0).toFixed(2) }}
                </span>
                <span class="text-xs text-gray-500">{{ cluster.total_posts }} posts</span>
              </div>
            </div>
            <div class="mt-2 flex flex-wrap gap-1.5">
              <span
                v-for="keyword in cluster.palavras_chave"
                :key="keyword"
                class="rounded-full bg-blue-50 px-2 py-0.5 text-[11px] font-medium text-blue-700"
              >
                {{ keyword }}
              </span>
            </div>
          </summary>
          <div class="border-t border-gray-100 px-4 py-3">
            <ul class="space-y-2">
              <li v-for="post in cluster.posts" :key="post.id" class="text-xs">
                <a :href="post.post_url" target="_blank" class="font-medium text-blue-600 hover:underline">
                  {{ formatLegenda(post.legenda_post, 110) }}
                </a>
                <span class="ml-1 text-gray-500">{{ post.source_profile }} · {{ Number(post.score_engajamento).toFixed(2) }}</span>
              </li>
            </ul>
          </div>
        </details>
      </div>
    </section>
  </div>

  <div v-else class="max-w-7xl mx-auto mt-10 p-4 bg-white rounded-xl shadow-lg">
    <h2 class="text-2xl font-medium text-center text-gray-800 mb-8">
      Ranking de Engajamento geral
    </h2>

    <div v-if="!loading" class="mb-6 flex flex-wrap items-end justify-center gap-4 rounded-lg bg-gray-50 p-4">
      <label class="flex flex-col gap-1 text-left text-sm font-semibold text-gray-700">
        De
        <input v-model="selectedStartDate" :min="availableStartDate" :max="availableEndDate" type="date" class="rounded-md border border-gray-300 px-3 py-2 font-normal focus:border-blue-500 focus:outline-none" />
      </label>

      <label class="flex flex-col gap-1 text-left text-sm font-semibold text-gray-700">
        Até
        <input v-model="selectedEndDate" :min="availableStartDate" :max="availableEndDate" type="date" class="rounded-md border border-gray-300 px-3 py-2 font-normal focus:border-blue-500 focus:outline-none" />
      </label>

      <button v-if="selectedStartDate || selectedEndDate" @click="clearDateFilter" type="button" class="rounded-md border border-gray-300 px-4 py-2 text-sm font-semibold text-gray-700 hover:bg-white">
        Limpar período
      </button>
    </div>

    <p v-if="!loading && selectedStartDate && selectedEndDate && selectedStartDate > selectedEndDate" class="mb-4 text-center text-red-600">
      A data inicial deve ser anterior à data final.
    </p>

    <p v-else-if="!loading" class="mb-4 text-center text-gray-600">
      <span v-if="selectedStartDate || selectedEndDate">
        {{ filteredRanking.length }} post{{ filteredRanking.length === 1 ? '' : 's' }} encontrado{{ filteredRanking.length === 1 ? '' : 's' }} no período selecionado.
      </span>
      <span v-else-if="availableStartDate && availableEndDate">
        Dados disponíveis de {{ new Date(`${availableStartDate}T00:00:00`).toLocaleDateString('pt-BR') }} a {{ new Date(`${availableEndDate}T00:00:00`).toLocaleDateString('pt-BR') }}.
      </span>
      <span v-else>Período: -</span>
    </p>

    <p v-if="loading" class="text-center text-gray-500">
      Carregando dados...
    </p>

    <div v-else class="overflow-x-auto">
      <table class="min-w-full border border-gray-200 rounded-lg overflow-hidden">
        <thead class="bg-gray-100 text-gray-700 text-sm uppercase">
          <tr>
            <th class="px-4 py-3 text-left"></th>
            <th class="px-4 py-3 text-left">Perfil</th>
            <th class="px-4 py-3 text-left">Curtidas</th>
            <th class="px-4 py-3 text-left">Comentários</th>
            <th class="px-4 py-3 text-left">Seguidores</th>
            <th class="px-4 py-3 text-left">Engajamento</th>
            <th class="px-4 py-3 text-left">Data</th>
            <th class="px-4 py-3 text-left">Legenda</th>
            <th class="px-4 py-3 text-left">Post</th>
          </tr>
        </thead>

        <tbody class="divide-y divide-gray-200">
          <tr v-for="(item, index) in filteredRanking" :key="item.post_url || `${item.source_profile}-${index}`" class="hover:bg-gray-50 transition">
            <td class="px-4 py-3 font-semibold text-gray-600">
              {{ item.position }}
            </td>

            <td class="px-4 py-3 font-medium text-gray-800">
              {{ item.source_profile }}
            </td>

            <td class="px-4 py-3">
              {{ item.likes }}
            </td>

            <td class="px-4 py-3">
              {{ item.comments_count }}
            </td>

            <td class="px-4 py-3">
              {{ Number(item.followers).toLocaleString('pt-BR') }}
            </td>

            <td class="px-4 py-3 font-semibold text-green-600">
              {{ item.score_engajamento.toFixed(2) }}
            </td>

            <td class="px-4 py-3">
              {{ item.published_at ? new Date(item.published_at).toLocaleDateString('pt-BR') : '-' }}
            </td>

            <td class="px-4 py-3 max-w-lg">
              <div class="text-sm text-gray-700 max-w-xs" :class="expanded[index]
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

            <td class="px-4 py-3 whitespace-nowrap">
              <a :href="item.post_url" target="_blank" class="text-blue-500 hover:underline font-medium">
                Ver Post
              </a>
            </td>
          </tr>
        </tbody>
      </table>

      <p v-if="!filteredRanking.length && !loading && !(selectedStartDate && selectedEndDate && selectedStartDate > selectedEndDate)" class="py-8 text-center text-gray-500">
        Nenhum post encontrado no período selecionado.
      </p>
    </div>
  </div>
</template>