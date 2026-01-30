<script setup>
import { ref, onMounted } from 'vue'

const ranking = ref([])
const loading = ref(true)

onMounted(async () => {
  try {
    const response = await fetch('/dados_ranking/ranking_posts_geral.json')
    ranking.value = await response.json()
  } catch (error) {
    console.error('Erro ao carregar ranking:', error)
  } finally {
    loading.value = false
  }
})
</script>

<template>
  <nav class="w-full bg-white shadow-md px-6 py-4 flex items-center justify-between">
      <img
      src="@/assets/logo-pet-horizontal.svg"
      alt="Logo"
      class="h-16 ml-8 mt-3"
    />

    <h1 class="text-xl font-bold text-center text-gray-700">Observatorio das Midias Sociais do Litoral Norte - PE</h1>

    <ul class="flex gap-6 text-gray-700 font-medium mr-8">
      <li>
        <a href="/" class="hover:text-blue-600 transition">Sobre</a>
      </li>
    </ul>
  </nav>

  <div class="max-w-5xl mx-auto mt-10 p-6 bg-white rounded-xl shadow-lg">
    <h2 class="text-2xl font-medium text-center text-gray-800 mb-8">
      Ranking de Engajamento geral
    </h2>

    <p v-if="loading" class="text-center text-gray-500">
      Carregando dados...
    </p>

    <div v-else class="overflow-x-auto">
      <table class="min-w-full border border-gray-200 rounded-lg overflow-hidden">
        <thead class="bg-gray-100 text-gray-700 text-sm uppercase">
          <tr>
            <th class="px-4 py-3 text-left"></th>
            <th class="px-4 py-3 text-left">Perfil</th>
            <th class="px-4 py-3 text-left">Likes</th>
            <th class="px-4 py-3 text-left">Comentários</th>
            <th class="px-4 py-3 text-left">Seguidores</th>
            <th class="px-4 py-3 text-left">Engajamento</th>
            <th class="px-4 py-3 text-left">Post</th>
          </tr>
        </thead>

        <tbody class="divide-y divide-gray-200">
          <tr
            v-for="item in ranking"
            :key="item.source_profile"
            class="hover:bg-gray-50 transition"
          >
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
              {{ item.followers }}
            </td>

            <td class="px-4 py-3 font-semibold text-green-600">
              {{ item.score_engajamento.toFixed(2) }}
            </td>

            <td class="px-4 py-3">
              <a
                :href="item.post_url"
                target="_blank"
                class="text-blue-500 hover:underline font-medium"
              >
                Ver Post
              </a>
            </td>
          </tr>
        </tbody>
      </table>
    </div>
  </div>
</template>
