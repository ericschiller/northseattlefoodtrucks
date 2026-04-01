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
    <h2 class="font-headline text-on-surface text-lg font-bold uppercase tracking-tight mb-4 flex items-center gap-2 pl-6">
      {{ dayName }}, {{ monthDay }}
    </h2>
    <div class="space-y-4">
      <slot />
    </div>
  </section>
</template>
