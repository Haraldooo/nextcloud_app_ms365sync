import { createApp } from 'vue'
import App from './App.vue'
import router from './router.js'

function mount() {
    // AppAPI's embedded.php template stamps a <div id="content"></div>
    // INSIDE Nextcloud's own outer <div id="content" class="app-app_api">,
    // so the page ends up with two elements sharing the id. document
    // .getElementById returns the first in tree order (the outer one),
    // which is fine to mount into, but be explicit about the inner empty
    // slot when it exists so we sit where AppAPI intended. Fall back to
    // #app-content (the standalone dev page in index.html) and finally
    // <body> for any other host.
    const target = document.querySelector('.app-app_api > #content')
        || document.getElementById('content')
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
