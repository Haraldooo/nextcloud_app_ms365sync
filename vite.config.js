import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'
import { resolve } from 'path'

// Library-mode build: produces a single self-mounting IIFE bundle
// (dist/ms365sync.js + dist/ms365sync.css) that AppAPI injects into the
// Nextcloud-rendered top-menu page via nc.ui.resources.set_script/set_style.
export default defineConfig({
    plugins: [vue()],
    // Vite's `lib` mode does NOT replace `process.env.NODE_ENV` the way app
    // mode does, so Vue 3 / vue-router / @nextcloud/axios end up shipping a
    // literal `process.env.NODE_ENV` reference that throws
    // `ReferenceError: process is not defined` the moment the IIFE runs in
    // the browser. Stub it out at compile time.
    define: {
        'process.env.NODE_ENV': JSON.stringify('production'),
        'process.env': '{}',
    },
    build: {
        outDir: 'dist',
        emptyOutDir: true,
        cssCodeSplit: false,
        lib: {
            entry: resolve(__dirname, 'src/main.js'),
            name: 'Ms365Sync',
            formats: ['iife'],
            fileName: () => 'ms365sync.js',
        },
        rollupOptions: {
            // Everything (Vue, vue-router, @nextcloud/vue, axios) is bundled
            // into the IIFE. Nextcloud does not expose these as page globals,
            // so externalizing would crash at init. The trade-off is bundle
            // size; that's acceptable for an admin-only ExApp.
            output: {
                // Belt-and-suspenders shim. The `define` above already
                // replaces `process.env.NODE_ENV`, but if any transitive dep
                // accesses bare `process` or `process.X` in a way Vite can't
                // statically rewrite, the IIFE would still throw
                // `ReferenceError: process is not defined`. We assign onto
                // globalThis (rather than `var process = ...`) because the
                // minifier renames local identifiers — `var process` becomes
                // `var Be`, defeating the shim. A property assignment on
                // globalThis can't be renamed (the key is a string), so
                // `process` becomes a real global available to the rest of
                // the IIFE. We only set it if missing, so a host page that
                // already exposes `process` is left alone.
                intro: 'if (typeof globalThis.process === "undefined") { globalThis.process = { env: { NODE_ENV: "production" } }; }',
                assetFileNames: (asset) => {
                    if (asset.name && asset.name.endsWith('.css')) {
                        return 'ms365sync.css'
                    }
                    return 'ms365sync.[ext]'
                },
            },
        },
    },
    resolve: {
        alias: {
            '@': resolve(__dirname, 'src'),
        },
    },
})
