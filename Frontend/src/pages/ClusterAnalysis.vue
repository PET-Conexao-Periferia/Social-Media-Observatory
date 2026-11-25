<script setup>
import { computed, onMounted, ref } from 'vue'
import { formatLegenda } from '@/utils/legenda.js'

const elbow = ref([])
const selectedK = ref(27)
const suggestedK = ref(null)
const clusters = ref([])
const clusterLoading = ref(false)
const clusterError = ref('')
const elbowReady = ref(false)
const clusterPeriodMode = ref('last7')
const clusterStartDate = ref('')
const clusterEndDate = ref('')
const activeRanking = ref('average')
const CLUSTER_STORAGE_KEY = 'observatorio:last-cluster-analysis-v2'

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

const updateClusterPeriod = () => {
  if (clusterPeriodMode.value !== 'custom') {
    clusterStartDate.value = ''
    clusterEndDate.value = ''
  }
  restoreClusterAnalysis()
}

const saveClusterAnalysis = () => {
  try {
    const savedAnalyses = loadSavedAnalyses()
    savedAnalyses[getClusterPeriodKey()] = {
      elbow: elbow.value,
      suggestedK: suggestedK.value,
      selectedK: selectedK.value,
      clusters: clusters.value,
      clusterPeriodMode: clusterPeriodMode.value,
      clusterStartDate: clusterStartDate.value,
      clusterEndDate: clusterEndDate.value,
    }
    localStorage.setItem(CLUSTER_STORAGE_KEY, JSON.stringify(savedAnalyses))
  } catch (error) {
    console.error('N\u00e3o foi poss\u00edvel salvar a \u00faltima an\u00e1lise de clusters:', error)
  }
}

const loadSavedAnalyses = () => {
  const saved = JSON.parse(localStorage.getItem(CLUSTER_STORAGE_KEY) || '{}')
  if (Array.isArray(saved.elbow)) {
    return { last7: saved }
  }
  return saved
}

const getClusterPeriodKey = () => {
  if (clusterPeriodMode.value !== 'custom') return clusterPeriodMode.value
  return `custom:${clusterStartDate.value || ''}:${clusterEndDate.value || ''}`
}

const clearClusterAnalysis = () => {
  elbowReady.value = false
  elbow.value = []
  suggestedK.value = null
  clusters.value = []
}

const applyClusterAnalysis = (analysis) => {
  elbow.value = Array.isArray(analysis.elbow) ? analysis.elbow : []
  suggestedK.value = analysis.k_sugerido || analysis.suggestedK || null
  selectedK.value = analysis.k_escolhido || analysis.selectedK || analysis.suggestedK || 27
  clusters.value = Array.isArray(analysis.clusters) ? analysis.clusters : []
  if (analysis.period_mode || analysis.clusterPeriodMode) {
    clusterPeriodMode.value = analysis.period_mode || analysis.clusterPeriodMode
  }
  if (analysis.periodo) {
    clusterStartDate.value = analysis.periodo.start_date || ''
    clusterEndDate.value = analysis.periodo.end_date || ''
  } else {
    clusterStartDate.value = analysis.clusterStartDate || ''
    clusterEndDate.value = analysis.clusterEndDate || ''
  }
  elbowReady.value = elbow.value.length > 0
}

const restoreClusterAnalysis = () => {
  try {
    const analysis = loadSavedAnalyses()[getClusterPeriodKey()]
    if (!analysis || !Array.isArray(analysis.elbow) || !analysis.elbow.length) {
      clearClusterAnalysis()
      return false
    }
    applyClusterAnalysis(analysis)
    return true
  } catch (error) {
    console.error('N\u00e3o foi poss\u00edvel restaurar a \u00faltima an\u00e1lise de clusters:', error)
    clearClusterAnalysis()
    return false
  }
}

const restoreLatestClusterAnalysis = async () => {
  try {
    const response = await fetch('/api/clusters/latest')
    if (response.ok) {
      applyClusterAnalysis(await response.json())
      return true
    }
    if (response.status !== 404) {
      const result = await response.json()
      throw new Error(result.detail || 'N\u00e3o foi poss\u00edvel carregar a \u00faltima clusteriza\u00e7\u00e3o.')
    }
  } catch (error) {
    console.error('N\u00e3o foi poss\u00edvel carregar a \u00faltima clusteriza\u00e7\u00e3o persistida:', error)
  }
  return restoreClusterAnalysis()
}

