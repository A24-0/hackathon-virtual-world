<script setup>
import { ref, watch, nextTick } from 'vue'

const props = defineProps({
  events: {
    type: Array,
    required: true
  }
})

const eventsListRef = ref(null)

// Функция для иконки по типу события
const getEventIcon = (type) => {
  const icons = {
    interaction: '•',
    action: '•',
    discovery: '•',
    creation: '•',
    memory: '•',
    emotion: '•',
    user_event: '•'
  }
  return icons[type] || '•'
}

// Форматирование времени (например: "5 мин назад")
const formatTime = (timestamp) => {
  if (!timestamp) return ''
  const date = new Date(timestamp)
  if (isNaN(date.getTime())) return 'Неверная дата'
  const now = new Date()
  const diff = now - date
  
  const seconds = Math.floor(diff / 1000)
  const minutes = Math.floor(seconds / 60)
  const hours = Math.floor(minutes / 60)
  const days = Math.floor(hours / 24)

  if (seconds < 10) return 'только что'
  if (seconds < 60) return `${seconds} сек назад`
  if (minutes < 60) return `${minutes} мин назад`
  if (hours < 24) return `${hours} ч назад`
  if (days < 7) return `${days} дн назад`
  return date.toLocaleDateString('ru-RU', { day: 'numeric', month: 'short', hour: '2-digit', minute: '2-digit' })
}

watch(() => props.events, () => {
  nextTick(() => {
    if (eventsListRef.value && props.events.length > 0) {
      eventsListRef.value.scrollTop = 0
    }
  })
}, { deep: true })
</script>

<template>
  <div class="card event-feed">
    <h2>Лента событий</h2>
    <div class="events-list" ref="eventsListRef">
      <div
        v-for="event in events"
        :key="event.id"
        class="event-item"
        :class="`event-${event.mood || 'neutral'}`"
      >
        <div class="event-icon">{{ getEventIcon(event.type) }}</div>
        <div class="event-content">
          <p class="event-text">
            <span v-if="event.agentName" class="agent-name">{{ event.agentName }}:</span>
            <span v-else-if="event.description && event.description.includes('→')" class="agent-name">{{ event.description.split('→')[0].trim() }}:</span>
            {{ event.content }}
          </p>
        </div>
      </div>
      <div v-if="events.length === 0" class="empty-state">
        <p>Пока нет событий</p>
      </div>
    </div>
  </div>
</template>

<style scoped>
.event-feed {
  min-height: 400px;
  max-height: 600px;
  display: flex;
  flex-direction: column;
  background: #ffffff;
  border: 1px solid #e2e8f0;
  border-radius: 16px;
  padding: 24px;
  box-shadow: 0 4px 6px rgba(0, 0, 0, 0.07), 0 1px 3px rgba(0, 0, 0, 0.05);
  transition: box-shadow 0.3s ease;
}

.event-feed:hover {
  box-shadow: 0 8px 12px rgba(0, 0, 0, 0.1), 0 2px 4px rgba(0, 0, 0, 0.06);
}

.event-feed h2 {
  margin-bottom: 15px;
  font-size: 20px;
  color: #1e293b;
}

.events-list {
  overflow-y: auto;
  flex: 1;
  display: flex;
  flex-direction: column;
  gap: 12px;
  min-height: 0;
}

.event-item {
  display: flex;
  gap: 12px;
  padding: 12px;
  background: #f8fafc;
  border-radius: 8px;
  border-left: 4px solid #cbd5e0;
  transition: all 0.2s;
}

.event-item:hover {
  background: #f1f5f9;
  transform: translateX(4px);
}

.event-item.event-positive {
  border-left-color: #10b981;
}

.event-item.event-excited {
  border-left-color: #f59e0b;
}

.event-item.event-neutral {
  border-left-color: #6b7280;
}

.event-item.event-negative {
  border-left-color: #ef4444;
  background: #fef2f2;
}

.event-item.event-negative:hover {
  background: #fee2e2;
}

.event-item.event-happy {
  border-left-color: #10b981;
}

.event-icon {
  font-size: 24px;
  flex-shrink: 0;
  color: #475569;
  line-height: 1;
}

.event-content {
  flex: 1;
  min-width: 0;
}

.event-text {
  font-size: 14px;
  color: #334155;
  margin-bottom: 4px;
  line-height: 1.4;
}

.agent-name {
  font-weight: 700;
  color: #667eea;
  font-size: 15px;
  margin-right: 4px;
}

.event-time {
  font-size: 12px;
  color: #94a3b8;
}

.empty-state {
  text-align: center;
  padding: 40px;
  color: #94a3b8;
}

.events-list::-webkit-scrollbar {
  width: 6px;
}

.events-list::-webkit-scrollbar-track {
  background: #f1f5f9;
  border-radius: 3px;
}

.events-list::-webkit-scrollbar-thumb {
  background: #cbd5e0;
  border-radius: 3px;
}

.events-list::-webkit-scrollbar-thumb:hover {
  background: #94a3b8;
}

@media (max-width: 768px) {
  .event-feed {
    min-height: 300px;
    max-height: 400px;
  }
  
  .event-feed h2 {
    font-size: 18px;
    margin-bottom: 12px;
  }
  
  .event-item {
    padding: 10px;
    gap: 10px;
  }
  
  .event-icon {
    font-size: 20px;
  }
  
  .event-text {
    font-size: 13px;
  }
  
  .event-time {
    font-size: 11px;
  }
}

@media (max-width: 480px) {
  .event-feed {
    min-height: 250px;
    max-height: 350px;
  }
  
  .event-feed h2 {
    font-size: 16px;
  }
  
  .event-item {
    padding: 8px;
    gap: 8px;
  }
  
  .event-icon {
    font-size: 18px;
  }
  
  .event-text {
    font-size: 12px;
  }
}
</style>

