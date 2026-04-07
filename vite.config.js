import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'
import { resolve } from 'path'

// Builds the SPA into dist/ as a self-contained static bundle that the
// ExApp container will serve under /ui/. The Dockerfile copies dist/
// into ms365sync_exapp/ui at image build time.
export default defineConfig({
    plugins: [vue()],
    base: './',
    build: {
        outDir: 'dist',
        emptyOutDir: true,
    },
    resolve: {
        alias: {
            '@': resolve(__dirname, 'src'),
        },
    },
})
