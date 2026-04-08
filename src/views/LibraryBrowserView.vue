<template>
    <div class="library-browser-view">
        <h2>Add Sync Job</h2>

        <!-- Step indicator -->
        <div class="steps">
            <span v-for="s in 4" :key="s" :class="['step', { active: step === s, done: step > s }]">
                {{ s }}
            </span>
        </div>

        <!-- Step 1: Select Tenant -->
        <div v-if="step === 1" class="step-content">
            <h3>Select Azure Tenant</h3>
            <div v-if="tenants.length === 0" class="empty-state">
                <p>No tenants configured. <router-link :to="{ name: 'settings' }">Add a tenant first.</router-link></p>
            </div>
            <div v-else class="tenant-list">
                <div v-for="t in tenants" :key="t.id"
                    :class="['selectable-card', { selected: selectedTenant?.id === t.id }]"
                    @click="selectTenant(t)">
                    <strong>{{ t.name }}</strong>
                    <span class="sub">{{ t.tenantId }}</span>
                </div>
            </div>
            <div class="step-actions">
                <NcButton type="primary" :disabled="!selectedTenant" @click="step = 2">
                    Next
                </NcButton>
            </div>
        </div>

        <!-- Step 2: Browse & Select Library -->
        <div v-if="step === 2" class="step-content">
            <h3>Select Source Library</h3>
            <div class="source-tabs">
                <NcButton :type="sourceTab === 'sites' ? 'primary' : 'secondary'" @click="sourceTab = 'sites'; loadSites()">
                    SharePoint Sites
                </NcButton>
                <NcButton :type="sourceTab === 'users' ? 'primary' : 'secondary'" @click="sourceTab = 'users'; loadUsers()">
                    User OneDrives
                </NcButton>
            </div>

            <LibraryList :items="libraryItems"
                :loading="loadingLibrary"
                @select-drive="selectDrive"
                @expand-item="expandItem" />

            <div class="step-actions">
                <NcButton @click="step = 1">Back</NcButton>
                <NcButton type="primary" :disabled="!selectedDrive" @click="step = 3">
                    Next
                </NcButton>
            </div>
        </div>

        <!-- Step 3: Choose Destination -->
        <div v-if="step === 3" class="step-content">
            <h3>Choose Destination</h3>

            <div class="form-group">
                <label>Destination Type</label>
                <select v-model="destType" class="nc-select">
                    <option value="user_files">User Files</option>
                    <option value="groupfolder">Group Folder</option>
                    <option value="external">External Storage</option>
                </select>
            </div>

            <div class="form-group">
                <label>Destination User (owner)</label>
                <NcTextField v-model="destUser" placeholder="admin" />
            </div>

            <div class="form-group">
                <label>Destination Path</label>
                <div class="dest-picker">
                    <div class="dest-toolbar">
                        <NcButton :disabled="!destUser || destBrowsing" @click="loadDestRoot">
                            {{ destEntries.length || destBrowseError ? 'Refresh' : 'Browse' }}
                        </NcButton>
                        <span class="dest-breadcrumbs">
                            <a href="#" @click.prevent="navigateDest('/')">~</a>
                            <template v-for="(seg, i) in destCrumbs" :key="i">
                                <span>/</span>
                                <a href="#" @click.prevent="navigateDest(crumbPath(i))">{{ seg }}</a>
                            </template>
                        </span>
                    </div>
                    <div v-if="destBrowsing" class="dest-loading">Loading…</div>
                    <div v-else-if="destBrowseError" class="error-alert">{{ destBrowseError }}</div>
                    <ul v-else-if="destEntries.length" class="dest-list">
                        <li v-for="e in destEntries" :key="e.path"
                            class="dest-item"
                            @click="navigateDest(e.path)">
                            📁 {{ e.name }}
                        </li>
                    </ul>
                    <div v-else-if="destPath" class="dest-empty">
                        (empty folder — files will be created here)
                    </div>
                    <div class="dest-current">
                        Selected: <code>{{ destPath || '/' }}</code>
                        <NcButton v-if="destPath && destPath !== '/'" @click="destPath = '/'">
                            Reset
                        </NcButton>
                    </div>
                </div>
            </div>

            <div class="form-group">
                <label>Sync Mode</label>
                <select v-model="syncMode" class="nc-select">
                    <option value="copy">Copy (additive, safe)</option>
                    <option value="sync">Sync (mirror, deletes removed files)</option>
                </select>
            </div>

            <div class="form-group">
                <label>Schedule</label>
                <select v-model="schedule" class="nc-select">
                    <option value="manual">Manual</option>
                    <option value="hourly">Hourly</option>
                    <option value="daily">Daily</option>
                    <option value="weekly">Weekly</option>
                </select>
            </div>

            <div class="step-actions">
                <NcButton @click="step = 2">Back</NcButton>
                <NcButton type="primary" :disabled="!destPath || !destUser" @click="step = 4">
                    Next
                </NcButton>
            </div>
        </div>

        <!-- Step 4: Review & Create -->
        <div v-if="step === 4" class="step-content">
            <h3>Review & Create</h3>

            <div class="form-group">
                <label>Job Name</label>
                <NcTextField v-model="jobName" :placeholder="defaultJobName" />
            </div>

            <div class="review-card">
                <dl>
                    <dt>Tenant</dt><dd>{{ selectedTenant?.name }}</dd>
                    <dt>Source</dt><dd>{{ selectedDrive?.name }} ({{ sourceTab === 'sites' ? 'SharePoint' : 'OneDrive' }})</dd>
                    <dt>Destination</dt><dd>{{ destUser }}:{{ destPath }} ({{ destType }})</dd>
                    <dt>Mode</dt><dd>{{ syncMode }}</dd>
                    <dt>Schedule</dt><dd>{{ schedule }}</dd>
                </dl>
            </div>

            <div class="step-actions">
                <NcButton @click="step = 3">Back</NcButton>
                <NcButton type="primary" :disabled="creating" @click="createSyncJob">
                    <template #icon>
                        <span v-if="creating" class="icon-loading-small" />
                    </template>
                    Create Job
                </NcButton>
            </div>

            <div v-if="error" class="error-alert">{{ error }}</div>
        </div>
    </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import NcButton from '@nextcloud/vue/components/NcButton'
