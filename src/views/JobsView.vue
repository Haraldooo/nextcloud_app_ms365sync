<template>
    <div class="jobs-view">
        <div class="jobs-header">
            <h2>Sync Jobs</h2>
            <NcButton type="primary" :to="{ name: 'add-job' }">
                Add Job
            </NcButton>
        </div>

        <div v-if="loading" class="loading">
            <span class="icon-loading" />
        </div>

        <div v-else-if="jobs.length === 0" class="empty-state">
            <p>No sync jobs configured yet.</p>
            <NcButton type="primary" :to="{ name: 'add-job' }">
                Create your first sync job
            </NcButton>
        </div>

        <div v-else class="jobs-list">
            <JobCard v-for="job in jobs"
                :key="job.id"
                :job="job"
                @start="onStart"
                @stop="onStop"
                @delete="onDelete" />
        </div>

        <div v-if="error" class="error-alert">{{ error }}</div>
    </div>
</template>

<script setup>
import { ref, onMounted, onUnmounted } from 'vue'
import NcButton from '@nextcloud/vue/dist/Components/NcButton.js'
import JobCard from '../components/JobCard.vue'
import { listJobs, startJob, stopJob, deleteJob, getJobProgress } from '../services/api.js'

const jobs = ref([])
const loading = ref(true)
const error = ref('')
let pollInterval = null

async function loadJobs() {
    try {
        const res = await listJobs()
        jobs.value = res.data
    } catch (e) {
        error.value = 'Failed to load jobs'
    } finally {
        loading.value = false
    }
}

async function pollRunningJobs() {
    const running = jobs.value.filter(j => j.status === 'running')
    for (const job of running) {
        try {
            const res = await getJobProgress(job.id)
            Object.assign(job, res.data)
        } catch (e) {
            // ignore polling errors
        }
    }
}

async function onStart(job) {
    try {
        error.value = ''
        const res = await startJob(job.id)
        Object.assign(job, res.data)
    } catch (e) {
        error.value = e.response?.data?.error || 'Failed to start job'
    }
}

async function onStop(job) {
    try {
        error.value = ''
        const res = await stopJob(job.id)
        Object.assign(job, res.data)
    } catch (e) {
        error.value = e.response?.data?.error || 'Failed to stop job'
    }
}

async function onDelete(job) {
    if (!confirm(`Delete sync job "${job.name}"?`)) return
    try {
        await deleteJob(job.id)
        jobs.value = jobs.value.filter(j => j.id !== job.id)
    } catch (e) {
        error.value = 'Failed to delete job'
    }
}

onMounted(async () => {
    await loadJobs()
    pollInterval = setInterval(pollRunningJobs, 10000)
})

onUnmounted(() => {
    if (pollInterval) clearInterval(pollInterval)
})
</script>

<style scoped>
.jobs-view {
    padding: 20px;
}
.jobs-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 20px;
}
.jobs-list {
    display: flex;
    flex-direction: column;
    gap: 12px;
}
.empty-state {
    text-align: center;
    padding: 60px 20px;
    color: var(--color-text-maxcontrast);
}
.loading {
    text-align: center;
    padding: 40px;
}
.error-alert {
    margin-top: 12px;
    padding: 8px;
    background: var(--color-error);
    color: white;
    border-radius: 4px;
}
</style>
