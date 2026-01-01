/** 前端应用入口 */
import { createApp } from 'vue'
import { createPinia } from 'pinia'
import router from './router'
import './style.css'
import App from './App.vue'

const app = createApp(App)

// 配置 Pinia
const pinia = createPinia()
app.use(pinia)

// 配置 Vue Router
app.use(router)

app.mount('#app')
