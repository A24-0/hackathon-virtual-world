import { ref } from 'vue'
import { api } from '../utils/api'

export function useEvents() {
    const events = ref([])
    const loading = ref(false)

    const fetchEvents = async () => {
        try {
            loading.value = true
            const response = await api.get('/api/events')
            events.value = response.data
        } catch (error) {
            console.error('Ошибка загрузки событий:', error)
            events.value = getMockEvents()
        } finally {
            loading.value = false
        }
    }

    const addEvent = async (eventData) => {
        try {
            const response = await api.post('/api/events', eventData)
            events.value.unshift(response.data)
            return response.data
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

