<script setup lang="ts">
import { format, parseISO } from 'date-fns'

interface FoodTruckEvent {
  date: string
  vendor: string
  location: string
  location_url?: string
  start_time: string
  end_time: string
  description?: string
  extraction_method?: string
  category?: string
}

interface WebData {
  truck_events: FoodTruckEvent[]
  other_events: FoodTruckEvent[]
  updated: string
  total_events: number

  errors?: string[]
}

const { data, pending, error } = useFetch<WebData>('/data.json')

const currentTab = ref<'trucks' | 'events'>('trucks')

const groupedEvents = computed(() => {
  const list = currentTab.value === 'trucks'
    ? data.value?.truck_events
    : data.value?.other_events
  if (!list) return {}

  // Get today's date in Seattle timezone for filtering
  const today = new Date().toLocaleDateString('en-CA', { timeZone: 'America/Los_Angeles' })

  const groups: Record<string, FoodTruckEvent[]> = {}
  list.forEach(event => {
    const dateKey = event.date.split('T')[0]
    
    // Filter out entries in the past
    if (dateKey < today) return

    if (!groups[dateKey]) groups[dateKey] = []
    groups[dateKey].push(event)
  })

  return Object.keys(groups).sort().reduce((acc, key) => {
    acc[key] = groups[key]
    return acc
  }, {} as Record<string, FoodTruckEvent[]>)
})

const formatDateParts = (dateStr: string) => {
  const date = new Date(dateStr + 'T12:00:00-08:00')
  return {
    dayName: date.toLocaleDateString('en-US', { weekday: 'long' }),
    monthDay: date.toLocaleDateString('en-US', { month: 'long', day: 'numeric' })
  }
}

const formatUpdatedDate = (isoString: string) => {
  try {
    const date = new Date(isoString)
    return date.toLocaleDateString('en-US', { 
      month: 'short', 
      day: 'numeric', 
      year: 'numeric' 
    })
  } catch (e) {
    return ''
  }
}
</script>

<template>
  <div class="bg-[#f9fffb] text-[#2e3432] min-h-screen font-body selection:bg-primary-mint/30">
    <!-- HARDCODED TEST ELEMENT -->
    <div style="background: red; color: white; padding: 10px; text-align: center; position: fixed; top: 0; width: 100%; z-index: 9999;">
      DEBUG: APP IS RENDERING
    </div>
    <main class="pt-16 pb-24 px-6 md:px-12 max-w-4xl mx-auto min-h-screen">
      <AppHeader :updated-date="data?.updated ? formatUpdatedDate(data.updated) : undefined" />

      <!-- Loading State -->
      <div v-if="pending" class="py-20 text-center">
        <p class="font-label text-sm uppercase tracking-[0.5em] text-primary-mint animate-pulse">Accessing Archive...</p>
      </div>

      <!-- Error State -->
      <div v-else-if="error" class="py-20 text-center border-b border-outline/10">
        <p class="font-headline text-2xl font-bold uppercase text-error mb-2">Archive Interrupted</p>
        <p class="font-label text-sm uppercase tracking-widest text-on-surface-variant">System synchronization failed.</p>
      </div>

      <div v-else>
        <!-- Tab Toggle -->
        <div class="flex gap-3 mt-12 mb-0">
          <button
            @click="currentTab = 'trucks'"
            :class="currentTab === 'trucks'
              ? 'px-5 py-2 rounded-lg font-label text-xs uppercase tracking-[0.4em] bg-primary-mint-dark text-white font-bold transition-all shadow-sm'
              : 'px-5 py-2 rounded-lg font-label text-xs uppercase tracking-[0.4em] bg-[#F8F8FF] text-[#64748B] border border-[#64748B] font-bold transition-all hover:bg-white'"
          >TRUCKS</button>
          <button
            @click="currentTab = 'events'"
            :class="currentTab === 'events'
              ? 'px-5 py-2 rounded-lg font-label text-xs uppercase tracking-[0.4em] bg-primary-mint-dark text-white font-bold transition-all shadow-sm'
              : 'px-5 py-2 rounded-lg font-label text-xs uppercase tracking-[0.4em] bg-[#F8F8FF] text-[#64748B] border border-[#64748B] font-bold transition-all hover:bg-white'"
          >EVENTS</button>
        </div>

        <!-- Content Grid -->
        <div class="space-y-16 mt-10">
          <DaySection
            v-for="(events, dateKey) in groupedEvents"
            :key="dateKey"
            :day-name="formatDateParts(dateKey).dayName"
            :month-day="formatDateParts(dateKey).monthDay"
            :count="(events as FoodTruckEvent[]).length"
            :count-label="currentTab === 'trucks' ? ((events as FoodTruckEvent[]).length === 1 ? 'TRUCK' : 'TRUCKS') : ((events as FoodTruckEvent[]).length === 1 ? 'EVENT' : 'EVENTS')"
          >
            <TruckItem
              v-for="(event, eIdx) in events"
              :key="eIdx"
              :name="event.vendor"
              :location="event.location"
              :location-url="event.location_url"
              :time="`${event.start_time} — ${event.end_time}`"
              :description="event.description"
              :category="event.category"
:is-vision-extracted="event.extraction_method === 'vision'"
            />
          </DaySection>

        </div>

        <!-- Errors Note -->
        <div v-if="data?.errors?.length" class="mt-12 space-y-2 p-6 bg-surface-container-low border border-error/10">
          <p class="font-label text-[9px] uppercase tracking-widest text-error font-bold mb-2">Integrity Warnings:</p>
          <p v-for="(err, idx) in data.errors" :key="idx" class="text-[9px] uppercase tracking-tighter text-on-surface-variant">
            • {{ err }}
          </p>
        </div>
      </div>
    </main>

    <AppFooter />
  </div>
</template>

<style>
.material-symbols-outlined {
  font-variation-settings: 'FILL' 0, 'wght' 400, 'GRAD' 0, 'opsz' 24;
  vertical-align: middle;
}

/* Custom scrollbar for a more integrated feel */
::-webkit-scrollbar {
  width: 8px;
}
::-webkit-scrollbar-track {
  background: #f9fffb;
}
::-webkit-scrollbar-thumb {
  background: #d4e0db;
}
::-webkit-scrollbar-thumb:hover {
  background: #aab4b0;
}
</style>
