<script setup lang="ts">
defineProps<{
  updatedDate?: string
}>()
</script>

<template>
  <header class="mb-20">
    <div class="flex items-center justify-between border-b border-outline/10 pb-8">
      <div>
        <h1 class="font-headline text-2xl font-bold uppercase tracking-[0.1em] text-[#1E293B]">North Seattle Food Trucks</h1>
      </div>
      <div v-if="updatedDate" class="text-sm font-label uppercase tracking-widest text-on-surface-variant">
        Updated: {{ updatedDate }}
      </div>
    </div>
  </header>
</template>
