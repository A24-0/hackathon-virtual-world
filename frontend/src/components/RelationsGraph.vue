<script setup>
import { computed, ref, watch, onMounted, onUnmounted } from 'vue'
import { api } from '../utils/api'

const props = defineProps({
  agents: {
    type: Array,
    default: () => []
  }
})

const emit = defineEmits(['agent-click'])

const graphDataFromAPI = ref(null)
const loading = ref(false)

const moodColors = {
  'happy': '#10b981',
  'sad': '#3b82f6',
  'angry': '#ef4444',
  'neutral': '#6b7280',
  'excited': '#f59e0b',
  'anxious': '#f97316',
  'bored': '#94a3b8'
}

const fetchGraph = async () => {
  try {
    loading.value = true
    const response = await api.get('/api/v1/system/agents/graph/relationships', {
      params: { _t: Date.now() }
    })
    // Создаем полностью новый объект для принудительного обновления реактивности
    const newData = {
      nodes: [...(response.data.nodes || [])],
      edges: [...(response.data.edges || [])]
    }
    // Принудительно обновляем, создавая новый объект через JSON для глубокого копирования
    graphDataFromAPI.value = JSON.parse(JSON.stringify(newData))
  } catch (error) {
    console.error('Ошибка загрузки графа:', error)
    graphDataFromAPI.value = null
  } finally {
    loading.value = false
  }
}

const graphData = computed(() => {
  try {
    if (graphDataFromAPI.value) {
      const nodes = (graphDataFromAPI.value.nodes || []).map(node => ({
        id: node.id,
        name: node.name,
        avatar: node.avatar_url && node.avatar_url.length <= 4 ? node.avatar_url : node.name.charAt(0),
        mood: {
          current: node.mood || 'neutral',
          color: moodColors[node.mood] || '#6b7280'
        }
      }))

      const links = (graphDataFromAPI.value.edges || [])
        .map(edge => ({
          source: edge.source,
          target: edge.target,
          sentiment: edge.sympathy || 0,
          type: edge.description || ''
        }))
        .filter(link => link.source && link.target && typeof link.sentiment === 'number')

      return { nodes: nodes || [], links: links || [] }
    }

    const nodes = (props.agents || []).map(agent => ({
    id: agent.id,
    name: agent.name,
      avatar: agent.avatar && agent.avatar.length <= 4 ? agent.avatar : agent.name.charAt(0),
      mood: agent.mood || { current: 'neutral', color: '#6b7280' }
  }))

  const links = []
    (props.agents || []).forEach(agent => {
      if (agent && agent.relationships) {
      agent.relationships.forEach(rel => {
          if (rel && rel.agentId) {
        links.push({
          source: agent.id,
          target: rel.agentId,
              sentiment: typeof rel.sentiment === 'number' ? rel.sentiment : (typeof rel.sympathy === 'number' ? rel.sympathy : 0),
              type: rel.type || ''
        })
          }
      })
    }
  })

    return { nodes: nodes || [], links: links.filter(link => link.source && link.target && typeof link.sentiment === 'number') || [] }
  } catch (error) {
    console.error('Ошибка в graphData computed:', error)
    return { nodes: [], links: [] }
  }
})

watch(() => props.agents, () => {
  fetchGraph()
}, { deep: true, immediate: false })

// Также следим за изменениями в данных агентов (настроение, отношения)
watch(() => props.agents.map(a => ({
  id: a.id,
  mood: a.mood?.current,
  relationships: a.relationships?.map(r => ({
    agentId: r.agentId,
    sentiment: r.sentiment
  }))
})), () => {
  fetchGraph()
}, { deep: true, immediate: false })

let graphUpdateInterval = null
onMounted(() => {
  fetchGraph()
  // Обновляем граф каждые 500ms для максимально быстрой реакции на изменения
  graphUpdateInterval = setInterval(() => {
    fetchGraph()
  }, 500)
})

onUnmounted(() => {
  if (graphUpdateInterval) {
    clearInterval(graphUpdateInterval)
  }
})

defineExpose({
  refresh: fetchGraph
})

const getRelationshipColor = (sentiment) => {
  const s = typeof sentiment === 'number' ? sentiment : 0
  if (s < -0.5) return 'transparent' // Скрываем очень враждебные связи
  if (s > 0.3) return '#10b981' // Дружба
  if (s > 0) return '#3b82f6' // Положительные
  if (s > -0.3) return '#6b7280' // Нейтральные
  return '#ef4444' // Враждебные
}

const getRelationshipWidth = (sentiment) => {
  const s = typeof sentiment === 'number' ? sentiment : 0
  if (s < -0.5) return 0 // Ширина 0 для скрытых связей
  return Math.abs(s) * 1.5 + 1
}

const getNodePosition = (nodeId) => {
  if (!nodeId || !graphData.value || !graphData.value.nodes) {
    return { x: 50, y: 50 }
  }
  const index = graphData.value.nodes.findIndex(n => n && n.id === nodeId)
  const total = graphData.value.nodes.length
  
  if (total === 0) return { x: 50, y: 50 }
  if (total === 1) return { x: 50, y: 50 }
  if (total === 2) return index === 0 ? { x: 30, y: 50 } : { x: 70, y: 50 }
  
  if (index === -1) return { x: 50, y: 50 }
  
  const angle = (index / total) * 2 * Math.PI - Math.PI / 2
  const radius = 25
  return {
    x: 50 + radius * Math.cos(angle),
    y: 50 + radius * Math.sin(angle)
  }
}
</script>

