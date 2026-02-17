<script setup>
import { computed } from 'vue'

const props = defineProps({
  agents: {
    type: Array,
    default: () => []
  }
})

const emit = defineEmits(['agent-click'])

const graphData = computed(() => {
  const nodes = props.agents.map(agent => ({
    id: agent.id,
    name: agent.name,
    avatar: agent.avatar,
    mood: agent.mood
  }))

  const links = []
  props.agents.forEach(agent => {
    if (agent.relationships) {
      agent.relationships.forEach(rel => {
        links.push({
          source: agent.id,
          target: rel.agentId,
          sentiment: rel.sentiment,
          type: rel.type
        })
      })
    }
  })

  return { nodes, links }
})

const getRelationshipColor = (sentiment) => {
  if (sentiment > 0.3) return '#10b981'
  if (sentiment > 0) return '#3b82f6'
  if (sentiment > -0.3) return '#6b7280'
  return '#ef4444'
}

const getRelationshipWidth = (sentiment) => {
  return Math.abs(sentiment) * 1.5 + 1
}

const getNodePosition = (nodeId) => {
  const index = graphData.value.nodes.findIndex(n => n.id === nodeId)
  const total = graphData.value.nodes.length
  
  if (total === 0) return { x: 0, y: 0 }
  if (total === 1) return { x: 50, y: 50 }
  if (total === 2) return index === 0 ? { x: 30, y: 50 } : { x: 70, y: 50 }
  
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
    <div class="graph-container" v-if="graphData.nodes.length > 0">
      <svg class="graph-svg" viewBox="0 0 100 100" preserveAspectRatio="xMidYMid meet">
        <g class="links">
          <line
            v-for="(link, index) in graphData.links"
            :key="`link-${index}`"
            :x1="getNodePosition(link.source).x"
            :y1="getNodePosition(link.source).y"
            :x2="getNodePosition(link.target).x"
            :y2="getNodePosition(link.target).y"
            :stroke="getRelationshipColor(link.sentiment)"
            :stroke-width="getRelationshipWidth(link.sentiment)"
            :opacity="0.4"
            class="link-line"
          />
        </g>

        <g class="nodes">
          <g
            v-for="(node, index) in graphData.nodes"
            :key="node.id"
            :transform="`translate(${getNodePosition(node.id).x}, ${getNodePosition(node.id).y})`"
            class="node-group"
            @click="emit('agent-click', node.id)"
          >
            <circle
              :r="8"
              :fill="node.mood?.color || '#667eea'"
              stroke="#fff"
              stroke-width="2.5"
              class="node-circle"
            />
            <text
              text-anchor="middle"
              dy="3"
              font-size="10"
              class="node-avatar"
            >
              {{ node.avatar }}
            </text>
            <text
              text-anchor="middle"
              dy="16"
              font-size="3.5"
              font-weight="600"
              fill="#334155"
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
      <p>Загрузка агентов...</p>
    </div>
  </div>
</template>

<style scoped>
.relations-graph {
  background: transparent;
  border-radius: 0;
  padding: 0;
  box-shadow: none;
  width: 100%;
}

.relations-graph h2 {
  margin-bottom: 20px;
  font-size: 20px;
  font-weight: 600;
  color: #1e293b;
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
  transition: opacity 0.2s ease;
}

.link-line:hover {
  opacity: 0.7;
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
  color: #64748b;
}

.legend-line {
  width: 30px;
  height: 3px;
  border-radius: 2px;
}

.empty-state {
  text-align: center;
  padding: 40px;
  color: #94a3b8;
}

@media (max-width: 768px) {
  .relations-graph h2 {
    font-size: 18px;
    margin-bottom: 12px;
  }
  
  .graph-container {
    height: 250px;
    padding: 10px;
  }
  
  .graph-svg {
    height: 220px;
  }
  
  .legend {
    flex-wrap: wrap;
    gap: 10px;
    margin-top: 10px;
    padding-top: 10px;
  }
  
  .legend-item {
    font-size: 11px;
  }
}

@media (max-width: 480px) {
  .relations-graph {
    padding: 12px;
  }
  
  .relations-graph h2 {
    font-size: 16px;
    margin-bottom: 10px;
  }
  
  .graph-container {
    height: 220px;
    padding: 8px;
  }
  
  .graph-svg {
    height: 190px;
  }
  
  .legend {
    margin-top: 8px;
    padding-top: 8px;
  }
}
</style>
