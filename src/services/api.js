import axios from '@nextcloud/axios'

// ExApp: the bundle is loaded into the Nextcloud-rendered page, so
// requests must go through AppAPI's proxy to reach the ExApp container.
// OC.generateUrl() yields the correct /index.php/apps/... prefix for the
// running Nextcloud install.
const ocGenerate = (typeof window !== 'undefined' && window.OC && window.OC.generateUrl)
    ? window.OC.generateUrl
    : (path) => path
const baseUrl = ocGenerate('/apps/app_api/proxy/ms365sync/api/v1')

// --- Tenants ---
export function listTenants() {
    return axios.get(`${baseUrl}/settings/tenants`)
}
export function createTenant(data) {
    return axios.post(`${baseUrl}/settings/tenants`, data)
}
export function updateTenant(id, data) {
    return axios.put(`${baseUrl}/settings/tenants/${id}`, data)
}
export function deleteTenant(id) {
    return axios.delete(`${baseUrl}/settings/tenants/${id}`)
}
export function testTenantConnection(id) {
    return axios.post(`${baseUrl}/settings/tenants/${id}/test`)
}

// --- Container Config ---
export function getContainerConfig() {
    return axios.get(`${baseUrl}/settings/container`)
}
export function setContainerConfig(url, nextcloudUrl) {
    return axios.put(`${baseUrl}/settings/container`, { url, nextcloudUrl })
}

// --- App Passwords (per WebDAV destination user) ---
export function listAppPasswords() {
    return axios.get(`${baseUrl}/settings/app-passwords`)
}
export function setAppPassword(user, password) {
    return axios.put(`${baseUrl}/settings/app-passwords`, { user, password })
}
export function deleteAppPassword(user) {
    return axios.delete(`${baseUrl}/settings/app-passwords/${encodeURIComponent(user)}`)
}

// --- Libraries ---
export function listMyDrives(tenantId, userId) {
    return axios.get(`${baseUrl}/libraries/${tenantId}/me/drives`, { params: { userId } })
}
export function listSites(tenantId) {
    return axios.get(`${baseUrl}/libraries/${tenantId}/sites`)
}
export function listSiteDrives(tenantId, siteId) {
    return axios.get(`${baseUrl}/libraries/${tenantId}/sites/${siteId}/drives`)
}
export function listUsers(tenantId) {
    return axios.get(`${baseUrl}/libraries/${tenantId}/users`)
}
export function listUserDrives(tenantId, userId) {
    return axios.get(`${baseUrl}/libraries/${tenantId}/users/${userId}/drives`)
}

// --- Destinations (Nextcloud user file tree via WebDAV) ---
export function browseDestination(user, path = '/') {
    return axios.get(`${baseUrl}/destinations/${encodeURIComponent(user)}/browse`, {
        params: { path },
    })
}

// --- Jobs ---
export function listJobs() {
    return axios.get(`${baseUrl}/jobs`)
}
export function getJob(id) {
    return axios.get(`${baseUrl}/jobs/${id}`)
}
export function createJob(data) {
    return axios.post(`${baseUrl}/jobs`, data)
}
export function updateJob(id, data) {
    return axios.put(`${baseUrl}/jobs/${id}`, data)
}
export function deleteJob(id) {
    return axios.delete(`${baseUrl}/jobs/${id}`)
}
export function startJob(id) {
    return axios.post(`${baseUrl}/jobs/${id}/start`)
}
export function stopJob(id) {
    return axios.post(`${baseUrl}/jobs/${id}/stop`)
}
export function getJobProgress(id) {
    return axios.get(`${baseUrl}/jobs/${id}/progress`)
}

// --- Logs ---
export function getJobLog(jobId) {
    return axios.get(`${baseUrl}/logs/${jobId}`)
}
export function tailJobLog(jobId, lines = 50) {
    return axios.get(`${baseUrl}/logs/${jobId}/tail`, { params: { lines } })
}
