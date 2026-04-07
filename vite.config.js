import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'
import { resolve } from 'path'

// Library-mode build: produces a single self-mounting IIFE bundle
// (dist/ms365sync.js + dist/ms365sync.css) that AppAPI injects into the
// Nextcloud-rendered top-menu page via nc.ui.resources.set_script/set_style.
export default defineConfig({
    plugins: [vue()],
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
            output: {
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
