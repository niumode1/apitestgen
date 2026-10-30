<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import apiClient from '@/api/client'

const router = useRouter()
const workspaces = ref<any[]>([])
const summary = ref<any>(null)
const loading = ref(true)

onMounted(async () => {
  try {
    const [ws, stats] = await Promise.all([
      apiClient.get('/projects', { params: { page_size: 5 } }),
      apiClient.get('/dashboard/summary'),
    ])
    workspaces.value = ws.data.items || []
    summary.value = stats.data
  } catch { /* ignore */ }
  finally { loading.value = false }
})
</script>

<template>
  <div class="home">
    <div class="hero">
      <h1>APITestGen</h1>
      <p>导入 OpenAPI 文档，AI 自动生成 pytest 测试，一键执行看结果</p>
      <div style="display:flex;gap:12px;justify-content:center">
        <el-button type="primary" size="large" @click="router.push('/workspaces')">进入工作区</el-button>
        <el-button size="large" @click="router.push('/workspaces'); setTimeout(() => document.querySelector('.el-button--primary')?.closest('.header')?.querySelector('.el-button--primary')?.click(), 500)">新建工作区</el-button>
      </div>
    </div>

    <div class="stats" v-if="summary">
      <div class="stat-card">
        <span class="num">{{ summary.total_projects }}</span>
        <span class="label">项目</span>
      </div>
      <div class="stat-card">
        <span class="num">{{ summary.total_testcases }}</span>
        <span class="label">测试用例</span>
      </div>
      <div class="stat-card">
        <span class="num">{{ summary.total_executions }}</span>
        <span class="label">执行次数</span>
      </div>
      <div class="stat-card">
        <span class="num">{{ summary.overall_pass_rate }}%</span>
        <span class="label">通过率</span>
      </div>
    </div>

    <div class="recent" v-if="workspaces.length">
      <h3>最近工作区</h3>
      <div class="ws-list">
        <div v-for="w in workspaces" :key="w.id" class="ws-item" @click="router.push(`/workspaces/${w.id}`)">
          <div>
            <strong>{{ w.name }}</strong>
            <span class="meta">{{ w.spec_count }} 文档 · {{ w.testcase_count }} 用例</span>
          </div>
          <el-icon><ArrowRight /></el-icon>
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped>
.home { max-width: 720px; margin: 0 auto; }

.hero {
  text-align: center; padding: 60px 0 40px;
}
.hero h1 { font-size: 36px; font-weight: 700; color: #111; margin-bottom: 12px; }
.hero p { font-size: 16px; color: #666; margin-bottom: 24px; }

.stats {
  display: grid; grid-template-columns: repeat(4, 1fr); gap: 16px;
  margin-bottom: 40px;
}
.stat-card {
  background: #fff; border: 1px solid #eee; border-radius: 10px;
  text-align: center; padding: 20px;
}
.stat-card .num { display: block; font-size: 28px; font-weight: 700; color: #111; }
.stat-card .label { font-size: 13px; color: #999; margin-top: 4px; }

.recent h3 { font-size: 16px; color: #333; margin-bottom: 12px; }
.ws-list { background: #fff; border: 1px solid #eee; border-radius: 10px; overflow: hidden; }
.ws-item {
  display: flex; justify-content: space-between; align-items: center;
  padding: 16px 20px; border-bottom: 1px solid #f5f5f5; cursor: pointer;
  transition: background 0.1s;
}
.ws-item:hover { background: #fafafa; }
.ws-item:last-child { border-bottom: none; }
.ws-item .meta { display: block; font-size: 12px; color: #999; margin-top: 2px; }
</style>
