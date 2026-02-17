<script setup>
const props = defineProps({
    agent: {
        type: Object,
        default: null
    }
})
</script>

<template>
    <div class="agent-inspector" v-if="agent">
        <div class="agent-header">
            <div class="avatar" :style="{ backgroundColor: agent.mood?.color || '#667eea' }">
                {{ agent.avatar }}
            </div>
            <div class="info">
                <h2>{{ agent.name }}</h2>
                <p>Настроение: {{ agent.mood?.current || 'неизвестно' }}</p>
            </div>
        </div>

        <div class="section">
            <h3>Личность</h3>
            <div class="traits" v-if="agent.personality?.traits">
                <span 
                    v-for="trait in agent.personality.traits" 
                    :key="trait"
                    class="trait-tag"
                >
                    {{ trait }}
                </span>
            </div>
            <p class="background">{{ agent.personality?.background }}</p>
        </div>

        <div class="section">
            <h3>Текущий план</h3>
            <p class="plan">{{ agent.currentPlan || 'Нет активного плана' }}</p>
        </div>

        <div class="section">
            <h3>Воспоминания</h3>
            <div v-if="agent.memories && agent.memories.length > 0">
                <div 
                    v-for="memory in agent.memories" 
                    :key="memory.id"
                    class="memory-item"
                >
                    <p>{{ memory.content }}</p>
                </div>
            </div>
            <div v-else class="empty">
                Нет воспоминаний
            </div>
        </div>
    </div>
    <div v-else class="placeholder">
        Выберите агента
    </div>
</template>

<style scoped>
.agent-inspector {
    background: white;
    border-radius: 12px;
    padding: 20px;
    box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
    margin-top: 20px;
}

.agent-header {
    display: flex;
    align-items: center;
    gap: 15px;
    margin-bottom: 20px;
    padding-bottom: 20px;
    border-bottom: 2px solid #e2e8f0;
}

.avatar {
    width: 60px;
    height: 60px;
    border-radius: 50%;
    display: flex;
    align-items: center;
    justify-content: center;
    font-size: 32px;
}

.section {
    margin-bottom: 20px;
    padding-bottom: 15px;
    border-bottom: 1px solid #e2e8f0;
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
}

.memory-item {
    padding: 10px;
    background: #f8fafc;
    border-radius: 6px;
    margin-bottom: 8px;
}

.empty, .placeholder {
    color: #94a3b8;
    text-align: center;
    padding: 20px;
}
</style>