<template>
  <div class="relations-graph">
    <h2>Граф отношений</h2>
    <div class="graph-container" v-if="graphData && graphData.nodes && graphData.nodes.length > 0">
      <svg class="graph-svg" viewBox="0 0 100 100" preserveAspectRatio="xMidYMid meet">
        <g class="links">
          <line
            v-for="(link, index) in (graphData.links || []).filter(l => l && typeof l.sentiment === 'number')"
            :key="`link-${link.source}-${link.target}-${(link.sentiment || 0).toFixed(3)}-${index}`"
            :x1="getNodePosition(link.source).x"
            :y1="getNodePosition(link.source).y"
            :x2="getNodePosition(link.target).x"
            :y2="getNodePosition(link.target).y"
            :stroke="getRelationshipColor(link.sentiment)"
            :stroke-width="getRelationshipWidth(link.sentiment)"
            :opacity="link.sentiment < -0.5 ? 0 : (0.4 + Math.abs(link.sentiment || 0) * 0.3)"
            class="link-line"
          />
        </g>

        <g class="nodes">
          <g
            v-for="(node, index) in (graphData.nodes || [])"
            :key="`node-${node.id}-${node.mood?.current || 'neutral'}-${node.mood?.color || ''}`"
            :transform="`translate(${getNodePosition(node.id).x}, ${getNodePosition(node.id).y})`"
            class="node-group"
            @click="emit('agent-click', node.id)"
          >
            <circle
              :r="8"
              :fill="(node.mood && node.mood.color) || '#667eea'"
              stroke="#fff"
              stroke-width="2.5"
              class="node-circle"
            />
            <text
              text-anchor="middle"
              dy="3"
              font-size="10"
              fill="#1e293b"
              class="node-avatar"
            >
              {{ node.avatar }}
            </text>
            <text
              text-anchor="middle"
              dy="16"
              font-size="3.5"
              font-weight="600"
              fill="#1e293b"
              class="node-name"
            >
              {{ node.name }}
            </text>
          </g>
        </g>
      </svg>

      <div class="legend">
        <div class="legend-item">
          <div class="legend-line" style="background: #10b981;"></div>
          <span>Дружба</span>
        </div>
        <div class="legend-item">
          <div class="legend-line" style="background: #3b82f6;"></div>
          <span>Нейтрально</span>
        </div>
        <div class="legend-item">
          <div class="legend-line" style="background: #ef4444;"></div>
          <span>Враждебность</span>
        </div>
      </div>
    </div>
    <div v-else class="empty-state">
      <p v-if="loading">Загрузка графа...</p>
      <p v-else>Нет данных для отображения</p>
    </div>
  </div>
</template>

<style scoped>
.relations-graph {
  background: #ffffff;
  border: 1px solid #e2e8f0;
  border-radius: 16px;
  padding: 24px;
  box-shadow: 0 4px 6px rgba(0, 0, 0, 0.07), 0 1px 3px rgba(0, 0, 0, 0.05);
  width: 100%;
  min-height: 300px;
  display: flex;
  flex-direction: column;
}

.relations-graph h2 {
  margin-bottom: 20px;
  font-size: 20px;
  font-weight: 600;
  color: #1e293b;
  display: flex;
  align-items: center;
  gap: 8px;
}


.graph-container {
  position: relative;
  width: 100%;
  height: 350px;
  background: #ffffff;
  border: 1px solid #e2e8f0;
  border-radius: 12px;
  padding: 20px;
  overflow: hidden;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.05);
}

.graph-svg {
  width: 100%;
  height: 320px;
  display: block;
}

.link-line {
  transition: stroke 0.5s cubic-bezier(0.4, 0, 0.2, 1), 
              stroke-width 0.5s cubic-bezier(0.4, 0, 0.2, 1), 
              opacity 0.5s cubic-bezier(0.4, 0, 0.2, 1);
  pointer-events: none;
}

.node-group {
  cursor: pointer;
}

.node-group:hover .node-circle {
  r: 9;
  filter: drop-shadow(0 2px 4px rgba(0, 0, 0, 0.2));
}

.node-circle {
  filter: drop-shadow(0 2px 4px rgba(0, 0, 0, 0.1));
  transition: r 0.2s ease, filter 0.2s ease;
}

.node-avatar {
  pointer-events: none;
  user-select: none;
}

.node-name {
  pointer-events: none;
  user-select: none;
}

.legend {
  display: flex;
  justify-content: center;
  gap: 15px;
  margin-top: 10px;
  padding-top: 10px;
  border-top: 1px solid #e2e8f0;
}

.legend-item {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 12px;
  color: #1e293b;
  font-weight: 500;
}

.legend-line {
  width: 30px;
  height: 3px;
  border-radius: 2px;
}

.empty-state {
  text-align: center;
  padding: 40px;
  color: #475569;
  font-size: 14px;
  background: #ffffff;
  border-radius: 12px;
  border: 1px solid #e2e8f0;
  min-height: 200px;
  display: flex;
  align-items: center;
  justify-content: center;
}

@media (max-width: 768px) {
  .relations-graph h2 { font-size: 18px; margin-bottom: 12px; }
  .graph-container { height: 250px; padding: 10px; }
  .graph-svg { height: 220px; }
  .legend { flex-wrap: wrap; gap: 10px; }
  .legend-item { font-size: 11px; }
}

@media (max-width: 480px) {
  .relations-graph { padding: 12px; }
  .relations-graph h2 { font-size: 16px; margin-bottom: 10px; }
  .graph-container { height: 220px; padding: 8px; }
  .graph-svg { height: 190px; }
}
</style>
