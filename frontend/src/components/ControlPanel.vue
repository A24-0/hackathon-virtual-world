<script setup>
import { ref, inject, computed } from 'vue'

const props = defineProps({
  timeSpeed: {
    type: Number,
    default: 1.0
  }
})

const emit = defineEmits(['add-event', 'send-message', 'update-time-speed'])

const newEventText = ref('')
const messageText = ref('')
const selectedAgentId = ref('')

const agentsRef = inject('agents', ref([]))
const agents = computed(() => agentsRef.value || [])

const handleAddEvent = () => {
  if (newEventText.value.trim()) {
    emit('add-event', {
      type: 'user_event',
      content: newEventText.value,
      timestamp: new Date()
    })
    newEventText.value = ''
  }
}

const handleSendMessage = () => {
  if (selectedAgentId.value && messageText.value.trim()) {
    emit('send-message', {
      agentId: selectedAgentId.value,
      message: messageText.value,
      timestamp: new Date()
    })
    messageText.value = ''
    selectedAgentId.value = ''
  }
}

const handleSpeedChange = (event) => {
  const speed = parseFloat(event.target.value)
  emit('update-time-speed', speed)
}
</script>

<template>
  <div class="card control-panel">
    <h2>Панель управления</h2>
    
    <!-- Добавить событие -->
    <div class="control-section">
      <h3>Добавить событие</h3>
      <input
        v-model="newEventText"
        type="text"
        class="input"
        placeholder="Например: Найден клад!"
        @keyup.enter="handleAddEvent"
      />
      <button 
        class="btn btn-primary" 
        @click="handleAddEvent"
        :disabled="!newEventText.trim()"
      >
        Добавить
      </button>
    </div>

    <!-- Отправить сообщение -->
    <div class="control-section">
      <h3>Отправить сообщение</h3>
      <select v-model="selectedAgentId" class="input">
        <option value="">Выберите агента</option>
        <option v-for="agent in agents" :key="agent.id" :value="agent.id">
          {{ agent.avatar }} {{ agent.name }}
        </option>
      </select>
      <input
        v-model="messageText"
        type="text"
        class="input"
        placeholder="Введите сообщение..."
        @keyup.enter="handleSendMessage"
      />
      <button 
        class="btn btn-primary" 
        @click="handleSendMessage"
        :disabled="!selectedAgentId || !messageText.trim()"
      >
        Отправить
      </button>
    </div>

    <!-- Скорость времени -->
    <div class="control-section">
      <h3>Скорость времени</h3>
      <div class="slider-container">
        <input
          type="range"
          min="0.1"
          max="5"
          step="0.1"
          :value="timeSpeed"
          @input="handleSpeedChange"
          class="slider"
        />
        <div class="slider-labels">
          <span>0.1x</span>
          <span class="current-speed">{{ timeSpeed.toFixed(1) }}x</span>
          <span>5x</span>
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped>
.control-panel {
  background: #ffffff;
  border: 1px solid #e2e8f0;
  border-radius: 12px;
  padding: 20px;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.05);
  min-height: 400px;
  display: flex;
  flex-direction: column;
}

.control-panel h2 {
  margin-bottom: 20px;
  font-size: 20px;
  color: #1e293b;
}

.control-section {
  margin-bottom: 25px;
  padding-bottom: 25px;
  border-bottom: 1px solid #e2e8f0;
}

.control-section:last-child {
  border-bottom: none;
  margin-bottom: 0;
  padding-bottom: 0;
}

.control-section h3 {
  font-size: 14px;
  font-weight: 600;
  color: #475569;
  margin-bottom: 10px;
}

.input, .btn {
  width: 100%;
  margin-top: 8px;
}

.input {
  padding: 10px;
  border: 2px solid #e2e8f0;
  border-radius: 8px;
  font-size: 14px;
  transition: border-color 0.2s;
}

.input:focus {
  outline: none;
  border-color: #667eea;
}

.btn {
  padding: 10px 20px;
  border: none;
  border-radius: 8px;
  cursor: pointer;
  font-size: 14px;
  font-weight: 500;
  transition: all 0.2s;
}

.btn-primary {
  background: #667eea;
  color: white;
}

.btn-primary:hover:not(:disabled) {
  background: #5568d3;
  transform: translateY(-2px);
  box-shadow: 0 4px 8px rgba(102, 126, 234, 0.3);
}

.btn-primary:disabled {
  background: #cbd5e0;
  cursor: not-allowed;
  transform: none;
}

.slider-container {
  margin-top: 10px;
}

.slider {
  width: 100%;
  height: 6px;
  border-radius: 3px;
  background: #e2e8f0;
  outline: none;
  -webkit-appearance: none;
}

.slider::-webkit-slider-thumb {
  -webkit-appearance: none;
  appearance: none;
  width: 20px;
  height: 20px;
  border-radius: 50%;
  background: #667eea;
  cursor: pointer;
  transition: background 0.2s;
}

.slider::-webkit-slider-thumb:hover {
  background: #5568d3;
}

.slider::-moz-range-thumb {
  width: 20px;
  height: 20px;
  border-radius: 50%;
  background: #667eea;
  cursor: pointer;
  border: none;
}

.slider-labels {
  display: flex;
  justify-content: space-between;
  margin-top: 8px;
  font-size: 12px;
  color: #64748b;
}

.current-speed {
  font-weight: 600;
  color: #667eea;
}

@media (max-width: 768px) {
  .control-panel {
    min-height: 300px;
    padding: 15px;
  }
  
  .control-panel h2 {
    font-size: 18px;
    margin-bottom: 15px;
  }
  
  .control-section {
    margin-bottom: 20px;
    padding-bottom: 20px;
  }
  
  .control-section h3 {
    font-size: 13px;
  }
  
  .input, .btn {
    font-size: 13px;
    padding: 8px 15px;
  }
}

@media (max-width: 480px) {
  .control-panel {
    min-height: 250px;
    padding: 12px;
  }
  
  .control-panel h2 {
    font-size: 16px;
  }
  
  .control-section {
    margin-bottom: 15px;
    padding-bottom: 15px;
  }
  
  .input, .btn {
    font-size: 12px;
    padding: 8px 12px;
  }
  
  .slider-labels {
    font-size: 11px;
  }
}
</style>

