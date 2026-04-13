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

            <div v-if="selectedDrive" class="selected-source-banner">
                <span class="selected-source-label">Selected source</span>
                <strong class="selected-source-name">{{ selectedDrive.name }}</strong>
                <span class="selected-source-meta">
                    {{ selectedDrive.parentType === 'site' ? 'SharePoint site' : 'OneDrive' }}
                </span>
            </div>
            <div v-else class="selected-source-banner empty">
                No source selected yet — pick a drive above.
            </div>

            <!-- Folder selection within selected drive -->
            <div v-if="selectedDrive" class="folder-selector">
                <div class="folder-selector-header">
                    <label class="folder-toggle">
                        <input type="checkbox" v-model="syncEntireDrive" />
                        Sync entire library
                    </label>
                </div>

                <div v-if="!syncEntireDrive" class="folder-browser">
                    <div class="folder-breadcrumbs">
                        <a href="#" @click.prevent="browseFolderRoot">Root</a>
                        <template v-for="(crumb, i) in folderCrumbs" :key="i">
                            <span> / </span>
                            <a href="#" @click.prevent="navigateToFolderCrumb(i)">{{ crumb.name }}</a>
                        </template>
                    </div>
                    <div v-if="loadingFolders" class="folder-loading">Loading folders...</div>
                    <div v-else-if="folderItems.length === 0" class="folder-empty">
                        No subfolders found at this level.
                    </div>
                    <ul v-else class="folder-list">
                        <li v-for="folder in folderItems" :key="folder.id" class="folder-item">
                            <label class="folder-check">
                                <input type="checkbox"
                                    :checked="isFolderSelected(folder)"
                                    @change="toggleFolder(folder)" />
                                <span class="folder-icon">&#128194;</span>
                                {{ folder.name }}
                            </label>
                            <NcButton type="tertiary" @click.stop="drillIntoFolder(folder)">
                                &#9654;
                            </NcButton>
                        </li>
                    </ul>
                    <div v-if="selectedFolders.length" class="folder-selection-summary">
                        {{ selectedFolders.length }} folder(s) selected
                        — {{ selectedFolders.length > 1 ? selectedFolders.length + ' jobs' : '1 job' }} will be created.
                        <ul class="selected-folders-list">
                            <li v-for="f in selectedFolders" :key="f.path">
                                <code>{{ f.path }}</code>
                                <a href="#" class="remove-folder" @click.prevent="removeFolder(f)">&#10005;</a>
                            </li>
                        </ul>
                    </div>
                    <div v-else class="folder-selection-summary empty">
                        Select one or more folders above, or check "Sync entire library".
                    </div>
                </div>
            </div>

            <div class="step-actions">
                <NcButton @click="step = 1">Back</NcButton>
                <NcButton type="primary"
                    :disabled="!selectedDrive || (!syncEntireDrive && selectedFolders.length === 0)"
                    @click="step = 3">
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
                <select v-model="destUser" class="nc-select" :disabled="loadingUsers">
                    <option value="">{{ loadingUsers ? 'Loading users…' : '— Select a user —' }}</option>
                    <option v-for="u in ncUsers" :key="u.id" :value="u.id">
                        {{ u.id }}{{ u.hasAppPassword ? '' : ' (no app password)' }}
                    </option>
                </select>
                <p v-if="destUser && !selectedUserHasPassword" class="hint warning">
                    No app password is configured for <code>{{ destUser }}</code>. Add one in
                    Settings → WebDAV App Passwords before starting the job.
                </p>
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
                    <template v-if="!syncEntireDrive">
                        <dt>Folder(s)</dt>
                        <dd>
                            <ul class="review-folders">
                                <li v-for="f in selectedFolders" :key="f.path"><code>{{ f.path }}</code></li>
                            </ul>
                        </dd>
                    </template>
                    <template v-else>
                        <dt>Scope</dt>
                        <dd>Entire library</dd>
                    </template>
                    <dt>Destination</dt><dd>{{ destUser }}:{{ destPath }} ({{ destType }})</dd>
                    <dt>Mode</dt><dd>{{ syncMode }}</dd>
                    <dt>Schedule</dt><dd>{{ schedule }}</dd>
                </dl>
            </div>

            <p v-if="!syncEntireDrive && selectedFolders.length > 1" class="multi-job-hint">
                {{ selectedFolders.length }} separate jobs will be created, one per selected folder.
            </p>

            <div class="step-actions">
                <NcButton @click="step = 3">Back</NcButton>
                <NcButton type="primary" :disabled="creating" @click="createSyncJob">
                    <template #icon>
                        <span v-if="creating" class="icon-loading-small" />
                    </template>
                    {{ !syncEntireDrive && selectedFolders.length > 1 ? `Create ${selectedFolders.length} Jobs` : 'Create Job' }}
                </NcButton>
            </div>

            <div v-if="error" class="error-alert">{{ error }}</div>
        </div>
    </div>
