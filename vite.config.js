import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'
import { resolve } from 'path'
import { mkdirSync, renameSync } from 'fs'

const appId = 'ms365sync'

export default defineConfig({
    plugins: [
        vue(),
        // Move CSS files from js/ to css/ after build
        {
            name: 'move-css',
            closeBundle() {
                try {
                    mkdirSync('css', { recursive: true })
                    renameSync(`js/${appId}-style.css`, `css/${appId}-main.css`)
                } catch {
                    // CSS file may not exist
                }
            },
        },
    ],
    build: {
        outDir: 'js',
        rollupOptions: {
            input: {
                main: resolve(__dirname, 'src/main.js'),
            },
            output: {
                entryFileNames: `${appId}-[name].js`,
                chunkFileNames: `${appId}-[name].js`,
                assetFileNames: `${appId}-[name][extname]`,
            },
        },
        cssCodeSplit: false,
    },
    resolve: {
        alias: {
            '@': resolve(__dirname, 'src'),
        },
    },
})
