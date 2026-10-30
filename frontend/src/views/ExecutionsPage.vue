<script setup lang="ts">
import { ref, onMounted, onUnmounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import apiClient from '@/api/client'

const route = useRoute()
const router = useRouter()
const projectId = route.params.id as string

const executions = ref<any[]>([])
const loading = ref(false)
const running = ref(false)
const polling = ref<ReturnType<typeof setInterval> | null>(null)

const statusTag: Record<string, string> = {
  completed: 'success', running: 'warning', failed: 'danger',
  pending: 'info', cancelled: '',
}

const fetch = async () => {
  try {
    const { data } = await apiClient.get(`/projects/${projectId}/executions`, { params: { page_size: 10 } })
    executions.value = data.items || []
  } catch { /* ignore */ }
}

const startExecution = async () => {
  running.value = true
  try {
    await apiClient.post(`/projects/${projectId}/executions`, {})
    // Poll every 2s for results
    polling.value = setInterval(async () => {
      await fetch()
      const latest = executions.value[0]
      if (latest && latest.status !== 'running') {
        stopPolling()
        running.value = false
      }
    }, 2000)
  } catch {
    running.value = false
  }
}

const stopPolling = () => {
  if (polling.value) { clearInterval(polling.value); polling.value = null }
}

const cancelExecution = async () => {
  const latest = executions.value[0]
  if (!latest) return
  try {
    await apiClient.post(`/projects/${projectId}/executions/${latest.id}/cancel`)
    stopPolling()
    running.value = false
    await fetch()
  } catch { /* ignore */ }
}

const formatDuration = (ms: number) => {
  if (!ms) return '-'
  if (ms < 1000) return `${ms}ms`
  return `${(ms / 1000).toFixed(1)}s`
}

onMounted(fetch)
onUnmounted(stopPolling)
</script>

<template>
  <div class="page">
    <el-breadcrumb separator="/" style="margin-bottom: 16px">
      <el-breadcrumb-item :to="{ path: '/projects' }">项目</el-breadcrumb-item>
      <el-breadcrumb-item :to="{ path: `/projects/${projectId}` }">详情</el-breadcrumb-item>
      <el-breadcrumb-item>执行</el-breadcrumb-item>
    </el-breadcrumb>

    <div class="page-header">
      <h2>测试执行</h2>
      <div style="display:flex;gap:8px">
        <el-button v-if="running" type="danger" @click="cancelExecution">停止</el-button>
        <el-button type="primary" :loading="running" @click="startExecution">
          <el-icon><VideoPlay /></el-icon> 运行测试
        </el-button>
      </div>
    </div>

    <!-- Live status for running execution -->
    <div v-if="running && executions.length > 0 && executions[0].status === 'running'" class="live-banner">
      <el-icon class="is-loading" :size="18"><Loading /></el-icon>
      <span>测试运行中... 已采集 {{ executions[0].total_tests || 0 }} 条</span>
      <el-progress
        v-if="executions[0].total_tests > 0"
        :percentage="Math.round((executions[0].passed + executions[0].failed + executions[0].errors) / executions[0].total_tests * 100)"
        :stroke-width="6"
        style="flex:1;margin:0 16px"
      />
    </div>

    <!-- History -->
    <div class="list" v-loading="loading">
      <div v-for="e in executions" :key="e.id" class="row">
        <el-tag :type="statusTag[e.status] || 'info'" size="small" effect="dark">{{ e.status }}</el-tag>
        <span class="name">{{ e.name }}</span>
        <span class="count pass">{{ e.passed }} passed</span>
        <span v-if="e.failed > 0" class="count fail">{{ e.failed }} failed</span>
        <span v-if="e.errors > 0" class="count err">{{ e.errors }} error</span>
        <span class="count">{{ e.pass_rate }}%</span>
        <span class="count">{{ formatDuration(e.duration_ms) }}</span>
      </div>
      <div v-if="!loading && executions.length === 0" class="empty">
        点击「运行测试」执行生成的测试用例
      </div>
    </div>
  </div>
</template>

<style scoped>
.page { max-width: 900px; }
.page-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 20px; }
.page-header h2 { font-size: 22px; font-weight: 600; color: #111; }

.live-banner {
  display: flex; align-items: center; gap: 12px;
  background: #fdf6ec; border: 1px solid #faecd8; border-radius: 8px;
  padding: 14px 20px; margin-bottom: 20px; font-size: 14px; color: #e6a23c;
}

.list { background: #fff; border: 1px solid #eee; border-radius: 10px; overflow: hidden; }
.row {
  display: flex; align-items: center; gap: 16px;
  padding: 12px 20px; border-bottom: 1px solid #f5f5f5; font-size: 14px;
}
.row:last-child { border-bottom: none; }
.name { flex: 1; color: #333; }
.count { font-size: 13px; color: #888; }
.count.pass { color: #67c23a; font-weight: 600; }
.count.fail { color: #f56c6c; font-weight: 600; }
.count.err { color: #e6a23c; font-weight: 600; }
.empty { text-align: center; padding: 60px 0; color: #bbb; }
</style>
