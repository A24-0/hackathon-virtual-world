<script setup>
import { watch, ref, onMounted, computed } from 'vue'
import { api } from '../utils/api'

const props = defineProps({
    agent: {
        type: Object,
        default: null
    }
})

// Создаем реактивную копию агента для правильного обновления
const agentData = ref(props.agent)
const agentEvents = ref([])
const loadingEvents = ref(false)
const showMemories = ref(true)
const showEvents = ref(true)
const showRelationships = ref(true)

watch(() => props.agent, (newAgent) => {
    if (newAgent) {
        // Создаем новый объект для принудительного обновления
        agentData.value = { ...newAgent }
    }
}, { deep: true, immediate: true })

// Отдельно следим за изменениями настроения и черт
watch(() => props.agent?.mood, (newMood) => {
    if (agentData.value && newMood) {
        agentData.value.mood = { ...newMood }
    }
}, { deep: true, immediate: true })

watch(() => props.agent?.personality, (newPersonality) => {
    if (agentData.value && newPersonality) {
        agentData.value.personality = { ...newPersonality }
    }
}, { deep: true, immediate: true })

watch(() => props.agent?.currentGoal, (newGoal) => {
    if (agentData.value) {
        agentData.value.currentGoal = newGoal
    }
}, { immediate: true })

watch(() => props.agent?.currentPlan, (newPlan) => {
    if (agentData.value) {
        agentData.value.currentPlan = newPlan
    }
}, { immediate: true })

// Загрузка событий агента
const fetchAgentEvents = async () => {
    if (!props.agent?.id) return
    try {
        loadingEvents.value = true
        const response = await api.get(`/api/v1/action/events/agent/${props.agent.id}`, {
            params: { limit: 20 }
        })
        agentEvents.value = (response.data.events || []).map(event => ({
            id: event.id,
            type: event.event_type,
            content: event.content || event.description,
            timestamp: new Date(event.timestamp),
            targetAgent: event.target_agent_name
        }))
    } catch (error) {
        console.error('Ошибка загрузки событий агента:', error)
        agentEvents.value = []
    } finally {
        loadingEvents.value = false
    }
}

// Форматирование времени для событий
const formatEventTime = (timestamp) => {
    if (!timestamp) return ''
    const date = new Date(timestamp)
    if (isNaN(date.getTime())) return 'Неверная дата'
    const now = new Date()
    const diff = now - date
    
    const seconds = Math.floor(diff / 1000)
    const minutes = Math.floor(seconds / 60)
    const hours = Math.floor(minutes / 60)
    
    if (seconds < 60) return 'только что'
    if (minutes < 60) return `${minutes} мин назад`
    if (hours < 24) return `${hours} ч назад`
    return date.toLocaleDateString('ru-RU', { day: 'numeric', month: 'short', hour: '2-digit', minute: '2-digit' })
}

// Форматирование времени для воспоминаний
const formatMemoryTime = (timestamp) => {
    if (!timestamp) return ''
    const date = new Date(timestamp)
    if (isNaN(date.getTime())) return ''
    return date.toLocaleDateString('ru-RU', { day: 'numeric', month: 'short', hour: '2-digit', minute: '2-digit' })
}

// Функция для определения цвета текста на основе яркости фона
const getMoodTextColor = (backgroundColor) => {
    if (!backgroundColor) return '#ffffff'
    // Удаляем # если есть
    const hex = backgroundColor.replace('#', '')
    // Конвертируем в RGB
    const r = parseInt(hex.substr(0, 2), 16)
    const g = parseInt(hex.substr(2, 2), 16)
    const b = parseInt(hex.substr(4, 2), 16)
    // Вычисляем яркость (YIQ формула)
    const brightness = (r * 299 + g * 587 + b * 114) / 1000
    // Если яркость меньше 128, используем белый текст, иначе черный
    return brightness < 128 ? '#ffffff' : '#1e293b'
}

