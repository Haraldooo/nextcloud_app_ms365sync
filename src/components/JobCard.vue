<template>
    <div class="job-card" @click="$router.push({ name: 'job-detail', params: { id: job.id } })">
        <div class="job-card-header">
            <strong>{{ job.name }}</strong>
            <span :class="['status-badge', job.status]">{{ job.status }}</span>
        </div>
        <div class="job-card-meta">
            <span>{{ job.sourceType === 'sharepoint' ? 'SharePoint' : 'OneDrive' }}: {{ job.sourceDriveName }}</span>
            <span>&rarr; {{ job.destPath }}</span>
        </div>
        <ProgressBar v-if="job.status === 'running'"
            :bytes="job.bytesTransferred || 0"
            :files="job.filesTransferred || 0" />
        <div class="job-card-footer">
            <span v-if="job.lastRunAt" class="last-run">Last: {{ formatDate(job.lastRunAt) }}</span>
            <span v-else class="last-run">Never run</span>
            <div class="job-card-actions" @click.stop>
                <NcButton v-if="job.status !== 'running'" type="primary" @click="$emit('start', job)">
                    Start
                </NcButton>
                <NcButton v-else type="warning" @click="$emit('stop', job)">
                    Stop
                </NcButton>
                <NcButton type="tertiary-no-background"
                    @click="$router.push({ name: 'logs', params: { jobId: job.id } })">
                    Logs
                </NcButton>
                <NcButton type="error" @click="$emit('delete', job)">
                    Delete
                </NcButton>
            </div>
        </div>
    </div>
</template>

<script setup>
import NcButton from '@nextcloud/vue/components/NcButton'
import ProgressBar from './ProgressBar.vue'

defineProps({
    job: { type: Object, required: true },
})

defineEmits(['start', 'stop', 'delete'])

function formatDate(dateStr) {
    if (!dateStr) return ''
    return new Date(dateStr).toLocaleString()
}
</script>

<style scoped>
.job-card {
    background: var(--color-background-dark);
    border-radius: 8px;
    padding: 16px;
    cursor: pointer;
    transition: box-shadow 0.15s;
}
.job-card:hover {
    box-shadow: 0 2px 8px rgba(0,0,0,0.1);
}
.job-card-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 8px;
}
.status-badge {
    padding: 2px 8px;
    border-radius: 12px;
    font-size: 12px;
    font-weight: bold;
    color: white;
}
.status-badge.idle { background: var(--color-text-maxcontrast); }
.status-badge.running { background: var(--color-primary); }
.status-badge.paused { background: var(--color-warning); }
.status-badge.completed { background: var(--color-success); }
.status-badge.error { background: var(--color-error); }
.job-card-meta {
    display: flex;
    flex-direction: column;
    gap: 2px;
    font-size: 13px;
    color: var(--color-text-maxcontrast);
    margin-bottom: 8px;
}
.job-card-footer {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-top: 8px;
}
.last-run {
    font-size: 12px;
    color: var(--color-text-maxcontrast);
}
.job-card-actions {
    display: flex;
    gap: 4px;
}
</style>
