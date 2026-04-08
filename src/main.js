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
    // Fill the parent #content cell exactly — Nextcloud already positions
    // its #content below the top navbar with the standard left/right
    // gutters, so we want to occupy that box completely. #content has no
    // intrinsic height in the AppAPI embedded template, so anchor the
    // host with position:absolute inset:0 against a relatively-positioned
    // parent.
    if (target instanceof HTMLElement) {
        const cs = getComputedStyle(target)
        if (cs.position === 'static') {
            target.style.position = 'relative'
        }
    }
    host.style.position = 'absolute'
    host.style.top = '0'
    host.style.left = '0'
    host.style.right = '0'
    host.style.bottom = '0'
    host.style.display = 'flex'
    host.style.flexDirection = 'column'
    host.style.minHeight = '0'
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