// Вычисляемые свойства для взаимоотношений
const relationshipsList = computed(() => {
    if (!agentData.value?.relationships) return []
    return agentData.value.relationships.map(rel => ({
        ...rel,
        sentimentColor: rel.sentiment > 0.3 ? '#10b981' : rel.sentiment > -0.3 ? '#3b82f6' : '#ef4444',
        sentimentLabel: rel.sentiment > 0.3 ? 'Дружба' : rel.sentiment > 0 ? 'Нейтрально' : 'Враждебность'
    }))
})

// Отслеживаем изменения агента и загружаем события
watch(() => props.agent?.id, (newId) => {
    if (newId) {
        fetchAgentEvents()
    }
}, { immediate: true })

onMounted(() => {
    if (props.agent?.id) {
        fetchAgentEvents()
    }
})
</script>

<template>
    <div class="agent-inspector" v-if="agentData">
        <div class="agent-header">
            <div class="avatar" :style="{ backgroundColor: agentData.mood?.color || '#667eea' }">
                {{ agentData.avatar }}
            </div>
            <div class="info">
                <h2>{{ agentData.name }}</h2>
                <p>Настроение: {{ agentData.mood?.current || 'неизвестно' }}</p>
            </div>
        </div>

        <div class="section">
            <h3>Личность</h3>
            <div class="traits" v-if="agentData.personality?.traits">
                <span 
                    v-for="trait in agentData.personality.traits" 
                    :key="trait"
                    class="trait-tag"
                >
                    {{ trait }}
                </span>
            </div>
            <p class="background">{{ agentData.personality?.background }}</p>
            <div v-if="agentData.personality" class="personality-stats">
                <div class="stat-item">
                    <span class="stat-label">Открытость:</span>
                    <div class="stat-bar">
                        <div class="stat-fill" :style="{ width: (agentData.personality.openness * 100) + '%' }"></div>
                        <span class="stat-value">{{ Math.round(agentData.personality.openness * 100) }}%</span>
                    </div>
                </div>
                <div class="stat-item">
                    <span class="stat-label">Экстраверсия:</span>
                    <div class="stat-bar">
                        <div class="stat-fill" :style="{ width: (agentData.personality.extraversion * 100) + '%' }"></div>
                        <span class="stat-value">{{ Math.round(agentData.personality.extraversion * 100) }}%</span>
                    </div>
                </div>
                <div class="stat-item">
                    <span class="stat-label">Доброжелательность:</span>
                    <div class="stat-bar">
                        <div class="stat-fill" :style="{ width: (agentData.personality.agreeableness * 100) + '%' }"></div>
                        <span class="stat-value">{{ Math.round(agentData.personality.agreeableness * 100) }}%</span>
                    </div>
                </div>
                <div class="stat-item">
                    <span class="stat-label">Сознательность:</span>
                    <div class="stat-bar">
                        <div class="stat-fill" :style="{ width: (agentData.personality.conscientiousness * 100) + '%' }"></div>
                        <span class="stat-value">{{ Math.round(agentData.personality.conscientiousness * 100) }}%</span>
                    </div>
                </div>
            </div>
        </div>

        <div class="section">
            <h3>Настроение</h3>
            <div class="mood-display">
                <span 
                    class="mood-badge"
                    :style="{ 
                        backgroundColor: agentData.mood?.color || '#6b7280',
                        color: getMoodTextColor(agentData.mood?.color || '#6b7280')
                    }"
                >
                    {{ agentData.mood?.current || 'нейтральный' }}
                </span>
                <span class="mood-level">Уровень счастья: {{ Math.round((agentData.mood?.level || 0.5) * 100) }}%</span>
            </div>
        </div>

        <div class="section">
            <h3>Текущая цель</h3>
            <p class="goal" v-if="agentData.currentGoal" :key="agentData.currentGoal">
                <span class="change-indicator">🎯</span>
                {{ agentData.currentGoal }}
            </p>
            <p class="goal-empty" v-else>Нет активной цели</p>
        </div>

        <div class="section">
            <h3>Текущий план</h3>
            <p class="plan" :key="agentData.currentPlan">
                <span class="change-indicator">📋</span>
                {{ agentData.currentPlan || 'Нет активного плана' }}
            </p>
        </div>

        <div class="section">
            <h3 @click="showMemories = !showMemories" class="section-toggle">
                Воспоминания ({{ agentData.memories?.length || 0 }})
                <span class="toggle-icon">{{ showMemories ? '▼' : '▶' }}</span>
            </h3>
            <div v-if="showMemories">
                <div v-if="agentData.memories && agentData.memories.length > 0" class="memories-list">
                    <div 
                        v-for="(memory, idx) in agentData.memories.slice(0, 10)" 
                        :key="memory.id || idx"
                        class="memory-item"
                        :class="{
                            'memory-reflection': memory.content.startsWith('[Рефлексия]'),
                            'memory-goal': memory.content.startsWith('[Цель]'),
                            'memory-dialogue': memory.content.startsWith('[Диалог]'),
                            'memory-achievement': memory.content.startsWith('[Достижение]')
                        }"
                    >
                        <p class="memory-content">{{ memory.content }}</p>
                        <span class="memory-time" v-if="memory.timestamp">{{ formatMemoryTime(memory.timestamp) }}</span>
                    </div>
                    <p v-if="agentData.memories.length > 10" class="memory-more">
                        И еще {{ agentData.memories.length - 10 }} воспоминаний...
                    </p>
                </div>
                <div v-else class="empty">
                    Нет воспоминаний
                </div>
            </div>
        </div>

        <div class="section">
            <h3 @click="showRelationships = !showRelationships" class="section-toggle">
                Взаимоотношения ({{ relationshipsList.length }})
                <span class="toggle-icon">{{ showRelationships ? '▼' : '▶' }}</span>
            </h3>
            <div v-if="showRelationships">
                <div v-if="relationshipsList.length > 0" class="relationships-list">
                    <div 
                        v-for="rel in relationshipsList" 
                        :key="rel.agentId"
                        class="relationship-item"
                    >
                        <div class="relationship-header">
                            <span class="relationship-name">{{ rel.agentName || 'Неизвестный' }}</span>
                            <span 
                                class="relationship-sentiment"
                                :style="{ color: rel.sentimentColor }"
                                :key="rel.sentiment"
                            >
                                {{ rel.sentimentLabel }} ({{ (rel.sentiment * 100).toFixed(0) }}%)
                            </span>
                        </div>
                        <div class="relationship-bar">
                            <div 
                                class="relationship-fill" 
                                :style="{ 
                                    width: Math.abs(rel.sentiment * 100) + '%',
                                    backgroundColor: rel.sentimentColor
                                }"
                            ></div>
                        </div>
                        <p v-if="rel.type" class="relationship-type">{{ rel.type }}</p>
                    </div>
                </div>
                <div v-else class="empty">
                    Нет взаимоотношений
                </div>
            </div>
        </div>

        <div class="section">
            <h3 @click="showEvents = !showEvents" class="section-toggle">
                История событий ({{ agentEvents.length }})
                <span class="toggle-icon">{{ showEvents ? '▼' : '▶' }}</span>
            </h3>
            <div v-if="showEvents">
                <div v-if="loadingEvents" class="loading">Загрузка событий...</div>
                <div v-else-if="agentEvents.length > 0" class="events-list">
                    <div 
                        v-for="event in agentEvents" 
                        :key="event.id"
                        class="event-item"
                    >
                        <div class="event-content">
                            <p class="event-text">{{ event.content }}</p>
                        </div>
                        <span v-if="event.targetAgent" class="event-target">→ {{ event.targetAgent }}</span>
                    </div>
                </div>
                <div v-else class="empty">
                    Нет событий
                </div>
            </div>
        </div>
    </div>
    <div v-else class="placeholder">
        Выберите агента
    </div>
