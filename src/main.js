import { createApp } from 'vue'
import App from './App.vue'
import router from './router.js'

function mount() {
    // AppAPI's embedded.php template (rendered when the user clicks the
    // top-menu entry registered via nc.ui.top_menu.register) only contains
    // <div id="content"></div>. The standalone dev page in index.html uses
    // #app-content. Fall back to <body> for any other host so the bundle
    // still surfaces *something* during local builds.
    const target = document.getElementById('content')
        || document.getElementById('app-content')
        || document.body
    const host = document.createElement('div')
    host.id = 'ms365sync'
    // #content has no intrinsic height in the embedded template, so the
    // 100%-height flex layout in App.vue would collapse to 0px. Pin the
    // host to the viewport-minus-header height instead.
    host.style.height = 'calc(100vh - var(--header-height, 50px))'
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
