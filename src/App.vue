<template>
    <NcContent app-name="ms365sync">
        <NcAppNavigation>
            <template #list>
                <NcAppNavigationItem :to="{ name: 'jobs' }" name="Sync Jobs" :active="$route.name === 'jobs'">
                    <template #icon>
                        <IconSync :size="20" />
                    </template>
                </NcAppNavigationItem>
                <NcAppNavigationItem :to="{ name: 'add-job' }" name="Add Job" :active="$route.name === 'add-job'">
                    <template #icon>
                        <IconPlus :size="20" />
                    </template>
                </NcAppNavigationItem>
                <NcAppNavigationItem :to="{ name: 'settings' }" name="Settings" :active="$route.name === 'settings'">
                    <template #icon>
                        <IconCog :size="20" />
                    </template>
                </NcAppNavigationItem>
            </template>
        </NcAppNavigation>
        <NcAppContent>
            <router-view />
        </NcAppContent>
    </NcContent>
</template>

<script setup>
import NcContent from '@nextcloud/vue/components/NcContent'
import NcAppNavigation from '@nextcloud/vue/components/NcAppNavigation'
import NcAppNavigationItem from '@nextcloud/vue/components/NcAppNavigationItem'
import NcAppContent from '@nextcloud/vue/components/NcAppContent'

// Simple inline SVG icon components
import { h } from 'vue'

const IconSync = { render: () => h('span', { class: 'icon-sync' }) }
const IconPlus = { render: () => h('span', { class: 'icon-add' }) }
const IconCog = { render: () => h('span', { class: 'icon-settings' }) }
</script>
