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

  const now = new Date()
  const todayStr = now.toLocaleDateString('en-CA', { timeZone: 'America/Los_Angeles' })

  const sortedList = [...list]
    .filter(event => {
      const eventDateStr = event.date.split('T')[0]
      
      // 1. If date is in the future, keep it
      if (eventDateStr > todayStr) return true
      
      // 2. If date is in the past, discard it
      if (eventDateStr < todayStr) return false
      
      // 3. If it's today, check the end time
      if (eventDateStr === todayStr) {
        if (!event.end_time) return true // Keep "All Day" events
        
        try {
          // Parse "9:00 PM", "9 PM", or "21:00" etc.
          const timeParts = event.end_time.trim().split(' ')
          const timeStr = timeParts[0]
          const modifier = timeParts[1]?.toUpperCase()
          
          let [hours, minutes] = timeStr.split(':').map(Number)
          if (isNaN(minutes)) minutes = 0
          
          if (modifier === 'PM' && hours < 12) hours += 12
          if (modifier === 'AM' && hours === 12) hours = 0
          
          const endDateTime = new Date()
          endDateTime.setHours(hours, minutes, 0, 0)
          
          // Use current time in Pacific for comparison
          const currentPacificTime = new Date(new Date().toLocaleString('en-US', { timeZone: 'America/Los_Angeles' }))
          
          return endDateTime > currentPacificTime
        } catch (e) {
          return true // Fallback to showing it if parsing fails
        }
      }
      return false
    })
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
      <div class="px-6 pt-8 pb-12 flex flex-col md:flex-row-reverse md:justify-between md:items-center gap-4">
        <div v-if="data?.updated" class="text-sm font-label font-bold uppercase tracking-widest text-on-surface-variant/60">
          Updated: {{ formatUpdatedDate(data.updated) }}
        </div>
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