</template>

<style scoped>
.agent-inspector {
  background: #ffffff;
  border: 1px solid #e2e8f0;
  border-radius: 16px;
  padding: 24px;
  box-shadow: 0 4px 6px rgba(0, 0, 0, 0.07), 0 1px 3px rgba(0, 0, 0, 0.05);
  min-height: 400px;
  max-height: 600px;
  overflow-y: auto;
  display: flex;
  flex-direction: column;
  transition: box-shadow 0.3s ease;
  scrollbar-width: thin;
  scrollbar-color: #cbd5e0 #f1f5f9;
}

.agent-inspector:hover {
  box-shadow: 0 8px 12px rgba(0, 0, 0, 0.1), 0 2px 4px rgba(0, 0, 0, 0.06);
}

.agent-inspector::-webkit-scrollbar {
  width: 6px;
}

.agent-inspector::-webkit-scrollbar-track {
  background: #f1f5f9;
  border-radius: 3px;
}

.agent-inspector::-webkit-scrollbar-thumb {
  background: #cbd5e0;
  border-radius: 3px;
}

.agent-inspector::-webkit-scrollbar-thumb:hover {
  background: #94a3b8;
}

.agent-header {
    display: flex;
    align-items: center;
    gap: 15px;
    margin-bottom: 20px;
    padding-bottom: 20px;
    border-bottom: 2px solid #e2e8f0;
}

