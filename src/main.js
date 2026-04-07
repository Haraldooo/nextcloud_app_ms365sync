import { createApp } from 'vue'
import App from './App.vue'
import router from './router.js'

function mount() {
    const target = document.getElementById('app-content-vue')
        || document.getElementById('app-content')
        || document.body
    const host = document.createElement('div')
    host.id = 'ms365sync'
    target.appendChild(host)

    const app = createApp(App)
    app.use(router)
    app.mount(host)
}

if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', mount)
} else {
    mount()
}
