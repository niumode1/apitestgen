<script setup lang="ts">
import Sidebar from './Sidebar.vue'
</script>

<template>
  <div class="app-shell">
    <Sidebar />
    <div class="main-area">
      <router-view />
    </div>
  </div>
</template>

<style>
/* 全局重置 */
* { margin: 0; padding: 0; box-sizing: border-box; }
html, body, #app { height: 100%; font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; }
</style>

<style scoped>
.app-shell {
  display: flex;
  height: 100vh;
  background: #f8f9fa;
}

.main-area {
  flex: 1;
  overflow-y: auto;
  padding: 32px 40px;
  min-width: 0;
}
</style>
