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
  const now = new Date()
  const diff = now - date
  const minutes = Math.floor(diff / 60000)
  
  if (minutes < 1) return 'только что'
  if (minutes < 60) return `${minutes} мин назад`
  const hours = Math.floor(minutes / 60)
  if (hours < 24) return `${hours} ч назад`
  return date.toLocaleTimeString('ru-RU', { hour: '2-digit', minute: '2-digit' })
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
          <p class="event-text">{{ event.content }}</p>
          <span class="event-time">{{ formatTime(event.timestamp) }}</span>
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
  border-radius: 12px;
  padding: 20px;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.05);
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
}

.event-item.event-happy {
  border-left-color: #10b981;
}

.event-icon {
  font-size: 24px;
  flex-shrink: 0;
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

