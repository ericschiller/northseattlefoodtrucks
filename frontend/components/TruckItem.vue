<script setup lang="ts">
import { slugify } from '~/utils/slugify'

const props = defineProps<{
  name: string
  location: string
  locationUrl?: string
  time: string
  description?: string
  category?: string
  isVisionExtracted?: boolean
  isClickable?: boolean
  index?: number
}>()

const router = useRouter()

const navigateToProfile = () => {
  if (props.isClickable) {
    router.push(`/truck/${slugify(props.name)}`)
  }
}

const badgeLabel = computed(() => {
  if (props.description) return props.description
  if (props.category) return props.category.replace(/-/g, ' ').replace(/\b\w/g, c => c.toUpperCase())
  return 'Food Truck'
})

const badgeClasses = (idx: number) => {
  const colors = [
    'bg-[#D1FAE5] text-[#065F46]', // Mint
    'bg-[#DBEAFE] text-[#1E40AF]', // Blue
    'bg-[#FFEDD5] text-[#9A3412]', // Orange
    'bg-[#FCE7F3] text-[#9D174D]', // Pink
    'bg-[#F5D0FE] text-[#701A75]'  // Fuchsia
  ]
  return colors[(props.index + idx) % colors.length]
}

const tags = computed(() => {
  const t = []
  if (props.category) t.push(props.category.replace(/-/g, ' '))
  if (props.description) t.push(props.description)
  if (t.length === 0) t.push('Food Truck')
  if (props.isVisionExtracted) t.push('AI Extracted')
  return t
})
</script>

<template>
  <div 
    @click="navigateToProfile"
    :class="[
      'bg-surface-container-lowest rounded-xl p-5 shadow-[0_4px_20px_rgba(0,103,94,0.06)] border border-outline-variant/10 transition-all duration-300',
      isClickable ? 'hover:border-primary/30 hover:shadow-lg cursor-pointer active:scale-[0.98]' : 'cursor-default'
    ]"
  >
    <div class="flex flex-col md:flex-row md:justify-between md:items-start mb-2 gap-1 md:gap-4">
      <h3 class="font-headline text-2xl font-extrabold text-on-surface">{{ name }}</h3>
      <span class="text-[1rem] font-bold text-on-surface-variant/60 font-label">{{ time }}</span>
    </div>
    
    <div class="flex items-center text-on-surface-variant mb-5 gap-1.5">
      <span class="material-symbols-outlined text-[18px]" data-icon="location_on">location_on</span>
      <span class="text-sm font-medium font-body">
        <a
          v-if="locationUrl"
          :href="locationUrl"
          target="_blank"
          @click.stop
          class="hover:text-primary transition-colors relative z-10"
        >{{ location }}</a>
        <span v-else>{{ location }}</span>
      </span>
    </div>

    <div class="flex flex-wrap gap-2">
      <span 
        :class="[badgeClasses(0), 'px-3 py-1 rounded-full text-[10px] font-bold uppercase tracking-wider']"
      >
        {{ badgeLabel }}<span v-if="isVisionExtracted"> · AI</span>
      </span>
    </div>
  </div>
</template>
