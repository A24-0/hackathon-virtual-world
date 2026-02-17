<script setup>
const props = defineProps({
  agents: {
    type: Array,
    default: () => []
  }
})

const emit = defineEmits(['agent-click'])
</script>

<template>
  <div class="relations-graph">
    <h2>Граф отношений</h2>
    <div class="graph-placeholder">
      <p>Пока моковые данные</p>
    </div>
  </div>
</template>

<style scoped>
.relations-graph {
  background: white;
  border-radius: 12px;
  padding: 20px;
  margin-bottom: 20px;
  box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
}

.graph-placeholder {
  text-align: center;
  padding: 40px;
  color: #94a3b8;
  background: #f8fafc;
  border-radius: 8px;
}
</style>

