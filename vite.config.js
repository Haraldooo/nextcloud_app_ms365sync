import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'
import { resolve } from 'path'

const appId = 'ms365sync'

export default defineConfig({
    plugins: [vue()],
    build: {
        outDir: 'js',
        rollupOptions: {
            input: {
                main: resolve(__dirname, 'src/main.js'),
            },
            output: {
                entryFileNames: `${appId}-[name].js`,
                chunkFileNames: `${appId}-[name].js`,
                assetFileNames: (assetInfo) => {
                    if (assetInfo.name?.endsWith('.css')) {
                        return `../css/${appId}-[name][extname]`
                    }
                    return `${appId}-[name][extname]`
                },
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
