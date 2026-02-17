import { ref } from 'vue'
import { api } from '../utils/api'

export function useAgents(){
    const agents = ref([])
    const loading = ref(false)
    const selectedAgent = ref(null)

    const fetchAgents = async () => {
        try{
            loading.value = true
            const response = await api.get('/api/agents')
            agents.value = response.data
        } catch (error) {
            console.error('Ошибка загрузки агентов: ', error)
            agents.value = getMockAgents()
        } finally {
            loading.value = false
        }
    }

    const selectAgent = (agentID) => {
        selectedAgent.value = agents.value.find(agent => agent.id === agentID) || null
    }

    return{
        agents,
        loading,
        selectedAgent,
        selectAgent,
        fetchAgents
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