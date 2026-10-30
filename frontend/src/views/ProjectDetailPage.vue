<script setup lang="ts">
import { ref, onMounted, computed } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { getProject, type Project } from '@/api/projects'
import { getSpecs, uploadSpec, deleteSpec, type SpecResponse } from '@/api/specs'
import { getEndpointsSummary } from '@/api/endpoints'
import apiClient from '@/api/client'

const route = useRoute()
const router = useRouter()
const projectId = route.params.id as string

const project = ref<Project | null>(null)
const specs = ref<SpecResponse[]>([])
const loading = ref(false)
const uploading = ref(false)
const activeTab = ref('overview')

// Stats
const tcCount = ref(0)
const execCount = ref(0)
const lastExec = ref<any>(null)
const lastReport = ref<any>(null)

// Generate+Run
const quickRunning = ref(false)
const quickStatus = ref('')

const fetchAll = async () => {
  loading.value = true
  try {
    project.value = await getProject(projectId)
    const s = await getSpecs(projectId)
    specs.value = s.items
    try {
      const { data } = await apiClient.get(`/projects/${projectId}/testcases`, { params: { page_size: 1 } })
      tcCount.value = data.total
    } catch { }
    try {
      const { data } = await apiClient.get(`/projects/${projectId}/executions`, { params: { page_size: 1 } })
      execCount.value = data.total
      if (data.items?.length) lastExec.value = data.items[0]
    } catch { }
    try {
      const { data } = await apiClient.get(`/projects/${projectId}/reports`, { params: { page_size: 1 } })
      if (data.items?.length) lastReport.value = data.items[0]
    } catch { }
  } finally { loading.value = false }
}

const handleUpload = async (file: any) => {
  uploading.value = true
  try { await uploadSpec(projectId, file); await fetchAll() }
  finally { uploading.value = false }
  return false
}

const handleDeleteSpec = async (s: SpecResponse) => {
  await deleteSpec(s.id, projectId)
  await fetchAll()
}

// Quick: Generate + Execute for a spec
const quickGenerateAndRun = async (specId: string) => {
  quickRunning.value = true
  quickStatus.value = 'generating'
  try {
    // Generate
    const { data: genResp } = await apiClient.post(`/specs/${specId}/generate`, {
      strategy: 'positive_only',
      max_testcases_per_endpoint: 2,
    })
    const genId = genResp.generation_id

    // Poll generation
    let genDone = false
    while (!genDone) {
      await new Promise(r => setTimeout(r, 2000))
      const { data } = await apiClient.get(`/specs/${specId}/generations/${genId}/status`)
      if (data.status === 'completed') genDone = true
      if (data.status === 'failed') { quickStatus.value = 'failed'; quickRunning.value = false; return }
    }

    // Execute
    quickStatus.value = 'executing'
    await apiClient.post(`/projects/${projectId}/executions`, {})

    // Poll execution
    let execDone = false
    while (!execDone) {
      await new Promise(r => setTimeout(r, 2000))
      const { data } = await apiClient.get(`/projects/${projectId}/executions`, { params: { page_size: 1 } })
      if (data.items?.length && data.items[0].status !== 'running') {
        lastExec.value = data.items[0]
        execDone = true
      }
    }

    quickStatus.value = 'done'
    await fetchAll()
  } catch (e: any) {
    quickStatus.value = 'error'
  } finally {
    quickRunning.value = false
    setTimeout(() => quickStatus.value = '', 5000)
  }
}

const formatRate = (rate: number) => `${rate}%`

onMounted(fetchAll)
</script>