import NcTextField from '@nextcloud/vue/components/NcTextField'
import LibraryList from '../components/LibraryList.vue'
import {
    listTenants, listSites, listSiteDrives, listUsers, listUserDrives, createJob,
    browseDestination,
} from '../services/api.js'

const router = useRouter()

const step = ref(1)
const tenants = ref([])
const selectedTenant = ref(null)
const sourceTab = ref('sites')
const libraryItems = ref([])
const loadingLibrary = ref(false)
const selectedDrive = ref(null)
const destType = ref('user_files')
const destPath = ref('')
const destUser = ref('')
const syncMode = ref('copy')
const schedule = ref('manual')
const jobName = ref('')
const creating = ref(false)
const error = ref('')

// Destination browser state
const destEntries = ref([])
const destBrowsing = ref(false)
const destBrowseError = ref('')
const destCrumbs = computed(() =>
    destPath.value && destPath.value !== '/'
        ? destPath.value.split('/').filter(Boolean)
        : [],
)
function crumbPath(i) {
    return '/' + destCrumbs.value.slice(0, i + 1).join('/')
}
async function loadDestRoot() {
    destPath.value = '/'
    await navigateDest('/')
}
async function navigateDest(path) {
    if (!destUser.value) {
        destBrowseError.value = 'Enter a destination user first'
        return
    }
    destBrowsing.value = true
    destBrowseError.value = ''
    try {
        const res = await browseDestination(destUser.value, path)
        destPath.value = res.data.path
        destEntries.value = res.data.entries
    } catch (e) {
        destBrowseError.value = e.response?.data?.detail || 'Failed to browse destination'
        destEntries.value = []
    } finally {
        destBrowsing.value = false
    }
}

const defaultJobName = computed(() => {
    if (selectedDrive.value) {
        return `Sync ${selectedDrive.value.name}`
    }
    return 'New Sync Job'
})

function selectTenant(t) {
    selectedTenant.value = t
}

async function loadSites() {
    if (!selectedTenant.value) return
    loadingLibrary.value = true
    try {
        const res = await listSites(selectedTenant.value.id)
        libraryItems.value = res.data.map(site => ({
            id: site.id,
            name: site.displayName || site.name,
            type: 'site',
            children: null,
        }))
    } catch (e) {
        error.value = 'Failed to load sites'
    } finally {
        loadingLibrary.value = false
    }
}

async function loadUsers() {
    if (!selectedTenant.value) return
    loadingLibrary.value = true
    try {
        const res = await listUsers(selectedTenant.value.id)
        libraryItems.value = res.data.map(user => ({
            id: user.id,
            name: user.displayName || user.userPrincipalName,
            type: 'user',
            children: null,
        }))
    } catch (e) {
        error.value = 'Failed to load users'
    } finally {
        loadingLibrary.value = false
    }
}

async function expandItem(item) {
    if (item.children !== null) return
    try {
        let res
        if (item.type === 'site') {
            res = await listSiteDrives(selectedTenant.value.id, item.id)
        } else if (item.type === 'user') {
            res = await listUserDrives(selectedTenant.value.id, item.id)
        }
        item.children = (res?.data || []).map(drive => ({
            id: drive.id,
            name: drive.name,
            type: 'drive',
            parentId: item.id,
            parentType: item.type,
        }))
    } catch (e) {
        error.value = 'Failed to load drives'
    }
}

