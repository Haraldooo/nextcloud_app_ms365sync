<template>
    <div class="log-view">
        <div class="log-header">
            <h2>Logs: Job #{{ jobId }}</h2>
            <div class="log-controls">
                <label>
                    <input v-model="autoScroll" type="checkbox">
                    Auto-scroll
                </label>
                <NcButton type="secondary" @click="refresh">
                    Refresh
                </NcButton>
                <NcButton type="secondary" @click="downloadLog">
                    Download
                </NcButton>
            </div>
        </div>

        <LogStream :log="logContent" :auto-scroll="autoScroll" :loading="loading" />
    </div>
</template>

<script setup>
import { ref, onMounted, onUnmounted } from 'vue'
import NcButton from '@nextcloud/vue/components/NcButton'
import LogStream from '../components/LogStream.vue'
import { getJobLog } from '../services/api.js'

const props = defineProps({
    jobId: { type: [String, Number], required: true },
})

const logContent = ref('')
const loading = ref(true)
const autoScroll = ref(true)
let pollInterval = null

async function refresh() {
    try {
        const res = await getJobLog(props.jobId)
        // Backend returns PlainTextResponse, so res.data is the raw string.
        logContent.value = typeof res.data === 'string' ? res.data : (res.data?.log ?? '')
    } catch (e) {
        logContent.value = 'Failed to load log: ' + e.message
    } finally {
        loading.value = false
    }
}

function downloadLog() {
    const blob = new Blob([logContent.value], { type: 'text/plain' })
    const url = URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = `ms365sync-job-${props.jobId}.log`
    a.click()
    URL.revokeObjectURL(url)
}

onMounted(async () => {
    await refresh()
    pollInterval = setInterval(refresh, 10000)
})

onUnmounted(() => {
    if (pollInterval) clearInterval(pollInterval)
})
</script>

<style scoped>
.log-view {
    padding: 20px;
    height: 100%;
    display: flex;
    flex-direction: column;
}
.log-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 12px;
}
.log-controls {
    display: flex;
    gap: 12px;
    align-items: center;
}
</style>
