<script setup>
import { ref, onMounted, provide } from 'vue'
import { useAgents } from './composables/useAgents'
import { useEvents } from './composables/useEvents'
import RelationsGraph from './components/RelationsGraph.vue'
import AgentInspector from './components/AgentInspector.vue'
import EventFeed from './components/EventFeed.vue'
import ControlPanel from './components/ControlPanel.vue'

const { agents, selectedAgent, selectAgent, fetchAgents } = useAgents()
const { events, fetchEvents, addEvent } = useEvents()
const timeSpeed = ref(1.0)

provide('agents', agents)

onMounted(async () => {
  await fetchAgents()
  await fetchEvents()
})

const handleAgentClick = (agentId) => {
  selectAgent(agentId)
}

const handleAddEvent = async (eventData) => {
  await addEvent(eventData)
}

const handleSendMessage = async (messageData) => {
  console.log('Отправить сообщение:', messageData)
  await addEvent({
    type: 'user_event',
    content: `Сообщение для агента ${messageData.agentId}: ${messageData.message}`,
    agentIds: [messageData.agentId],
    mood: 'neutral'
  })
}

const handleUpdateTimeSpeed = (speed) => {
  timeSpeed.value = speed
  console.log('Скорость времени:', speed)
}
</script>

<template>
  <div class="app">
    <header class="header">
      <h1>Виртуальный мир</h1>
      <p class="subtitle">Симулятор живых существ с памятью и эмоциями</p>
    </header>

    <div class="main-container">
      <!-- Верхняя часть: Граф отношений (главный элемент) -->
      <div class="top-section">
        <RelationsGraph
          :agents="agents"
          @agent-click="handleAgentClick"
        />
      </div>

      <div class="bottom-section">
        <div class="left-column">
          <EventFeed :events="events" />
        </div>

        <div class="center-column">
          <ControlPanel 
            :time-speed="timeSpeed"
            @add-event="handleAddEvent"
            @send-message="handleSendMessage"
            @update-time-speed="handleUpdateTimeSpeed"
          />
        </div>

        <div class="right-column">
          <AgentInspector
            v-if="selectedAgent"
            :agent="selectedAgent"
          />
          <div v-else class="placeholder">
            Выберите агента на графе выше
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped>
.app {
  min-height: 100vh;
  width: 100%;
  background: #f8fafc;
  display: flex;
  flex-direction: column;
}

.header {
  background: #ffffff;
  border-bottom: 1px solid #e2e8f0;
  padding: 24px 0;
  text-align: center;
  color: #1e293b;
  width: 100%;
  flex-shrink: 0;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.05);
}

.header h1 {
  font-size: 28px;
  margin-bottom: 8px;
  font-weight: 700;
  color: #0f172a;
}

.subtitle {
  font-size: 15px;
  color: #64748b;
  font-weight: 400;
}

.main-container {
  flex: 1;
  display: flex;
  flex-direction: column;
  padding: 24px;
  gap: 24px;
  width: 100%;
  max-width: 1600px;
  margin: 0 auto;
}

.top-section {
  flex-shrink: 0;
  width: 100%;
  max-height: 400px;
}

.bottom-section {
  flex: 1;
  display: grid;
  grid-template-columns: 1fr 1fr 1fr;
  gap: 15px;
  align-items: start;
  width: 100%;
  min-height: 400px;
}

.left-column,
.center-column,
.right-column {
  display: flex;
  flex-direction: column;
  width: 100%;
  min-height: 400px;
}

.agents-list {
  background: rgba(255, 255, 255, 0.95);
  border-radius: 12px;
  padding: 20px;
  margin: 0 20px 20px;
  box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
}

.agents-list h2 {
  margin-bottom: 15px;
  color: #1e293b;
}

.agents-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(200px, 1fr));
  gap: 15px;
}

.agent-card {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 10px;
  padding: 15px;
  background: #f8fafc;
  border-radius: 8px;
  cursor: pointer;
  transition: all 0.2s;
  text-align: center;
}

.agent-card:hover {
  background: #e2e8f0;
  transform: translateY(-2px);
  box-shadow: 0 4px 8px rgba(0, 0, 0, 0.1);
}

.avatar {
  font-size: 40px;
}

.info h3 {
  margin: 0;
  font-size: 16px;
  color: #334155;
}

.info p {
  margin: 5px 0 0;
  font-size: 12px;
  color: #64748b;
}

.placeholder {
  background: #ffffff;
  border: 1px solid #e2e8f0;
  border-radius: 12px;
  padding: 40px;
  text-align: center;
  color: #94a3b8;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.05);
}

@media (max-width: 1200px) {
  .bottom-section {
    grid-template-columns: 1fr 1fr;
    gap: 15px;
  }
  
  .right-column {
    grid-column: 1 / -1;
  }
  
  .header h1 {
    font-size: 24px;
  }
  
  .subtitle {
    font-size: 13px;
  }
  
  .main-container {
    padding: 12px;
  }
}

@media (max-width: 768px) {
  .main-container {
    padding: 10px;
    gap: 10px;
  }
  
  .header {
    padding: 15px 0;
  }
  
  .header h1 {
    font-size: 20px;
  }
  
  .subtitle {
    font-size: 12px;
  }
  
  .bottom-section {
    grid-template-columns: 1fr;
    gap: 10px;
  }
  
  .top-section {
    margin-bottom: 10px;
  }
  
  .left-column,
  .center-column,
  .right-column {
    min-height: 300px;
  }
}

@media (max-width: 480px) {
  .main-container {
    padding: 8px;
    gap: 8px;
  }
  
  .header {
    padding: 12px 0;
  }
  
  .header h1 {
    font-size: 18px;
  }
  
  .subtitle {
    font-size: 11px;
  }
  
  .left-column,
  .center-column,
  .right-column {
    min-height: 250px;
  }
}
</style>