<template>
  <div class="workspace">
    <!-- Header -->
    <div class="ws-header">
      <div>
        <el-breadcrumb separator="/">
          <el-breadcrumb-item :to="{ path: '/projects' }">项目</el-breadcrumb-item>
          <el-breadcrumb-item>{{ project?.name || '...' }}</el-breadcrumb-item>
        </el-breadcrumb>
        <h2>{{ project?.name }}</h2>
      </div>
      <el-upload :show-file-list="false" :before-upload="handleUpload" accept=".json,.yaml,.yml">
        <el-button type="primary" :loading="uploading">导入文档</el-button>
      </el-upload>
    </div>

    <!-- Stats Bar -->
    <div class="stat-bar" v-if="project">
      <div class="stat">{{ specs.length }} 文档</div>
      <div class="stat">{{ tcCount }} 用例</div>
      <div class="stat">{{ execCount }} 执行</div>
      <div class="stat" v-if="lastExec">
        最近: {{ lastExec.pass_rate }}% | {{ lastExec.passed }}/{{ lastExec.total_tests }}
        <el-tag :type="lastExec.pass_rate > 80 ? 'success' : 'warning'" size="small" style="margin-left:4px">
          {{ lastExec.status }}
        </el-tag>
      </div>
    </div>

    <!-- Quick Run Banner -->
    <div v-if="quickStatus" class="quick-banner" :class="quickStatus">
      <el-icon class="is-loading" v-if="quickStatus === 'generating' || quickStatus === 'executing'"><Loading /></el-icon>
      <span>{{ quickStatus === 'generating' ? 'AI生成中...' : quickStatus === 'executing' ? '执行测试中...' : quickStatus === 'done' ? '完成!' : '出错了' }}</span>
    </div>

    <!-- Spec Cards -->
    <div v-if="specs.length === 0 && !loading" class="empty-state">
      <el-empty description="导入 OpenAPI 文档开始" />
    </div>

    <div class="card-grid" v-loading="loading">
      <div v-for="s in specs" :key="s.id" class="spec-card">
        <div class="card-top">
          <h4>{{ s.name }}</h4>
          <el-tag :type="s.parse_status === 'parsed' ? 'success' : 'warning'" size="small">{{ s.parse_status }}</el-tag>
        </div>
        <div class="card-meta">v{{ s.version }} · {{ s.endpoint_count }} 接口</div>
        <div class="card-actions">
          <el-button size="small" @click="router.push(`/projects/${projectId}/specs/${s.id}`)">
            查看接口
          </el-button>
          <el-button size="small" type="primary" @click="router.push(`/projects/${projectId}/specs/${s.id}/generate`)">
            生成测试
          </el-button>
          <el-button size="small" type="success" :loading="quickRunning" @click="quickGenerateAndRun(s.id)">
            一键全流程
          </el-button>
          <el-button size="small" text type="danger" @click="handleDeleteSpec(s)">删除</el-button>
        </div>
      </div>
    </div>

    <!-- Quick Links -->
    <div class="quick-links" v-if="tcCount > 0">
      <el-button @click="router.push(`/projects/${projectId}/testcases`)">测试用例 ({{ tcCount }})</el-button>
      <el-button type="success" @click="router.push(`/projects/${projectId}/executions`)">测试执行 ({{ execCount }})</el-button>
      <el-button @click="router.push(`/projects/${projectId}/reports`)">缺陷报告</el-button>
    </div>
  </div>
</template>

<style scoped>
.workspace { max-width: 960px; }

.ws-header {
  display: flex; justify-content: space-between; align-items: flex-start;
  margin-bottom: 16px;
}
.ws-header h2 { font-size: 22px; font-weight: 600; color: #111; margin-top: 8px; }

.stat-bar {
  display: flex; gap: 24px; padding: 14px 20px;
  background: #fff; border: 1px solid #eee; border-radius: 10px;
  margin-bottom: 20px; font-size: 14px; color: #666;
}
.stat { font-weight: 500; }

.quick-banner {
  display: flex; align-items: center; gap: 8px;
  padding: 10px 16px; border-radius: 8px; margin-bottom: 16px;
  font-size: 14px;
}
.quick-banner.generating, .quick-banner.executing { background: #e8f0fe; color: #409eff; }
.quick-banner.done { background: #f0f9eb; color: #67c23a; }
.quick-banner.error, .quick-banner.failed { background: #fef0f0; color: #f56c6c; }

.card-grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(300px, 1fr)); gap: 16px; }

.spec-card {
  background: #fff; border: 1px solid #eee; border-radius: 10px;
  padding: 20px; display: flex; flex-direction: column; gap: 12px;
}
.card-top { display: flex; justify-content: space-between; align-items: center; }
.card-top h4 { font-size: 15px; color: #111; }
.card-meta { font-size: 13px; color: #999; }
.card-actions { display: flex; gap: 6px; flex-wrap: wrap; }

.quick-links { display: flex; gap: 8px; margin-top: 24px; }

.empty-state { text-align: center; padding: 60px 0; }
</style>