function selectDrive(drive, parent) {
    selectedDrive.value = {
        ...drive,
        siteId: parent?.type === 'site' ? parent.id : null,
    }
}

async function createSyncJob() {
    creating.value = true
    error.value = ''
    try {
        await createJob({
            tenantId: selectedTenant.value.id,
            name: jobName.value || defaultJobName.value,
            sourceType: selectedDrive.value.parentType === 'site' ? 'sharepoint' : 'onedrive',
            sourceSiteId: selectedDrive.value.siteId,
            sourceDriveId: selectedDrive.value.id,
            sourceDriveName: selectedDrive.value.name,
            destType: destType.value,
            destPath: destPath.value,
            destUser: destUser.value,
            syncMode: syncMode.value,
            schedule: schedule.value,
        })
        router.push({ name: 'jobs' })
    } catch (e) {
        error.value = e.response?.data?.error || 'Failed to create job'
    } finally {
        creating.value = false
    }
}

onMounted(async () => {
    try {
        const res = await listTenants()
        tenants.value = res.data
    } catch (e) {
        error.value = 'Failed to load tenants'
    }
})
</script>

<style scoped>
.library-browser-view {
    padding: 20px;
    max-width: 800px;
}
.steps {
    display: flex;
    gap: 8px;
    margin-bottom: 24px;
}
.step {
    width: 32px;
    height: 32px;
    border-radius: 50%;
    display: flex;
    align-items: center;
    justify-content: center;
    background: var(--color-background-dark);
    font-weight: bold;
}
.step.active {
    background: var(--color-primary);
    color: white;
}
.step.done {
    background: var(--color-success);
    color: white;
}
.step-content {
    margin-bottom: 24px;
}
.step-actions {
    display: flex;
    gap: 8px;
    margin-top: 16px;
}
.source-tabs {
    display: flex;
    gap: 8px;
    margin-bottom: 16px;
}
.selectable-card {
    background: var(--color-background-dark);
    border: 2px solid transparent;
    border-radius: 8px;
    padding: 12px;
    margin-bottom: 8px;
    cursor: pointer;
}
.selectable-card:hover {
    border-color: var(--color-primary-element-light);
}
.selectable-card.selected {
    border-color: var(--color-primary);
}
.selectable-card .sub {
    display: block;
    font-size: 12px;
    color: var(--color-text-maxcontrast);
}
.tenant-list {
    margin-bottom: 16px;
}
.form-group {
    margin-bottom: 12px;
}
.form-group label {
    display: block;
    margin-bottom: 4px;
    font-weight: bold;
}
.nc-select {
    width: 100%;
    padding: 8px;
    border-radius: 4px;
    border: 1px solid var(--color-border-dark);
    background: var(--color-main-background);
}
.review-card {
    background: var(--color-background-dark);
    border-radius: 8px;
    padding: 16px;
    margin: 16px 0;
}
.review-card dl {
    display: grid;
    grid-template-columns: 120px 1fr;
    gap: 8px;
}
.review-card dt {
    font-weight: bold;
    color: var(--color-text-maxcontrast);
}
.empty-state {
    text-align: center;
    padding: 40px;
    color: var(--color-text-maxcontrast);
}
.dest-picker {
    border: 1px solid var(--color-border, #ddd);
    border-radius: 6px;
    padding: 8px;
    background: var(--color-main-background, #fff);
}
.dest-toolbar {
    display: flex;
    align-items: center;
    gap: 8px;
    margin-bottom: 8px;
}
.dest-breadcrumbs {
    font-family: monospace;
    font-size: 13px;
}
.dest-breadcrumbs a {
    color: var(--color-primary, #5186D7);
    text-decoration: none;
}
.dest-breadcrumbs a:hover {
    text-decoration: underline;
}
.dest-list {
    list-style: none;
    margin: 0 0 8px 0;
    padding: 0;
    max-height: 240px;
    overflow: auto;
    border: 1px solid var(--color-border, #eee);
    border-radius: 4px;
}
.dest-item {
    padding: 6px 10px;
    cursor: pointer;
}
.dest-item:hover {
    background: var(--color-background-hover, #f5f5f5);
}
.dest-loading, .dest-empty {
    padding: 8px;
    color: var(--color-text-maxcontrast, #777);
    font-size: 13px;
}
.dest-current {
    display: flex;
    align-items: center;
    gap: 8px;
    font-size: 13px;
    padding-top: 4px;
    border-top: 1px dashed var(--color-border, #eee);
}
.error-alert {
    margin-top: 12px;
    padding: 8px;
    background: var(--color-error);
    color: white;
    border-radius: 4px;
}
</style>