const clusterPeriodQuery = () => {
  const params = new URLSearchParams({ period_mode: clusterPeriodMode.value })
  if (clusterPeriodMode.value === 'custom' && clusterStartDate.value) {
    params.set('start_date', clusterStartDate.value)
  }
  if (clusterPeriodMode.value === 'custom' && clusterEndDate.value) {
    params.set('end_date', clusterEndDate.value)
  }
  return params.toString()
}

const updateCustomClusterDate = () => {
  if (clusterPeriodMode.value !== 'custom') return
  restoreClusterAnalysis()
}

onMounted(async () => {
  await restoreLatestClusterAnalysis()
})

const calculateElbow = async () => {
  clusterLoading.value = true
  clusterError.value = ''
  try {
    const query = clusterPeriodQuery()
    const response = await fetch(`/api/clusters/elbow${query ? `?${query}` : ''}`)
    if (!response.ok) throw new Error((await response.json()).detail || 'N\u00e3o foi poss\u00edvel calcular o cotovelo.')
    const result = await response.json()
    elbow.value = result.elbow
    clusters.value = []
    suggestedK.value = result.k_sugerido
    selectedK.value = result.k_sugerido
    if (result.periodo) {
      clusterStartDate.value = result.periodo.start_date || ''
      clusterEndDate.value = result.periodo.end_date || ''
    }
    elbowReady.value = true
    saveClusterAnalysis()
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
        period_mode: clusterPeriodMode.value,
        start_date: clusterPeriodMode.value === 'custom' ? clusterStartDate.value || null : null,
        end_date: clusterPeriodMode.value === 'custom' ? clusterEndDate.value || null : null,
      }),
    })
    if (!response.ok) throw new Error((await response.json()).detail || 'N\u00e3o foi poss\u00edvel agrupar os posts.')
    const result = await response.json()
    clusters.value = result.clusters
    saveClusterAnalysis()
  } catch (error) {
    clusterError.value = error.message
  } finally {
    clusterLoading.value = false
  }
}

</script>

<template>
  <div class="max-w-7xl mx-auto mt-10 p-6 bg-white rounded-xl shadow-lg">
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
      <div class="flex flex-wrap items-end gap-5">
        <label class="flex items-center gap-2 text-sm font-medium text-gray-700">
          <input v-model="clusterPeriodMode" @change="updateClusterPeriod" value="all" type="radio" name="cluster-period" class="order-first h-4 w-4 accent-blue-600" />
          <span>Todos os posts</span>
        </label>
        <label class="flex items-center gap-2 text-sm font-medium text-gray-700">
          <input v-model="clusterPeriodMode" @change="updateClusterPeriod" value="last7" type="radio" name="cluster-period" class="order-first h-4 w-4 accent-blue-600" />
          <span>Últimos 7 dias</span>
        </label>
        <label class="flex items-center gap-2 text-sm font-medium text-gray-700">
          <input v-model="clusterPeriodMode" @change="updateClusterPeriod" value="custom" type="radio" name="cluster-period" class="order-first h-4 w-4 accent-blue-600" />
          <span>Personalizado</span>
        </label>
        <label class="flex items-center gap-2 text-sm font-semibold text-gray-700">
          De
          <input v-model="clusterStartDate" @input="updateCustomClusterDate" :disabled="clusterPeriodMode !== 'custom'" type="date" class="rounded-md border border-gray-300 bg-white px-3 py-2 font-normal disabled:cursor-not-allowed disabled:bg-gray-100" />
        </label>
        <label class="flex items-center gap-2 text-sm font-semibold text-gray-700">
          Até
          <input v-model="clusterEndDate" @input="updateCustomClusterDate" :disabled="clusterPeriodMode !== 'custom'" type="date" class="rounded-md border border-gray-300 bg-white px-3 py-2 font-normal disabled:cursor-not-allowed disabled:bg-gray-100" />
        </label>
      </div>
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

    <!-- CONTROLES DE CLUSTERIZAÇÃO -->
    <div v-if="elbowReady && chartConfig" class="mb-8 flex flex-wrap items-end gap-4 border-b border-gray-100 pb-6">
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
</template>
