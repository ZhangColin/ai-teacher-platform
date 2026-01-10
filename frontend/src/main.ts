/** 前端应用入口 */
import { createApp } from 'vue'
import { createPinia } from 'pinia'
import router from './router'
import './style.css'
import './styles/markdown.css' // Markdown 通用样式
import App from './App.vue'
import { useAuthStore } from './stores/authStore'

const app = createApp(App)

// 配置 Pinia
const pinia = createPinia()
app.use(pinia)

// 配置 Vue Router
app.use(router)

// 初始化认证状态（从存储中恢复Token）
const authStore = useAuthStore()
authStore.restoreAuth()

app.mount('#app')
