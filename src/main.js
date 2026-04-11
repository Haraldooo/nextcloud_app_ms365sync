import { createApp } from 'vue'
import App from './App.vue'
import router from './router.js'

function mount() {
    // AppAPI's embedded.php template stamps a <div id="content"></div>
    // INSIDE Nextcloud's own outer <div id="content" class="app-app_api">,
    // creating a duplicate id. Rename the inner one to avoid side-effects.
    const appApiContent = document.querySelector('.app-app_api > #content')
    if (appApiContent) {
        appApiContent.id = 'ms365sync-content'
    }
    const target = appApiContent
        || document.getElementById('content')
        || document.getElementById('app-content')
        || document.body
    const host = document.createElement('div')
    host.id = 'ms365sync'
    // Nextcloud's outer #content is already sized + positioned correctly
    // (margin, header offset, body width/height, border-radius, flex
    // container). Just stretch as a flex child inside it.
    host.style.flex = '1 1 auto'
    host.style.minWidth = '0'
    host.style.minHeight = '0'
    host.style.display = 'flex'
    host.style.flexDirection = 'column'
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
