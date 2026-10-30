<script setup lang="ts">
import { useRoute } from 'vue-router'

const route = useRoute()

const items = [
  { path: '/', label: '首页', icon: 'HomeFilled' },
  { path: '/workspaces', label: '工作区', icon: 'Folder' },
  { path: '/postman', label: 'Postman', icon: 'Connection' },
  { path: '/settings', label: 'LLM 配置', icon: 'Setting' },
]
</script>

<template>
  <nav class="sidebar">
    <router-link to="/" class="brand">
      <span class="icon">◆</span>
      <span>APITestGen</span>
    </router-link>

    <div class="nav">
      <router-link
        v-for="item in items"
        :key="item.path"
        :to="item.path"
        class="item"
        :class="{ active: item.path === '/' ? route.path === '/' : route.path.startsWith(item.path) }"
      >
        <el-icon><component :is="item.icon" /></el-icon>
        <span>{{ item.label }}</span>
      </router-link>
    </div>

    <div class="footer">
      <span class="dot active"></span>
      <span class="ver">v1.0</span>
    </div>
  </nav>
</template>

<style scoped>
.sidebar {
  width: 190px; height: 100vh; background: #fff;
  border-right: 1px solid #eee; display: flex; flex-direction: column; flex-shrink: 0;
}

.brand {
  display: flex; align-items: center; gap: 10px;
  padding: 22px 18px; text-decoration: none; color: #111;
  font-weight: 700; font-size: 15px; border-bottom: 1px solid #f0f0f0;
}
.icon { font-size: 18px; color: #409eff; }

.nav { padding: 12px 10px; flex: 1; }

.item {
  display: flex; align-items: center; gap: 10px;
  padding: 10px 14px; border-radius: 8px;
  text-decoration: none; color: #555; font-size: 14px;
  margin-bottom: 2px; transition: all 0.12s;
}
.item:hover { background: #f0f5ff; color: #409eff; }
.item.active { background: #e8f0fe; color: #409eff; font-weight: 600; }

.footer { padding: 14px 18px; border-top: 1px solid #f0f0f0; display: flex; align-items: center; gap: 8px; }
.dot { width: 8px; height: 8px; border-radius: 50%; background: #ddd; }
.dot.active { background: #67c23a; }
.ver { font-size: 12px; color: #aaa; }
</style>
