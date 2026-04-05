import { createRouter, createWebHashHistory } from 'vue-router'
import SettingsView from './views/SettingsView.vue'
import JobsView from './views/JobsView.vue'
import JobDetailView from './views/JobDetailView.vue'
import LibraryBrowserView from './views/LibraryBrowserView.vue'
import LogView from './views/LogView.vue'

const routes = [
    { path: '/', redirect: '/jobs' },
    { path: '/settings', name: 'settings', component: SettingsView },
    { path: '/jobs', name: 'jobs', component: JobsView },
    { path: '/jobs/:id', name: 'job-detail', component: JobDetailView, props: true },
    { path: '/add-job', name: 'add-job', component: LibraryBrowserView },
    { path: '/logs/:jobId', name: 'logs', component: LogView, props: true },
]

export default createRouter({
    history: createWebHashHistory(),
    routes,
})
