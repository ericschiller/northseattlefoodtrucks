<script setup lang="ts">
defineProps<{
  dayName: string
  monthDay: string
  count?: number
  countLabel?: string
}>()
</script>

<template>
  <section>
    <div class="flex items-baseline justify-between mb-10 pb-4 border-b border-[#1E293B]/10">
      <h2 class="font-headline text-2xl font-bold uppercase tracking-tight text-[#1E293B]">
        {{ dayName }}, <span class="text-[#1E293B]">{{ monthDay }}</span>
      </h2>
      <span v-if="count" class="font-label text-[10px] font-bold tracking-[0.2em] text-[#1E293B] uppercase">
        {{ count }} {{ countLabel ?? (count === 1 ? 'EVENT' : 'EVENTS') }}
      </span>
    </div>
    <div class="space-y-6">
      <slot />
    </div>
  </section>
</template>
