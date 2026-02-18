import './assets/main.css'

import { createApp } from 'vue'
import App from './App.vue'

try {
  const app = createApp(App)
  app.config.errorHandler = (err, instance, info) => {
    console.error('Глобальная ошибка Vue:', err, info)
  }
  app.mount('#app')
} catch (error) {
  console.error('Критическая ошибка при запуске приложения:', error)
  document.getElementById('app').innerHTML = `
    <div style="padding: 20px; text-align: center; color: #ef4444;">
      <h1>Ошибка загрузки приложения</h1>
      <p>${error.message}</p>
      <p>Проверьте консоль для подробностей</p>
    </div>
  `
}