</template>

<script setup>
import { ref, computed, watch, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import NcButton from '@nextcloud/vue/components/NcButton'
import NcTextField from '@nextcloud/vue/components/NcTextField'
import LibraryList from '../components/LibraryList.vue'
import {
    listTenants, listSites, listSiteDrives, listUsers, listUserDrives, createJob,
    browseDestination, listNextcloudUsers, listDriveFolders,
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
const ncUsers = ref([])
const loadingUsers = ref(false)
const selectedUserHasPassword = computed(() => {
    const u = ncUsers.value.find(x => x.id === destUser.value)
    return !!u && u.hasAppPassword
})
const syncMode = ref('copy')
const schedule = ref('manual')

// Folder selection state
const syncEntireDrive = ref(true)
const folderItems = ref([])
const loadingFolders = ref(false)
const selectedFolders = ref([])  // [{id, name, path}]
const folderCrumbs = ref([])     // [{id, name}] breadcrumb trail
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
    // Reset folder selection when drive changes
    syncEntireDrive.value = true
    selectedFolders.value = []
    folderCrumbs.value = []
    folderItems.value = []
}

// ---- Folder browsing ----

async function loadFolders(itemId = '') {
    if (!selectedTenant.value || !selectedDrive.value) return
    loadingFolders.value = true
    try {
        const res = await listDriveFolders(
            selectedTenant.value.id,
            selectedDrive.value.id,
            itemId,
        )
        folderItems.value = (res.data || []).map(f => ({
            id: f.id,
            name: f.name,
            path: folderCrumbs.value.map(c => c.name).concat(f.name).join('/'),
        }))
    } catch (e) {
        folderItems.value = []
    } finally {
        loadingFolders.value = false
    }
}

function browseFolderRoot() {
    folderCrumbs.value = []
    loadFolders()
}

function drillIntoFolder(folder) {
    folderCrumbs.value.push({ id: folder.id, name: folder.name })
    loadFolders(folder.id)
}

function navigateToFolderCrumb(index) {
    const crumb = folderCrumbs.value[index]
    folderCrumbs.value = folderCrumbs.value.slice(0, index + 1)
    loadFolders(crumb.id)
}

function isFolderSelected(folder) {
    return selectedFolders.value.some(f => f.id === folder.id)
}

function toggleFolder(folder) {
    if (isFolderSelected(folder)) {
        selectedFolders.value = selectedFolders.value.filter(f => f.id !== folder.id)
    } else {
        selectedFolders.value.push({ id: folder.id, name: folder.name, path: folder.path })
    }
}

function removeFolder(folder) {
    selectedFolders.value = selectedFolders.value.filter(f => f.id !== folder.id)
}

watch(syncEntireDrive, (val) => {
    if (!val && folderItems.value.length === 0) {
        browseFolderRoot()
    }
})

async function createSyncJob() {
    creating.value = true
    error.value = ''
    try {
        const basePayload = {
            tenantId: selectedTenant.value.id,
            sourceType: selectedDrive.value.parentType === 'site' ? 'sharepoint' : 'onedrive',
            sourceSiteId: selectedDrive.value.siteId,
            sourceDriveId: selectedDrive.value.id,
            sourceDriveName: selectedDrive.value.name,
            destType: destType.value,
            destPath: destPath.value,
            destUser: destUser.value,
            syncMode: syncMode.value,
            schedule: schedule.value,
        }

        if (syncEntireDrive.value || selectedFolders.value.length === 0) {
            // Single job for the entire drive
            await createJob({
                ...basePayload,
                name: jobName.value || defaultJobName.value,
                sourcePath: '',
            })
        } else {
            // One job per selected folder
            for (const folder of selectedFolders.value) {
                const name = selectedFolders.value.length === 1
                    ? (jobName.value || `Sync ${selectedDrive.value.name}/${folder.name}`)
                    : `Sync ${selectedDrive.value.name}/${folder.name}`
                await createJob({
                    ...basePayload,
                    name,
                    sourcePath: folder.path,
                })
            }
        }
        router.push({ name: 'jobs' })
    } catch (e) {
        error.value = e.response?.data?.detail || e.response?.data?.error || 'Failed to create job'
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
    loadingUsers.value = true
    try {
        const res = await listNextcloudUsers()
        ncUsers.value = res.data
    } catch (e) {
        // Non-fatal: the dropdown will simply be empty.
    } finally {
        loadingUsers.value = false
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
.hint {
    margin-top: 6px;
    font-size: 12px;
    color: var(--color-text-maxcontrast);
}
.hint.warning {
    color: var(--color-warning);
}
.hint code {
    background: var(--color-background-dark);
    padding: 1px 4px;
    border-radius: 3px;
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
.selected-source-banner {
    position: sticky;
    bottom: 0;
    margin-top: 16px;
    padding: 12px 16px;
    border-radius: 8px;
    background: var(--color-primary-element-light, #e7f1fb);
    border: 2px solid var(--color-primary, #5186D7);
    display: flex;
    align-items: center;
    gap: 12px;
    flex-wrap: wrap;
}
.selected-source-banner.empty {
    background: var(--color-background-dark);
    border: 1px dashed var(--color-border, #ddd);
    color: var(--color-text-maxcontrast);
    font-size: 13px;
}
.selected-source-label {
    text-transform: uppercase;
    font-size: 11px;
    font-weight: bold;
    letter-spacing: 0.5px;
    color: var(--color-primary, #5186D7);
}
.selected-source-name {
    font-size: 16px;
}
.selected-source-meta {
    font-size: 12px;
    color: var(--color-text-maxcontrast);
}
.error-alert {
    margin-top: 12px;
    padding: 8px;
    background: var(--color-error);
    color: white;
    border-radius: 4px;
}
.folder-selector {
    margin-top: 16px;
    border: 1px solid var(--color-border, #ddd);
    border-radius: 8px;
    padding: 12px;
    background: var(--color-main-background, #fff);
}
.folder-selector-header {
    margin-bottom: 8px;
}
.folder-toggle {
    display: flex;
    align-items: center;
    gap: 8px;
    font-weight: 500;
    cursor: pointer;
}
.folder-toggle input {
    width: 16px;
    height: 16px;
}
.folder-browser {
    margin-top: 8px;
}
.folder-breadcrumbs {
    font-family: monospace;
    font-size: 13px;
    margin-bottom: 8px;
    padding: 4px 0;
}
.folder-breadcrumbs a {
    color: var(--color-primary, #5186D7);
    text-decoration: none;
}
.folder-breadcrumbs a:hover {
    text-decoration: underline;
}
.folder-list {
    list-style: none;
    margin: 0;
    padding: 0;
    max-height: 240px;
    overflow-y: auto;
    border: 1px solid var(--color-border, #eee);
    border-radius: 4px;
}
.folder-item {
    display: flex;
    align-items: center;
    justify-content: space-between;
    padding: 6px 10px;
    border-bottom: 1px solid var(--color-border, #eee);
}
.folder-item:last-child {
    border-bottom: none;
}
.folder-item:hover {
    background: var(--color-background-hover, #f5f5f5);
}
.folder-check {
    display: flex;
    align-items: center;
    gap: 6px;
    cursor: pointer;
    flex: 1;
}
.folder-check input {
    width: 16px;
    height: 16px;
}
.folder-icon {
    flex-shrink: 0;
}
.folder-loading, .folder-empty {
    padding: 12px;
    color: var(--color-text-maxcontrast, #777);
    font-size: 13px;
    text-align: center;
}
.folder-selection-summary {
    margin-top: 8px;
    padding: 8px 12px;
    background: var(--color-primary-element-light, #e7f1fb);
    border-radius: 6px;
    font-size: 13px;
}
.folder-selection-summary.empty {
    background: var(--color-background-dark);
    color: var(--color-text-maxcontrast);
}
.selected-folders-list {
    list-style: none;
    margin: 6px 0 0 0;
    padding: 0;
}
.selected-folders-list li {
    display: flex;
    align-items: center;
    gap: 6px;
    padding: 2px 0;
}
.selected-folders-list code {
    background: var(--color-background-dark);
    padding: 1px 4px;
    border-radius: 3px;
    font-size: 12px;
}
.remove-folder {
    color: var(--color-error);
    text-decoration: none;
    font-size: 14px;
}
.review-folders {
    list-style: none;
    margin: 0;
    padding: 0;
}
.review-folders code {
    background: var(--color-background-dark);
    padding: 1px 4px;
    border-radius: 3px;
    font-size: 12px;
}
.multi-job-hint {
    font-size: 13px;
    color: var(--color-text-maxcontrast);
    margin: 8px 0;
}
</style>
