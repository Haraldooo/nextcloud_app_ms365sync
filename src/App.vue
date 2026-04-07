<template>
    <div class="ms365sync-app">
        <nav class="ms365sync-tabs">
            <router-link :to="{ name: 'jobs' }" class="ms365sync-tab" active-class="is-active">
                Sync Jobs
            </router-link>
            <router-link :to="{ name: 'add-job' }" class="ms365sync-tab" active-class="is-active">
                Add Job
            </router-link>
            <router-link :to="{ name: 'settings' }" class="ms365sync-tab" active-class="is-active">
                Settings
            </router-link>
        </nav>
        <div class="ms365sync-content">
            <router-view />
        </div>
    </div>
</template>

<script setup>
// The bundle is injected into Nextcloud's already-rendered page (which
// already provides NcContent / NcAppNavigation / NcAppContent), so this
// component renders only the inner view content + a tab strip. Wrapping
// the app in NcContent here would nest Nextcloud's chrome inside itself.
</script>

<style scoped>
.ms365sync-app {
    display: flex;
    flex-direction: column;
    height: 100%;
    min-height: 0;
}
.ms365sync-tabs {
    display: flex;
    gap: 4px;
    padding: 8px 16px 0 16px;
    border-bottom: 1px solid var(--color-border, #ddd);
    flex-shrink: 0;
}
.ms365sync-tab {
    padding: 8px 16px;
    border-radius: 8px 8px 0 0;
    color: var(--color-text-maxcontrast, #555);
    text-decoration: none;
    font-weight: 500;
}
.ms365sync-tab:hover {
    background: var(--color-background-hover, #f5f5f5);
}
.ms365sync-tab.is-active {
    background: var(--color-main-background, #fff);
    color: var(--color-main-text, #000);
    border: 1px solid var(--color-border, #ddd);
    border-bottom: 1px solid var(--color-main-background, #fff);
    margin-bottom: -1px;
}
.ms365sync-content {
    flex: 1 1 auto;
    min-height: 0;
    overflow: auto;
}
</style>
