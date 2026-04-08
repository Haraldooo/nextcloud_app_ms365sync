<template>
    <NcContent app-name="ms365sync">
        <NcAppNavigation>
            <template #list>
                <NcAppNavigationItem name="Sync Jobs" :to="{ name: 'jobs' }" />
                <NcAppNavigationItem name="Add Job" :to="{ name: 'add-job' }" />
                <NcAppNavigationItem name="Settings" :to="{ name: 'settings' }" />
            </template>
        </NcAppNavigation>
        <NcAppContent>
            <router-view />
        </NcAppContent>
    </NcContent>
</template>

<script setup>
// Standard Nextcloud app layout: NcContent wraps a left NcAppNavigation
// (translucent sidebar) and the main NcAppContent area, mirroring the
// shell used by Notes, Tasks, Mail, Calendar, etc.
import NcContent from '@nextcloud/vue/components/NcContent'
import NcAppNavigation from '@nextcloud/vue/components/NcAppNavigation'
import NcAppNavigationItem from '@nextcloud/vue/components/NcAppNavigationItem'
import NcAppContent from '@nextcloud/vue/components/NcAppContent'
</script>
