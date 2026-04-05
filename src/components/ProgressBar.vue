<template>
    <div class="progress-bar-wrapper">
        <div class="progress-track">
            <div class="progress-fill" :style="{ width: percentage + '%' }" />
        </div>
        <div class="progress-stats">
            <span>{{ formatBytes(bytes) }} transferred</span>
            <span>{{ files }} files</span>
            <span v-if="speed > 0">{{ formatBytes(speed) }}/s</span>
            <span v-if="eta > 0">ETA: {{ formatEta(eta) }}</span>
        </div>
    </div>
</template>

<script setup>
import { computed } from 'vue'

const props = defineProps({
    bytes: { type: Number, default: 0 },
    totalBytes: { type: Number, default: 0 },
    files: { type: Number, default: 0 },
    speed: { type: Number, default: 0 },
    eta: { type: Number, default: 0 },
})

const percentage = computed(() => {
    if (props.totalBytes <= 0) return 0
    return Math.min(100, Math.round((props.bytes / props.totalBytes) * 100))
})

function formatBytes(b) {
    if (b === 0) return '0 B'
    const units = ['B', 'KB', 'MB', 'GB', 'TB']
    const i = Math.floor(Math.log(b) / Math.log(1024))
    return (b / Math.pow(1024, i)).toFixed(1) + ' ' + units[i]
}

function formatEta(seconds) {
    if (seconds < 60) return seconds + 's'
    if (seconds < 3600) return Math.round(seconds / 60) + 'm'
    return Math.round(seconds / 3600) + 'h ' + Math.round((seconds % 3600) / 60) + 'm'
}
</script>

<style scoped>
.progress-bar-wrapper {
    margin: 8px 0;
}
.progress-track {
    height: 6px;
    background: var(--color-background-darker, #ddd);
    border-radius: 3px;
    overflow: hidden;
}
.progress-fill {
    height: 100%;
    background: var(--color-primary);
    border-radius: 3px;
    transition: width 0.3s ease;
}
.progress-stats {
    display: flex;
    gap: 16px;
    font-size: 12px;
    color: var(--color-text-maxcontrast);
    margin-top: 4px;
}
</style>
