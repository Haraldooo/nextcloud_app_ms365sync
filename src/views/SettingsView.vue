<template>
    <div class="settings-view">
        <h2>MS365 Sync Settings</h2>

        <!-- Connection Settings -->
        <div class="section">
            <h3>Connection</h3>
            <div class="form-group">
                <label for="nextcloud-url">Nextcloud URL (external, as seen by the container)</label>
                <NcTextField id="nextcloud-url"
                    v-model="nextcloudUrl"
                    placeholder="https://cloud.example.com"
                    :disabled="savingContainer" />
            </div>
            <div class="form-group">
                <label for="container-url">Rclone Container URL</label>
                <NcTextField id="container-url"
                    v-model="containerUrl"
                    placeholder="http://localhost:8080"
                    :disabled="savingContainer" />
            </div>
            <NcButton type="primary"
                :disabled="savingContainer"
                @click="saveContainerUrl">
                <template #icon>
                    <span v-if="savingContainer" class="icon-loading-small" />
                </template>
                Save
            </NcButton>
        </div>

        <!-- App Passwords -->
        <div class="section">
            <h3>WebDAV App Passwords</h3>
            <p class="hint">
                Each sync job writes to a Nextcloud user's WebDAV root and needs an app password for that user.
                Generate one in Nextcloud (Personal Settings → Security → Devices &amp; sessions) and store it here.
            </p>
            <div v-for="entry in appPasswords" :key="entry.user" class="tenant-card">
                <div class="tenant-header">
                    <strong>{{ entry.user }}</strong>
                    <NcButton type="error" @click="removeAppPassword(entry.user)">Delete</NcButton>
                </div>
            </div>
            <div class="add-tenant-form">
                <h4>Add / Update App Password</h4>
                <div class="form-group">
                    <label>Nextcloud User ID</label>
                    <NcTextField v-model="appPwForm.user" placeholder="alice" />
                </div>
                <div class="form-group">
                    <label>App Password</label>
                    <NcTextField v-model="appPwForm.password" type="password" placeholder="Enter app password" />
                </div>
                <div class="form-actions">
                    <NcButton type="primary" :disabled="savingAppPw" @click="saveAppPassword">
                        <template #icon>
                            <span v-if="savingAppPw" class="icon-loading-small" />
                        </template>
                        Save
                    </NcButton>
                </div>
                <div v-if="appPwError" class="error-alert">{{ appPwError }}</div>
            </div>
        </div>

        <!-- Azure Tenants -->
        <div class="section">
            <h3>Azure AD Tenants</h3>

            <div v-for="tenant in tenants" :key="tenant.id" class="tenant-card">
                <div class="tenant-header">
                    <strong>{{ tenant.name }}</strong>
                    <span :class="['status-badge', tenant.status]">{{ tenant.status }}</span>
                </div>
                <div class="tenant-details">
                    <span>Tenant ID: {{ tenant.tenantId }}</span>
                    <span>Client ID: {{ tenant.clientId }}</span>
                </div>
                <div class="tenant-actions">
                    <NcButton type="secondary" @click="testTenant(tenant)">
                        <template #icon>
                            <span v-if="testingId === tenant.id" class="icon-loading-small" />
                        </template>
                        Test Connection
                    </NcButton>
                    <NcButton type="secondary" @click="editTenant(tenant)">Edit</NcButton>
                    <NcButton type="error" @click="removeTenant(tenant)">Delete</NcButton>
                </div>
                <div v-if="testResult && testResult.id === tenant.id" class="test-result" :class="testResult.status">
                    {{ testResult.message }}
                </div>
            </div>

            <!-- Add Tenant Form -->
            <div class="add-tenant-form">
                <h4>{{ editingTenant ? 'Edit Tenant' : 'Add New Tenant' }}</h4>
                <div class="form-group">
                    <label>Display Name</label>
                    <NcTextField v-model="form.name" placeholder="My Organization" />
                </div>
                <div class="form-group">
                    <label>Azure Tenant ID</label>
                    <NcTextField v-model="form.tenantId" placeholder="xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx" />
                </div>
                <div class="form-group">
                    <label>Client ID</label>
                    <NcTextField v-model="form.clientId" placeholder="xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx" />
                </div>
                <div class="form-group">
                    <label>Client Secret</label>
                    <NcTextField v-model="form.clientSecret"
                        type="password"
                        :placeholder="editingTenant ? '(unchanged)' : 'Enter client secret'" />
                </div>
                <div class="form-actions">
                    <NcButton type="primary" :disabled="saving" @click="saveTenant">
                        <template #icon>
                            <span v-if="saving" class="icon-loading-small" />
                        </template>
                        {{ editingTenant ? 'Update' : 'Add Tenant' }}
                    </NcButton>
                    <NcButton v-if="editingTenant" type="secondary" @click="cancelEdit">Cancel</NcButton>
                </div>
                <div v-if="error" class="error-alert">{{ error }}</div>
            </div>
        </div>
    </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import NcButton from '@nextcloud/vue/components/NcButton'
import NcTextField from '@nextcloud/vue/components/NcTextField'
import { showError, getDialogBuilder } from '@nextcloud/dialogs'
import {
    listTenants, createTenant, updateTenant, deleteTenant,
    testTenantConnection, getContainerConfig, setContainerConfig,
    listAppPasswords, setAppPassword, deleteAppPassword,
} from '../services/api.js'

const tenants = ref([])
const containerUrl = ref('')
const nextcloudUrl = ref('')
const savingContainer = ref(false)
const saving = ref(false)
const testingId = ref(null)
const testResult = ref(null)
const error = ref('')
const editingTenant = ref(null)
const appPasswords = ref([])
const appPwForm = ref({ user: '', password: '' })
const savingAppPw = ref(false)
const appPwError = ref('')

