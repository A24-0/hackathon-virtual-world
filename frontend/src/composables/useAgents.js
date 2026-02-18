import { ref } from 'vue'
import { api } from '../utils/api'

// Маппинг настроения на цвета
const moodColors = {
    'happy': '#10b981',
    'sad': '#3b82f6',
    'angry': '#ef4444',
    'neutral': '#6b7280',
    'excited': '#f59e0b',
    'anxious': '#f97316',
    'bored': '#94a3b8'
}

const moodNames = {
    'happy': 'счастливый',
    'sad': 'грустный',
    'angry': 'раздражённый',
    'neutral': 'нейтральный',
    'excited': 'взволнованный',
    'anxious': 'тревожный',
    'bored': 'скучный'
}

// Преобразование агента из формата бэкенда в формат фронтенда
function mapAgent(agent) {
    const moodValue = agent.emotion?.mood || 'neutral'
    return {
        id: agent.id,
        name: agent.name,
        avatar: agent.avatar_url || ':)',
        personality: {
            traits: generateTraits(agent.personality),
            background: agent.bio || 'Нет описания'
        },
        mood: {
            current: moodNames[moodValue] || 'нейтральный',
            level: agent.emotion?.happiness || 0.5,
            color: moodColors[moodValue] || '#6b7280'
        },
        memories: [], // Будет загружено отдельно при необходимости
        relationships: (agent.relationships || []).map(rel => ({
            agentId: rel.agent_id,
            agentName: rel.agent_name,
            sentiment: rel.sympathy,
            type: rel.description || 'знакомый'
        })),
        currentPlan: agent.current_plan || 'Нет активного плана',
        currentGoal: agent.current_goal,
        status: agent.is_active ? 'активный' : 'неактивный'
    }
}

// Генерация черт личности на основе значений (реактивно обновляется)
function generateTraits(personality) {
    if (!personality) return ['неизвестно']
    const traits = []
    // Используем более точные пороги для разнообразия
    if (personality.openness > 0.7) traits.push('открытый')
    if (personality.openness < 0.3) traits.push('замкнутый')
    if (personality.extraversion > 0.7) traits.push('экстравертный')
    if (personality.extraversion < 0.3) traits.push('интровертный')
    if (personality.agreeableness > 0.7) traits.push('доброжелательный')
    if (personality.agreeableness < 0.3) traits.push('недоверчивый')
    if (personality.conscientiousness > 0.7) traits.push('сознательный')
    if (personality.conscientiousness < 0.3) traits.push('беспечный')
    if (personality.neuroticism > 0.7) traits.push('эмоциональный')
    if (personality.neuroticism < 0.3) traits.push('спокойный')
    return traits.length > 0 ? traits : ['сбалансированный']
}

// Загрузка детальной информации об агенте (с воспоминаниями)
async function fetchAgentDetail(agentId) {
    try {
        const response = await api.get(`/api/v1/system/agents/${agentId}`)
        return mapAgentDetail(response.data)
    } catch (error) {
        console.error('Ошибка загрузки деталей агента:', error)
        return null
    }
}

function mapAgentDetail(agent) {
    const mapped = mapAgent(agent)
    // Убеждаемся что личность передается с числовыми значениями
    if (agent.personality) {
        mapped.personality = {
            ...mapped.personality,
            openness: agent.personality.openness || 0.5,
            extraversion: agent.personality.extraversion || 0.5,
            agreeableness: agent.personality.agreeableness || 0.5,
            conscientiousness: agent.personality.conscientiousness || 0.5,
            neuroticism: agent.personality.neuroticism || 0.5
        }
    }
    mapped.memories = (agent.memories || []).map((mem, idx) => ({
        id: idx.toString(),
        content: mem.content,
        timestamp: new Date(mem.timestamp)
    }))
    return mapped
}

export function useAgents(){
    const agents = ref([])
    const loading = ref(false)
    const selectedAgent = ref(null)

    const fetchAgents = async () => {
        try{
            loading.value = true
            const response = await api.get('/api/v1/system/agents')
            // Бэкенд возвращает { agents: [...], total: ... }
            const agentsList = response.data.agents || response.data || []
            agents.value = agentsList.map(mapAgent)
        } catch (error) {
            console.error('Ошибка загрузки агентов: ', error)
            console.error('Детали ошибки:', error.response?.data || error.message)
            // Не используем мок-данные, оставляем пустой массив
            agents.value = []
        } finally {
            loading.value = false
        }
    }

    const selectAgent = async (agentID) => {
        // Загружаем детальную информацию об агенте
        const detail = await fetchAgentDetail(agentID)
        if (detail) {
            selectedAgent.value = detail
            // Обновляем агента в списке, создавая новый массив для реактивности
            const index = agents.value.findIndex(a => a.id === agentID)
            if (index !== -1) {
                agents.value = [
                    ...agents.value.slice(0, index),
                    detail,
                    ...agents.value.slice(index + 1)
                ]
            }
        } else {
            selectedAgent.value = agents.value.find(agent => agent.id === agentID) || null
        }
    }
    
    // Метод для обновления конкретного агента в списке
    const updateAgent = (agentId, updates) => {
        const index = agents.value.findIndex(a => a.id === agentId)
        if (index !== -1) {
            agents.value = [
                ...agents.value.slice(0, index),
                { ...agents.value[index], ...updates },
                ...agents.value.slice(index + 1)
            ]
        }
    }

    return{
        agents,
        loading,
        selectedAgent,
        selectAgent,
        fetchAgents,
        updateAgent
    }
}

function getMockAgents() {
    return [
        {
            id: '1',
            name: 'Алекс',
            avatar: ':)',
            personality: {
                traits: ['любознательный', 'дружелюбный'],
                background: 'Алекс - исследователь, который любит изучать новое'
            },
            mood: {
                current: 'счастливый',
                level: 0.8,
                color: '#10b981'
            },
            memories: [
                {
                    id: '1',
                    content: 'Встретил нового друга по имени Мария',
                    timestamp: new Date()
                }
            ],
            relationships: [
                {
                    agentId: '2',
                    agentName: 'Мария',
                    sentiment: 0.7,
                    type: 'друг'
                }
            ],
            currentPlan: 'Изучить новую область виртуального мира',
            status: 'активный'
        },
        {
            id: '2',
            name: 'Мария',
            avatar: ':D',
            personality: {
                traits: ['творческая', 'эмпатичная'],
                background: 'Мария - художник, который видит красоту во всем'
            },
            mood: {
                current: 'спокойная',
                level: 0.6,
                color: '#3b82f6'
            },
            memories: [
                {
                    id: '1',
                    content: 'Познакомилась с Алексом',
                    timestamp: new Date()
                }
            ],
            relationships: [
                {
                    agentId: '1',
                    agentName: 'Алекс',
                    sentiment: 0.7,
                    type: 'друг'
                }
            ],
            currentPlan: 'Создать новую картину',
            status: 'активный'
        },
        {
            id: '3',
            name: 'Роберт',
            avatar: ':0',
            personality: {
                traits: ['логичный', 'аналитичный'],
                background: 'Роберт - ученый, который анализирует все вокруг'
            },
            mood: {
                current: 'нейтральное',
                level: 0.5,
                color: '#6b7280'
            },
            memories: [],
            relationships: [],
            currentPlan: 'Проанализировать данные',
            status: 'активый'
        }
    ]
}