.agent-header h2 {
    color: #1e293b;
    margin: 0;
    font-size: 24px;
    font-weight: 700;
}

.agent-header p {
    color: #475569;
    margin: 4px 0 0 0;
    font-size: 14px;
}

.avatar {
    width: 60px;
    height: 60px;
    border-radius: 50%;
    display: flex;
    align-items: center;
    justify-content: center;
    font-size: 32px;
    color: #ffffff;
    font-weight: 600;
    text-shadow: 0 1px 2px rgba(0, 0, 0, 0.3);
}

.section {
    margin-bottom: 20px;
    padding-bottom: 15px;
    border-bottom: 1px solid #e2e8f0;
}

.section h3 {
    color: #1e293b;
    font-size: 16px;
    font-weight: 600;
    margin: 0 0 10px 0;
}

.section p {
    color: #334155;
    font-size: 14px;
    line-height: 1.6;
    margin: 0;
}

.section .plan {
    color: #475569;
    font-weight: 500;
}

.traits {
    display: flex;
    flex-wrap: wrap;
    gap: 8px;
    margin-bottom: 10px;
}

.trait-tag {
    padding: 4px 10px;
    background: #e0e7ff;
    color: #4338ca;
    border-radius: 12px;
    font-size: 12px;
    display: inline-block;
}

.mood-display {
    display: flex;
    flex-direction: column;
    gap: 8px;
}

.mood-badge {
    padding: 8px 16px;
    color: #ffffff;
    border-radius: 12px;
    font-size: 14px;
    font-weight: 600;
    display: inline-block;
    width: fit-content;
    box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
    transition: background-color 0.5s ease, color 0.5s ease, transform 0.3s ease;
    /* Динамический цвет текста будет установлен через :style */
}

.mood-badge:hover {
    transform: scale(1.05);
}

.mood-level {
    color: #64748b;
    font-size: 12px;
    transition: color 0.3s ease;
}

.mood-level:hover {
    color: #475569;
}

.goal {
    color: #1e293b;
    font-weight: 500;
    font-size: 14px;
    padding: 12px;
    background: #f0f9ff;
    border-left: 4px solid #0ea5e9;
    border-radius: 6px;
    animation: fadeIn 0.5s ease-in;
    transition: all 0.3s ease;
}

.goal:hover {
    background: #e0f2fe;
    transform: translateX(2px);
}

.goal-empty {
    color: #94a3b8;
    font-style: italic;
    font-size: 14px;
}

