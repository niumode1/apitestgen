<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useRoute } from 'vue-router'
import apiClient from '@/api/client'

const route = useRoute()
const projectId = route.params.id as string

const reports = ref<any[]>([])
const loading = ref(false)
const generating = ref(false)

// Viewer
const showViewer = ref(false)
const viewing = ref<any>(null)
const viewingMd = ref('')

const statusTag: Record<string, string> = {
  completed: 'success', running: 'warning', failed: 'danger',
}

const fetch = async () => {
  loading.value = true
  try {
    const { data } = await apiClient.get(`/projects/${projectId}/reports`)
    reports.value = data.items || []
  } finally { loading.value = false }
}

const generateReport = async () => {
  // Get latest execution
  const { data: execs } = await apiClient.get(`/projects/${projectId}/executions`, { params: { page_size: 1 } })
  const latest = execs.items?.[0]
  if (!latest) {
    alert('No executions found. Run tests first.')
    return
  }

  generating.value = true
  try {
    await apiClient.post(`/projects/${projectId}/executions/${latest.id}/reports`)
    await fetch()
  } catch (e: any) {
    alert(e.response?.data?.detail || 'Failed to generate report')
  } finally { generating.value = false }
}

const viewReport = async (r: any) => {
  try {
    const { data } = await apiClient.get(`/projects/${projectId}/reports/${r.id}`)
    viewing.value = data
    viewingMd.value = data.content || ''
    showViewer.value = true
  } catch { /* ignore */ }
}

const downloadReport = (r: any) => {
  window.open(`/api/v1/projects/${projectId}/reports/${r.id}/download`, '_blank')
}

onMounted(fetch)
</script>

<template>
  <div class="page">
    <el-breadcrumb separator="/" style="margin-bottom: 16px">
      <el-breadcrumb-item :to="{ path: '/projects' }">项目</el-breadcrumb-item>
      <el-breadcrumb-item :to="{ path: `/projects/${projectId}` }">详情</el-breadcrumb-item>
      <el-breadcrumb-item>报告</el-breadcrumb-item>
    </el-breadcrumb>

    <div class="page-header">
      <h2>缺陷报告</h2>
      <el-button type="primary" :loading="generating" @click="generateReport">
        生成报告
      </el-button>
    </div>

    <div class="list" v-loading="loading">
      <div v-for="r in reports" :key="r.id" class="row">
        <el-tag :type="r.pass_rate > 90 ? 'success' : r.pass_rate > 50 ? 'warning' : 'danger'" size="small" effect="dark">
          {{ r.pass_rate }}%
        </el-tag>
        <span class="name">{{ r.title }}</span>
        <span class="info">{{ r.failed_count }} failed / {{ r.error_count }} error</span>
        <span class="right">
          <el-button text size="small" @click="viewReport(r)">查看</el-button>
          <el-button text size="small" @click="downloadReport(r)">下载</el-button>
        </span>
      </div>
      <div v-if="!loading && reports.length === 0" class="empty">
        先执行测试，然后点「生成报告」
      </div>
    </div>

    <!-- Viewer Dialog -->
    <el-dialog v-model="showViewer" title="报告预览" width="800px" top="3vh">
      <div v-if="viewingMd" class="md-preview" v-html="viewingMd.replace(/\n/g, '<br>').replace(/## (.+)/g, '<h3>$1</h3>').replace(/\*\*(.+?)\*\*/g, '<strong>$1</strong>').replace(/\|(.+)\|/g, '<tr><td>$1</td></tr>')" />
      <el-empty v-else description="加载中..." />
    </el-dialog>
  </div>
</template>

<style scoped>
.page { max-width: 900px; }
.page-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 20px; }
.page-header h2 { font-size: 22px; font-weight: 600; color: #111; }

.list { background: #fff; border: 1px solid #eee; border-radius: 10px; overflow: hidden; }
.row {
  display: flex; align-items: center; gap: 12px;
  padding: 12px 20px; border-bottom: 1px solid #f5f5f5; font-size: 14px;
}
.row:last-child { border-bottom: none; }
.name { flex: 1; color: #333; }
.info { font-size: 13px; color: #888; }
.right { display: flex; gap: 4px; }
.empty { text-align: center; padding: 60px 0; color: #bbb; }

.md-preview {
  font-size: 14px; line-height: 1.8; max-height: 70vh; overflow-y: auto;
}
</style>
