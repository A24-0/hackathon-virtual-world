import { ref } from 'vue'
import { api } from '../utils/api'

// Маппинг типа события на настроение для отображения
function getEventMood(eventType, content = '') {
    const moodMap = {
        'chat': 'positive',
        'action': 'neutral',
        'mood_change': 'neutral',
        'relationship': 'positive',
        'world_event': 'neutral',
        'user_message': 'neutral',
        'reflection': 'neutral',
        'goal_set': 'excited'
    }
    
    // Анализируем контент на негативные слова для чатов
    if (eventType === 'chat' && content) {
        const contentLower = content.toLowerCase()
        const aggressiveWords = ['ненавижу', 'презираю', 'злой', 'злюсь', 'бесит', 'раздражает', 'достал', 'надоел', 'уйди', 'отстань', 'заткнись', 'тупой', 'идиот', 'дурак']
        const offendedWords = ['обижен', 'обидно', 'обиделся', 'несправедливо', 'нечестно', 'предал', 'обманул', 'разочарован', 'расстроен']
        const negativeWords = ['плохо', 'грустно', 'не нравится', 'неприятно']
        
        if (aggressiveWords.some(word => contentLower.includes(word))) {
            return 'negative'
        }
        if (offendedWords.some(word => contentLower.includes(word))) {
            return 'negative'
        }
        if (negativeWords.some(word => contentLower.includes(word))) {
            return 'negative'
        }
    }
    
    return moodMap[eventType] || 'neutral'
}

// Преобразование события из формата бэкенда в формат фронтенда
function mapEvent(event) {
    const agentIds = []
    if (event.agent_id) agentIds.push(event.agent_id)
    if (event.target_agent_id) agentIds.push(event.target_agent_id)
    
    const eventContent = event.content || event.description || 'Событие'
    return {
        id: event.id,
        type: event.event_type || 'action',
        content: eventContent,
        agentName: event.agent_name || null,
        agentIds: agentIds,
        timestamp: new Date(event.timestamp),
        mood: getEventMood(event.event_type, eventContent),
        description: event.description || null
    }
}

export function useEvents() {
    const events = ref([])
    const loading = ref(false)

    const fetchEvents = async () => {
        try {
            loading.value = true
            const response = await api.get('/api/v1/action/feed', {
                params: { limit: 50 }
            })
            // Бэкенд возвращает { events: [...], has_more: ..., next_cursor: ... }
            const eventsList = response.data.events || response.data || []
            events.value = eventsList.map(mapEvent)
        } catch (error) {
            console.error('Ошибка загрузки событий:', error)
            events.value = getMockEvents()
        } finally {
            loading.value = false
        }
    }

    const addEvent = async (eventData) => {
        try {
            // Определяем тип события
            if (eventData.type === 'user_event' || eventData.type === 'world_event') {
                const response = await api.post('/api/v1/action/world-event', {
                    description: eventData.content || eventData.description || 'Событие',
                    metadata: eventData.metadata || {}
                })
                const mapped = mapEvent(response.data)
                events.value.unshift(mapped)
                return mapped
            } else {
                // Для других типов событий используем agent-event
                const response = await api.post('/api/v1/action/agent-event', {
                    event_type: eventData.event_type || 'action',
                    description: eventData.content || eventData.description || 'Событие',
                    agent_id: eventData.agentIds?.[0] || '',
                    target_agent_id: eventData.agentIds?.[1] || null,
                    content: eventData.content,
                    metadata: eventData.metadata || {}
                })
                const mapped = mapEvent(response.data)
                events.value.unshift(mapped)
                return mapped
            }
        } catch (error) {
            console.error('Ошибка добавления события:', error)
            const newEvent = {
                id: Date.now().toString(),
                ...eventData,
                timestamp: new Date()
            }
            events.value.unshift(newEvent)
            return newEvent
        }
    }

    return {
        events,
        loading,
        fetchEvents,
        addEvent
    }
}

function getMockEvents() {
    const now = Date.now()
    return [
        {
            id: '1',
            type: 'interaction',
            content: 'Алекс и Мария обсуждают новое открытие',
            agentIds: ['1', '2'],
            timestamp: new Date(now - 300000),  // 5 минут назад
            mood: 'positive'
        },
        {
            id: '2',
            type: 'action',
            content: 'Роберт проводит анализ данных',
            agentIds: ['3'],
            timestamp: new Date(now - 600000),  // 10 минут назад
            mood: 'neutral'
        },
        {
            id: '3',
            type: 'discovery',
            content: 'Алекс обнаружил интересное место',
            agentIds: ['1'],
            timestamp: new Date(now - 900000),  // 15 минут назад
            mood: 'excited'
        },
        {
            id: '4',
            type: 'creation',
            content: 'Мария создала новое произведение искусства',
            agentIds: ['2'],
            timestamp: new Date(now - 1200000),  // 20 минут назад
            mood: 'happy'
        },
        {
            id: '5',
            type: 'memory',
            content: 'Алекс вспомнил прошлую встречу с Марией',
            agentIds: ['1'],
            timestamp: new Date(now - 1500000),  // 25 минут назад
            mood: 'positive'
        }
    ]
}