@keyframes fadeIn {
    from {
        opacity: 0;
        transform: translateY(-5px);
    }
    to {
        opacity: 1;
        transform: translateY(0);
    }
}

.memory-item {
    padding: 10px;
    background: #f8fafc;
    border-radius: 6px;
    margin-bottom: 8px;
}

.memory-item p {
    color: #334155;
    font-size: 13px;
    line-height: 1.5;
    margin: 0;
}

.empty, .placeholder {
    color: #475569;
    text-align: center;
    padding: 20px;
    font-size: 14px;
    background: #ffffff;
    border: 1px solid #e2e8f0;
    border-radius: 12px;
    box-shadow: 0 1px 3px rgba(0, 0, 0, 0.05);
}

.relationship-item {
    padding: 10px;
    background: #f8fafc;
    border-radius: 6px;
    margin-bottom: 8px;
    border-left: 4px solid #cbd5e0;
    transition: all 0.2s ease;
}

.relationship-item:hover {
    background: #f1f5f9;
    transform: translateX(2px);
}

.relationship-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 5px;
}

.relationship-name {
    font-weight: 600;
    color: #1e293b;
    font-size: 14px;
}

.relationship-sentiment {
    font-size: 13px;
    font-weight: 500;
}

.relationship-type {
    font-size: 12px;
    color: #64748b;
    margin-top: 5px;
    margin-bottom: 0;
}

@media (max-width: 768px) {
  .agent-inspector {
    min-height: 300px;
    max-height: 400px;
    padding: 15px;
  }
  
  .agent-header {
    margin-bottom: 15px;
    padding-bottom: 15px;
  }
  
  .agent-avatar {
    width: 50px;
    height: 50px;
    font-size: 28px;
  }
  
  .agent-info h2 {
    font-size: 20px;
  }
  
  .section {
    margin-bottom: 15px;
    padding-bottom: 15px;
  }
  
  .section h3 {
    font-size: 15px;
  }
}

@media (max-width: 480px) {
  .agent-inspector {
    min-height: 250px;
    max-height: 350px;
    padding: 12px;
  }
  
  .agent-avatar {
    width: 45px;
    height: 45px;
    font-size: 24px;
  }
  
  .agent-info h2 {
    font-size: 18px;
  }
  
  .section h3 {
    font-size: 14px;
  }
  
  .trait-tag {
    font-size: 11px;
    padding: 3px 8px;
  }
  
  .memory-item, .relationship-item {
    padding: 8px;
    font-size: 12px;
  }
}

.relationship-bar {
  width: 100%;
  height: 6px;
  background: #e2e8f0;
  border-radius: 3px;
  overflow: hidden;
  margin: 6px 0;
}

.relationship-fill {
  height: 100%;
  transition: width 0.5s ease, background-color 0.5s ease;
  border-radius: 3px;
}

.personality-stats {
  margin-top: 12px;
  padding-top: 12px;
  border-top: 1px solid #e2e8f0;
}

.stat-item {
  margin-bottom: 10px;
}

.stat-label {
  font-size: 12px;
  color: #64748b;
  display: block;
  margin-bottom: 4px;
}

.stat-bar {
  display: flex;
  align-items: center;
  gap: 8px;
  width: 100%;
}

.stat-fill {
  flex: 1;
  height: 8px;
  background: linear-gradient(90deg, #667eea 0%, #764ba2 100%);
  border-radius: 4px;
  transition: width 0.5s ease;
  min-width: 2px;
}

.stat-value {
  font-size: 11px;
  color: #475569;
  font-weight: 600;
  min-width: 35px;
  text-align: right;
}

.change-indicator {
  display: inline-block;
  margin-right: 6px;
  animation: pulse 2s infinite;
}

@keyframes pulse {
  0%, 100% {
    opacity: 1;
  }
  50% {
    opacity: 0.6;
  }
}
</style>