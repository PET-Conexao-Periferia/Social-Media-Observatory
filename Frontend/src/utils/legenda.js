export const formatLegenda = (texto, limite = 150) => {
  if (!texto) return '-'

  let resultado = texto

  if (resultado.includes(':')) {
    resultado = resultado.split(':').slice(1).join(':').trim()
  }

  const match = resultado.match(/["\u201c](.*?)[\u201d"]/)

  if (match) {
    resultado = match[1]
  }

  resultado = resultado.replace(/\n/g, ' ')

  if (resultado.length > limite) {
    resultado = resultado.substring(0, limite) + '...'
  }

  return resultado
}

export const getLegendaCompleta = (texto) => {
  if (!texto) return '-'

  let resultado = texto

  if (resultado.includes(':')) {
    resultado = resultado.split(':').slice(1).join(':').trim()
  }

  const match = resultado.match(/["\u201c](.*?)[\u201d"]/)

  if (match) {
    resultado = match[1]
  }

  return resultado.replace(/\n/g, ' ')
}
