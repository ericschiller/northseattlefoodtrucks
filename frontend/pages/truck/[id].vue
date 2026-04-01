<script setup lang="ts">
import { slugify } from '~/utils/slugify'

const route = useRoute()
const truckSlug = route.params.id as string

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
}

const { data, pending, error } = useFetch<WebData>(() => `${useRuntimeConfig().app.baseURL}data.json?t=${Date.now()}`)

const truckInfo = computed(() => {
  if (!data.value) return null
  
  const allEvents = [...data.value.truck_events, ...data.value.other_events]
  const stops = allEvents.filter(e => slugify(e.vendor) === truckSlug)
  
  if (stops.length === 0) return null

  const names = stops.map(s => s.vendor)
  const name = names.sort((a, b) => 
    names.filter(v => v === a).length - names.filter(v => v === b).length
  ).pop() || stops[0].vendor

  const today = new Date().toLocaleDateString('en-CA', { timeZone: 'America/Los_Angeles' })
  const upcomingStops = stops.filter(s => s.date.split('T')[0] >= today)
    .sort((a, b) => a.date.localeCompare(b.date))

  return {
    name,
    stops: upcomingStops
  }
})

const formatDate = (dateStr: string) => {
  const dateKey = dateStr.split('T')[0]
  const date = new Date(dateKey + 'T12:00:00-08:00')
  return date.toLocaleDateString('en-US', { 
    weekday: 'short', 
    month: 'short', 
    day: 'numeric' 
  })
}
</script>

<template>
  <div class="bg-surface min-h-screen">
    <AppHeader />

    <main class="pt-8 pb-12 px-6 max-w-4xl mx-auto">
      <NuxtLink 
        to="/" 
        class="inline-flex items-center gap-2 text-primary hover:text-primary-dim transition-colors font-label text-xs uppercase tracking-[0.2em] mb-8 font-bold"
      >
        <span class="material-symbols-outlined text-sm">arrow_back</span>
        Back to Schedule
      </NuxtLink>

      <div v-if="pending" class="py-20 text-center">
        <p class="font-label text-sm uppercase tracking-[0.5em] text-primary animate-pulse">Syncing Archive...</p>
      </div>

      <div v-else-if="error || !truckInfo" class="py-20 text-center">
        <p class="font-headline text-2xl font-bold uppercase text-error mb-2">Archive entry missing</p>
        <p class="font-label text-sm uppercase tracking-widest text-on-surface-variant">The requested truck could not be found.</p>
      </div>

      <div v-else>
        <h1 class="font-headline text-4xl font-extrabold text-on-surface mb-2 uppercase tracking-tighter">
          {{ truckInfo.name }}
        </h1>
        <div class="mb-12 flex flex-col gap-2">
          <a 
            :href="`https://www.google.com/search?q=${encodeURIComponent(truckInfo.name + ' food truck')}`"
            target="_blank"
            class="text-primary hover:text-primary-dim transition-colors font-label text-[10px] uppercase tracking-widest font-bold flex items-center gap-1"
          >
            <span class="material-symbols-outlined text-xs">search</span>
            Search on Google
          </a>
        </div>

        <div class="space-y-6">
          <div 
            v-for="(stop, idx) in truckInfo.stops" 
            :key="idx"
            class="bg-surface-container-lowest rounded-xl p-5 shadow-[0_4px_20px_rgba(0,103,94,0.06)] border border-outline-variant/10 flex flex-col md:flex-row justify-between items-start md:items-center gap-4"
          >
            <div>
              <div class="flex items-center gap-3 mb-2">
                <span class="font-label text-[1rem] font-bold text-on-surface-variant/60">
                  {{ formatDate(stop.date) }}
                </span>
                <span class="h-1 w-1 rounded-full bg-outline-variant/30"></span>
                <span class="font-label text-[1rem] font-bold text-primary uppercase tracking-widest">
                  {{ stop.start_time }} — {{ stop.end_time }}
                </span>
              </div>
              <h3 class="font-headline text-xl font-extrabold text-on-surface">
                <a
                  v-if="stop.location_url"
                  :href="stop.location_url"
                  target="_blank"
                  class="hover:text-primary transition-colors"
                >{{ stop.location }}</a>
                <span v-else>{{ stop.location }}</span>
              </h3>
            </div>
            
            <a 
              v-if="stop.location_url"
              :href="stop.location_url"
              target="_blank"
              class="px-5 py-2 rounded-full border border-primary/20 text-primary hover:bg-primary/5 transition-all text-[10px] font-bold uppercase tracking-widest"
            >
              Brewery Info
            </a>
          </div>
        </div>

        <div v-if="truckInfo.stops.length === 0" class="py-12 text-center text-on-surface-variant italic font-body">
          No other upcoming stops found in this archive cycle.
        </div>
      </div>
    </main>
  </div>
</template>