const form = ref({
    name: '',
    tenantId: '',
    clientId: '',
    clientSecret: '',
})

async function loadData() {
    try {
        const [tenantsRes, containerRes, appPwRes] = await Promise.all([
            listTenants(),
            getContainerConfig(),
            listAppPasswords(),
        ])
        tenants.value = tenantsRes.data
        containerUrl.value = containerRes.data.url || ''
        nextcloudUrl.value = containerRes.data.nextcloudUrl || ''
        appPasswords.value = appPwRes.data
    } catch (e) {
        error.value = 'Failed to load settings'
    }
}

async function saveAppPassword() {
    if (!appPwForm.value.user || !appPwForm.value.password) {
        appPwError.value = 'User and password are required'
        return
    }
    savingAppPw.value = true
    appPwError.value = ''
    try {
        await setAppPassword(appPwForm.value.user, appPwForm.value.password)
        appPwForm.value = { user: '', password: '' }
        await loadData()
    } catch (e) {
        appPwError.value = e.response?.data?.detail || 'Failed to save app password'
    } finally {
        savingAppPw.value = false
    }
}

async function removeAppPassword(user) {
    try {
        await deleteAppPassword(user)
        await loadData()
    } catch (e) {
        appPwError.value = 'Failed to delete app password'
    }
}

async function saveContainerUrl() {
    savingContainer.value = true
    try {
        await setContainerConfig(containerUrl.value, nextcloudUrl.value)
    } catch (e) {
        error.value = 'Failed to save connection settings'
    } finally {
        savingContainer.value = false
    }
}

async function saveTenant() {
    if (!form.value.name || !form.value.tenantId || !form.value.clientId) {
        error.value = 'Please fill in all required fields'
        return
    }
    if (!editingTenant.value && !form.value.clientSecret) {
        error.value = 'Client secret is required for new tenants'
        return
    }

    saving.value = true
    error.value = ''
    try {
        if (editingTenant.value) {
            await updateTenant(editingTenant.value.id, {
                name: form.value.name,
                tenantId: form.value.tenantId,
                clientId: form.value.clientId,
                clientSecret: form.value.clientSecret || undefined,
            })
        } else {
            await createTenant(form.value)
        }
        resetForm()
        await loadData()
    } catch (e) {
        error.value = e.response?.data?.error || 'Failed to save tenant'
    } finally {
        saving.value = false
    }
}

async function testTenant(tenant) {
    testingId.value = tenant.id
    testResult.value = null
    try {
        const res = await testTenantConnection(tenant.id)
        testResult.value = { id: tenant.id, ...res.data }
        await loadData()
    } catch (e) {
        testResult.value = {
            id: tenant.id,
            status: 'invalid',
            message: e.response?.data?.message || 'Connection test failed',
        }
    } finally {
        testingId.value = null
    }
}

function editTenant(tenant) {
    editingTenant.value = tenant
    form.value = {
        name: tenant.name,
        tenantId: tenant.tenantId,
        clientId: tenant.clientId,
        clientSecret: '',
    }
}

function cancelEdit() {
    editingTenant.value = null
    resetForm()
}

async function confirmDialog(message) {
    return new Promise((resolve) => {
        getDialogBuilder('Confirm')
            .setText(message)
            .setButtons([
                { label: 'Cancel', type: 'secondary', callback: () => resolve(false) },
                { label: 'Delete', type: 'error', callback: () => resolve(true) },
            ])
            .build()
            .show()
    })
}

async function removeTenant(tenant) {
    const ok = await confirmDialog(
        `Delete tenant "${tenant.name}"? This will not delete associated sync jobs.`,
    )
    if (!ok) return
    try {
        await deleteTenant(tenant.id)
        await loadData()
    } catch (e) {
        showError('Failed to delete tenant')
    }
}

function resetForm() {
    editingTenant.value = null
    form.value = { name: '', tenantId: '', clientId: '', clientSecret: '' }
}

onMounted(loadData)
</script>

<style scoped>
.settings-view {
    max-width: 800px;
    margin: 0 auto;
    padding: 20px;
}
.section {
    margin-bottom: 32px;
}
.form-group {
    margin-bottom: 12px;
}
.form-group label {
    display: block;
    margin-bottom: 4px;
    font-weight: bold;
}
.input-row {
    display: flex;
    gap: 8px;
    align-items: center;
}
.tenant-card {
    background: var(--color-background-dark);
    border-radius: 8px;
    padding: 16px;
    margin-bottom: 12px;
}
.tenant-header {
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
}
.status-badge.valid { background: var(--color-success); color: white; }
.status-badge.invalid { background: var(--color-error); color: white; }
.status-badge.unchecked { background: var(--color-warning); color: white; }
.tenant-details {
    display: flex;
    flex-direction: column;
    gap: 4px;
    font-size: 13px;
    color: var(--color-text-maxcontrast);
    margin-bottom: 12px;
}
.tenant-actions {
    display: flex;
    gap: 8px;
}
.test-result {
    margin-top: 8px;
    padding: 8px;
    border-radius: 4px;
}
.test-result.valid { background: var(--color-success); color: white; }
.test-result.invalid { background: var(--color-error); color: white; }
.add-tenant-form {
    background: var(--color-background-dark);
    border-radius: 8px;
    padding: 16px;
    margin-top: 16px;
}
.form-actions {
    display: flex;
    gap: 8px;
    margin-top: 16px;
}
.error-alert {
    margin-top: 12px;
    padding: 8px;
    background: var(--color-error);
    color: white;
    border-radius: 4px;
}
.hint {
    margin-top: 8px;
    font-size: 13px;
    color: var(--color-text-maxcontrast);
}
</style>
