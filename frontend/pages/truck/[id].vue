<script setup lang="ts">
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
  
  // Find all instances of this truck across all breweries
  const allEvents = [...data.value.truck_events, ...data.value.other_events]
  const stops = allEvents.filter(e => slugify(e.vendor) === truckSlug)
  
  if (stops.length === 0) return null

  // Use the most common vendor name (handles minor spelling variations)
  const names = stops.map(s => s.vendor)
  const name = names.sort((a, b) => 
    names.filter(v => v === a).length - names.filter(v => v === b).length
  ).pop() || stops[0].vendor

  // Filter out past events
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
  <main class="pt-16 pb-24 px-6 md:px-12 max-w-4xl mx-auto min-h-screen">
    <div class="mb-12">
      <NuxtLink 
        to="/" 
        class="inline-flex items-center gap-2 text-primary-mint-dark hover:text-primary-mint transition-colors font-label text-xs uppercase tracking-widest mb-8"
      >
        <span class="material-symbols-outlined text-sm">arrow_back</span>
        Back to Schedule
      </NuxtLink>

      <div v-if="pending" class="py-20 text-center">
        <p class="font-label text-sm uppercase tracking-[0.5em] text-primary-mint animate-pulse">Loading Archive...</p>
      </div>

      <div v-else-if="error || !truckInfo" class="py-20 text-center border-b border-outline/10">
        <p class="font-headline text-2xl font-bold uppercase text-error mb-2">Truck Not Found</p>
        <p class="font-label text-sm uppercase tracking-widest text-on-surface-variant">The requested archive entry is missing or invalid.</p>
      </div>

      <div v-else>
        <h1 class="font-headline text-4xl font-bold uppercase tracking-[0.1em] text-[#1E293B] mb-4">
          {{ truckInfo.name }}
        </h1>
        <p class="font-label text-sm uppercase tracking-widest text-[#64748B] mb-12">
          Upcoming Stops in North Seattle
        </p>

        <div class="space-y-6">
          <div 
            v-for="(stop, idx) in truckInfo.stops" 
            :key="idx"
            class="p-6 rounded-lg bg-white border border-[#1E293B]/10 shadow-sm flex flex-col md:flex-row justify-between items-start md:items-center gap-4"
          >
            <div>
              <div class="flex items-center gap-3 mb-1">
                <span class="font-label text-xs font-bold text-[#64748B] uppercase tracking-wider">
                  {{ formatDate(stop.date) }}
                </span>
                <span class="text-[#1E293B]/20 text-xs">•</span>
                <span class="font-label text-xs font-bold text-primary-mint-dark uppercase tracking-wider">
                  {{ stop.start_time }} — {{ stop.end_time }}
                </span>
              </div>
              <h3 class="font-headline text-xl font-bold text-[#1E293B]">
                {{ stop.location }}
              </h3>
            </div>
            
            <a 
              v-if="stop.location_url"
              :href="stop.location_url"
              target="_blank"
              class="px-4 py-2 rounded-lg border border-[#64748B]/30 text-[#64748B] hover:bg-[#F8F8FF] transition-all text-xs font-bold uppercase tracking-widest"
            >
              Brewery Info
            </a>
          </div>
        </div>

        <div v-if="truckInfo.stops.length === 0" class="py-12 text-center text-[#64748B] italic">
          No other upcoming stops found in this archive cycle.
        </div>
      </div>
    </div>
  </main>
</template>
