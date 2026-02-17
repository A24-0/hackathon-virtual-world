<script setup>
import { onMounted } from 'vue'
import { useAgents } from './composables/useAgents'
import RelationsGraph from './components/RelationsGraph.vue'
import AgentInspector from './components/AgentInspector.vue'

const { agents, selectedAgent, selectAgent, fetchAgents } = useAgents()

// загружаем агентов при старте
onMounted(async () => {
  await fetchAgents()
})

// клик на агента в графе
const handleAgentClick = (agentId) => {
  selectAgent(agentId)
}
</script>

<template>
  <div class="app">
    <h1>Виртуальный мир</h1>
    
    <!-- список агентов для теста -->
    <div class="agents-list">
      <h2>Агенты ({{ agents.length }})</h2>
      <div v-if="agents.length === 0">
        Загрузка агентов...
      </div>
      <div v-else>
        <div 
          v-for="agent in agents" 
          :key="agent.id"
          class="agent-card"
          @click="handleAgentClick(agent.id)"
        >
          <div class="avatar">{{ agent.avatar }}</div>
          <div class="info">
            <h3>{{ agent.name }}</h3>
            <p>Настроение: {{ agent.mood?.current || 'неизвестно' }}</p>
          </div>
        </div>
      </div>
    </div>

    <!-- Граф отношений -->
    <RelationsGraph
      :agents="agents"
      @agent-click="handleAgentClick"
    />

    <!-- Инспектор агента -->
    <AgentInspector
      v-if="selectedAgent"
      :agent="selectedAgent"
    />
    <div v-else class="placeholder">
      Выберите агента из списка выше
    </div>
  </div>
</template>

<style scoped>
  .app {
    padding: 20px;
    max-width: 1200px;
    margin: 0 auto;
  }

  .agents-list {
    margin-bottom: 30px;
  }

  .agent-card {
    display: flex;
    align-items: center;
    gap: 15px;
    padding: 15px;
    background: #f8fafc;
    border-radius: 8px;
    margin-bottom: 10px;
    cursor: pointer;
    transition: background 0.2s;
  }

  .agent-card:hover {
    background: #e2e8f0;
  }

  .avatar {
    font-size: 40px;
  }

  .placeholder {
    text-align: center;
    padding: 40px;
    color: #94a3b8;
  }
</style>
