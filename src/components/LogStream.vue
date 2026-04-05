<template>
    <div ref="container" class="log-stream">
        <div v-if="loading" class="loading">
            <span class="icon-loading" /> Loading logs...
        </div>
        <pre v-else>{{ log || 'No log output yet.' }}</pre>
    </div>
</template>

<script setup>
import { ref, watch, nextTick } from 'vue'

const props = defineProps({
    log: { type: String, default: '' },
    autoScroll: { type: Boolean, default: true },
    loading: { type: Boolean, default: false },
})

const container = ref(null)

watch(() => props.log, async () => {
    if (props.autoScroll && container.value) {
        await nextTick()
        container.value.scrollTop = container.value.scrollHeight
    }
})
</script>

<style scoped>
.log-stream {
    flex: 1;
    background: #1e1e1e;
    color: #d4d4d4;
    border-radius: 8px;
    padding: 12px;
    overflow-y: auto;
    font-family: 'Courier New', monospace;
    font-size: 13px;
    line-height: 1.5;
    min-height: 400px;
}
.log-stream pre {
    margin: 0;
    white-space: pre-wrap;
    word-break: break-all;
}
.loading {
    color: #888;
}
</style>
