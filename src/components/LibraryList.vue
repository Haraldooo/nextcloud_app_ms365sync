<template>
    <div class="library-list">
        <div v-if="loading" class="loading">
            <span class="icon-loading" />
        </div>
        <div v-else-if="items.length === 0" class="empty">
            No items found.
        </div>
        <div v-else>
            <div v-for="item in items" :key="item.id" class="library-item">
                <div class="library-item-row"
                    :class="{ expandable: item.type !== 'drive' }"
                    @click="toggle(item)">
                    <span class="expand-icon">
                        {{ item.type === 'drive' ? '&#128194;' : (item.expanded ? '&#9660;' : '&#9654;') }}
                    </span>
                    <span class="item-name">{{ item.name }}</span>
                    <span class="item-type">{{ item.type }}</span>
                    <NcButton v-if="item.type === 'drive'"
                        type="primary"
                        @click.stop="$emit('select-drive', item, findParent(item))">
                        Select
                    </NcButton>
                </div>
                <!-- Children (drives under a site/user) -->
                <div v-if="item.expanded && item.children" class="library-children">
                    <div v-for="child in item.children" :key="child.id" class="library-item-row child">
                        <span class="expand-icon">&#128194;</span>
                        <span class="item-name">{{ child.name }}</span>
                        <span class="item-type">drive</span>
                        <NcButton type="primary"
                            @click.stop="$emit('select-drive', child, item)">
                            Select
                        </NcButton>
                    </div>
                    <div v-if="item.children.length === 0" class="empty child">
                        No drives found.
                    </div>
                </div>
                <div v-if="item.expanded && item.children === null" class="loading child">
                    <span class="icon-loading-small" />
                </div>
            </div>
        </div>
    </div>
</template>

<script setup>
import NcButton from '@nextcloud/vue/dist/Components/NcButton.js'

const props = defineProps({
    items: { type: Array, default: () => [] },
    loading: { type: Boolean, default: false },
})

const emit = defineEmits(['select-drive', 'expand-item'])

function toggle(item) {
    if (item.type === 'drive') return
    item.expanded = !item.expanded
    if (item.expanded && item.children === null) {
        emit('expand-item', item)
    }
}

function findParent(drive) {
    return props.items.find(i =>
        i.children?.some(c => c.id === drive.id),
    )
}
</script>

<style scoped>
.library-list {
    border: 1px solid var(--color-border-dark);
    border-radius: 8px;
    max-height: 400px;
    overflow-y: auto;
}
.library-item-row {
    display: flex;
    align-items: center;
    gap: 8px;
    padding: 10px 12px;
    border-bottom: 1px solid var(--color-border);
}
.library-item-row.expandable {
    cursor: pointer;
}
.library-item-row.expandable:hover {
    background: var(--color-background-hover);
}
.library-item-row.child {
    padding-left: 36px;
}
.expand-icon {
    width: 20px;
    text-align: center;
    flex-shrink: 0;
}
.item-name {
    flex: 1;
    font-weight: 500;
}
.item-type {
    font-size: 12px;
    color: var(--color-text-maxcontrast);
    text-transform: uppercase;
}
.loading, .empty {
    padding: 20px;
    text-align: center;
    color: var(--color-text-maxcontrast);
}
.loading.child, .empty.child {
    padding-left: 36px;
    text-align: left;
}
</style>
