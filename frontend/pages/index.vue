<script setup lang="ts">
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

const { data, pending, error } = useFetch<WebData>(() => `${useRuntimeConfig().app.baseURL}data.json?t=${Date.now()}`)

const currentTab = ref<'trucks' | 'events'>('trucks')

const groupedEvents = computed(() => {
  const list = currentTab.value === 'trucks'
    ? data.value?.truck_events
    : data.value?.other_events
  if (!list) return {}

  const today = new Date().toLocaleDateString('en-CA', { timeZone: 'America/Los_Angeles' })

  const sortedList = [...list]
    .filter(event => event.date.split('T')[0] >= today)
    .sort((a, b) => a.date.localeCompare(b.date))

  const groups: Record<string, (FoodTruckEvent & { globalIndex: number })[]> = {}
  
  sortedList.forEach((event, idx) => {
    const dateKey = event.date.split('T')[0]
    if (!groups[dateKey]) groups[dateKey] = []
    groups[dateKey].push({ ...event, globalIndex: idx })
  })

  return groups
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
      hour: 'numeric',
      minute: '2-digit'
    })
  } catch (e) {
    return ''
  }
}
</script>

<template>
  <div class="bg-surface min-h-screen">
    <AppHeader />

    <main class="pb-12 max-w-4xl mx-auto">
      <!-- Filter Toggle Section -->
      <div class="px-6 pt-8 pb-12 flex justify-between items-center">
        <div class="flex gap-3">
          <button 
            @click="currentTab = 'trucks'"
            :class="[
              'px-8 py-3 rounded-xl font-label font-bold text-sm tracking-widest active:scale-95 duration-150 transition-colors',
              currentTab === 'trucks' ? 'bg-on-primary-fixed text-primary-container' : 'bg-surface-container-low text-on-surface-variant'
            ]"
          >TRUCKS</button>
          <button 
            @click="currentTab = 'events'"
            :class="[
              'px-8 py-3 rounded-xl font-label font-bold text-sm tracking-widest active:scale-95 duration-150 transition-colors',
              currentTab === 'events' ? 'bg-on-primary-fixed text-primary-container' : 'bg-surface-container-low text-on-surface-variant'
            ]"
          >EVENTS</button>
        </div>
        <div v-if="data?.updated" class="text-sm font-label font-bold uppercase tracking-widest text-on-surface-variant/60">
          Updated: {{ formatUpdatedDate(data.updated) }}
        </div>
      </div>

      <!-- Loading State -->
      <div v-if="pending" class="px-6 py-20 text-center">
        <p class="font-label text-sm uppercase tracking-[0.5em] text-primary animate-pulse">Syncing Brewery Data...</p>
      </div>

      <!-- Error State -->
      <div v-else-if="error" class="px-6 py-20 text-center">
        <p class="font-headline text-2xl font-bold uppercase text-error mb-2">Sync Interrupted</p>
        <p class="font-label text-sm uppercase tracking-widest text-on-surface-variant">Check connection.</p>
      </div>

      <div v-else class="px-6 space-y-8">
        <!-- Schedule Canvas -->
        <DaySection
          v-for="(events, dateKey) in groupedEvents"
          :key="dateKey"
          :day-name="formatDateParts(dateKey).dayName"
          :month-day="formatDateParts(dateKey).monthDay"
        >
          <TruckItem
            v-for="(event, eIdx) in events"
            :key="eIdx"
            :index="event.globalIndex"
            :name="event.vendor"
            :location="event.location"
            :location-url="event.location_url"
            :time="event.start_time && event.end_time ? `${event.start_time} — ${event.end_time}` : 'All Day'"
            :description="event.description"
            :category="event.category"
            :is-vision-extracted="event.extraction_method === 'vision'"
            :is-clickable="event.category === 'food-truck' || !event.category"
          />
        </DaySection>


        <!-- Integrity Warnings -->
        <div v-if="data?.errors?.length" class="mt-12 space-y-2 p-6 bg-surface-container-low border border-error/10 rounded-xl">
          <p class="font-label text-[9px] uppercase tracking-widest text-error font-bold mb-2">Integrity Warnings:</p>
          <p v-for="(err, idx) in data.errors" :key="idx" class="text-[9px] uppercase tracking-tighter text-on-surface-variant">
            • {{ err }}
          </p>
        </div>
      </div>
    </main>
  </div>
</template>
