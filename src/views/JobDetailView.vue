<template>
    <div class="job-detail-view">
        <div v-if="loading" class="loading">
            <span class="icon-loading" />
        </div>

        <template v-else-if="job">
            <div class="detail-header">
                <h2>{{ job.name }}</h2>
                <span :class="['status-badge', job.status]">{{ job.status }}</span>
            </div>

            <div class="detail-grid">
                <div class="detail-section">
                    <h3>Source</h3>
                    <dl>
                        <dt>Type</dt><dd>{{ job.sourceType }}</dd>
                        <dt>Drive</dt><dd>{{ job.sourceDriveName }}</dd>
                        <dt>Drive ID</dt><dd class="mono">{{ job.sourceDriveId }}</dd>
                    </dl>
                </div>

                <div class="detail-section">
                    <h3>Destination</h3>
                    <dl>
                        <dt>Type</dt><dd>{{ job.destType }}</dd>
                        <dt>Path</dt><dd>{{ job.destPath }}</dd>
                        <dt>User</dt><dd>{{ job.destUser || '-' }}</dd>
                    </dl>
                </div>

                <div class="detail-section">
                    <h3>Configuration</h3>
                    <dl>
                        <dt>Sync Mode</dt><dd>{{ job.syncMode }}</dd>
                        <dt>Schedule</dt><dd>{{ job.schedule }}</dd>
                        <dt>Enabled</dt><dd>{{ job.enabled ? 'Yes' : 'No' }}</dd>
                        <dt>Last Run</dt><dd>{{ job.lastRunAt || 'Never' }}</dd>
                    </dl>
                </div>

                <div class="detail-section">
                    <h3>Transfer Progress</h3>
                    <ProgressBar :bytes="progress.bytesTransferred || 0"
                        :files="progress.filesTransferred || 0"
                        :speed="progress.speed || 0"
                        :eta="progress.eta || 0" />
                </div>
            </div>

            <div v-if="job.lastError" class="error-alert">
                <strong>Last Error:</strong> {{ job.lastError }}
            </div>

            <div class="detail-actions">
                <NcButton v-if="job.status !== 'running'" type="primary" @click="onStart">
                    Start
                </NcButton>
                <NcButton v-else type="warning" @click="onStop">
                    Stop
                </NcButton>
                <NcButton type="secondary" :to="{ name: 'logs', params: { jobId: job.id } }">
                    View Logs
                </NcButton>
                <NcButton type="error" @click="onDelete">
                    Delete
                </NcButton>
            </div>
        </template>
    </div>
</template>

<script setup>
import { ref, onMounted, onUnmounted } from 'vue'
import { useRouter } from 'vue-router'
import NcButton from '@nextcloud/vue/dist/Components/NcButton.js'
import ProgressBar from '../components/ProgressBar.vue'
import { getJob, startJob, stopJob, deleteJob, getJobProgress } from '../services/api.js'

const props = defineProps({
    id: { type: [String, Number], required: true },
})

const router = useRouter()
const job = ref(null)
const progress = ref({})
const loading = ref(true)
let pollInterval = null

async function loadJob() {
    try {
        const res = await getJob(props.id)
        job.value = res.data
    } catch (e) {
        // handle
    } finally {
        loading.value = false
    }
}

async function pollProgress() {
    if (job.value?.status !== 'running') return
    try {
        const res = await getJobProgress(props.id)
        progress.value = res.data
        if (res.data.status) {
            job.value.status = res.data.status
        }
    } catch (e) {
        // ignore
    }
}

async function onStart() {
    try {
        const res = await startJob(props.id)
        job.value = res.data
    } catch (e) {
        // handle
    }
}

async function onStop() {
    try {
        const res = await stopJob(props.id)
        job.value = res.data
    } catch (e) {
        // handle
    }
}

async function onDelete() {
    if (!confirm(`Delete sync job "${job.value.name}"?`)) return
    await deleteJob(props.id)
    router.push({ name: 'jobs' })
}

onMounted(async () => {
    await loadJob()
    pollInterval = setInterval(pollProgress, 5000)
})

onUnmounted(() => {
    if (pollInterval) clearInterval(pollInterval)
})
</script>

<style scoped>
.job-detail-view {
    padding: 20px;
    max-width: 900px;
}
.detail-header {
    display: flex;
    align-items: center;
    gap: 12px;
    margin-bottom: 24px;
}
.status-badge {
    padding: 4px 12px;
    border-radius: 12px;
    font-size: 13px;
    font-weight: bold;
    color: white;
}
.status-badge.idle { background: var(--color-text-maxcontrast); }
.status-badge.running { background: var(--color-primary); }
.status-badge.paused { background: var(--color-warning); }
.status-badge.completed { background: var(--color-success); }
.status-badge.error { background: var(--color-error); }
.detail-grid {
    display: grid;
    grid-template-columns: 1fr 1fr;
    gap: 20px;
    margin-bottom: 24px;
}
.detail-section {
    background: var(--color-background-dark);
    border-radius: 8px;
    padding: 16px;
}
.detail-section h3 {
    margin-bottom: 12px;
}
.detail-section dl {
    display: grid;
    grid-template-columns: auto 1fr;
    gap: 4px 12px;
}
.detail-section dt {
    font-weight: bold;
    color: var(--color-text-maxcontrast);
}
.mono {
    font-family: monospace;
    font-size: 12px;
}
.detail-actions {
    display: flex;
    gap: 8px;
}
.error-alert {
    margin-bottom: 16px;
    padding: 8px 12px;
    background: var(--color-error);
    color: white;
    border-radius: 4px;
}
.loading {
    text-align: center;
    padding: 40px;
}
</style>
