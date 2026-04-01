<template>
  <div class="bg-surface text-on-surface min-h-screen font-body selection:bg-primary/30">
    <NuxtPage />
    <AppFooter />
  </div>
</template>

<style>
.material-symbols-outlined {
  font-variation-settings: 'FILL' 0, 'wght' 400, 'GRAD' 0, 'opsz' 24;
  vertical-align: middle;
}

body {
  background-color: #d2fffe;
}

/* Custom scrollbar */
::-webkit-scrollbar {
  width: 8px;
}
::-webkit-scrollbar-track {
  background: #d2fffe;
}
::-webkit-scrollbar-thumb {
  background: #7db7b7;
  border-radius: 4px;
}
::-webkit-scrollbar-thumb:hover {
  background: #468080;
}
</style>
