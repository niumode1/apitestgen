<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { getEndpoints, getEndpointsSummary, type EndpointBrief, type EndpointSummary } from '@/api/endpoints'

const route = useRoute()
const router = useRouter()
const projectId = route.params.id as string
const specId = route.params.specId as string

const endpoints = ref<EndpointBrief[]>([])
const summary = ref<EndpointSummary | null>(null)
const loading = ref(false)
const filterMethod = ref('')

const methodTag: Record<string, string> = {
  GET: '', POST: 'primary', PUT: 'warning', DELETE: 'danger', PATCH: 'info',
}

const fetchData = async () => {
  loading.value = true
  try {
    summary.value = await getEndpointsSummary(specId)
    const res = await getEndpoints(specId, {
      method: filterMethod.value || undefined,
      page_size: 200,
    })
    endpoints.value = res.items
  } finally { loading.value = false }
}

onMounted(fetchData)
</script>

<template>
  <div class="page">
    <el-breadcrumb separator="/" style="margin-bottom: 16px">
      <el-breadcrumb-item :to="{ path: '/projects' }">项目</el-breadcrumb-item>
      <el-breadcrumb-item :to="{ path: `/projects/${projectId}` }">详情</el-breadcrumb-item>
      <el-breadcrumb-item>接口</el-breadcrumb-item>
    </el-breadcrumb>

    <div class="page-header">
      <h2>
        接口列表
        <span class="count" v-if="summary">{{ summary.total }} 个</span>
      </h2>
      <div style="display:flex;gap:8px">
        <el-select v-model="filterMethod" placeholder="方法" clearable @change="fetchData" style="width:100px" size="default">
          <el-option label="GET" value="GET" />
          <el-option label="POST" value="POST" />
          <el-option label="PUT" value="PUT" />
          <el-option label="DELETE" value="DELETE" />
        </el-select>
        <el-button type="primary" @click="router.push(`/projects/${projectId}/specs/${specId}/generate`)">
          生成测试
        </el-button>
      </div>
    </div>

    <div class="endpoint-list" v-loading="loading">
      <div v-for="ep in endpoints" :key="ep.id" class="ep-row">
        <el-tag :type="methodTag[ep.method] as any || 'info'" size="small" effect="dark" class="method">{{ ep.method }}</el-tag>
        <span class="path">{{ ep.path }}</span>
        <span class="summary">{{ ep.summary }}</span>
        <span class="right">
          <el-tag v-for="t in (ep.tags||[]).slice(0,2)" :key="t" size="small" class="tag">{{ t }}</el-tag>
          <span class="tc">{{ ep.testcase_count || 0 }} 用例</span>
        </span>
      </div>
      <div v-if="!loading && endpoints.length === 0" class="empty">暂无接口</div>
    </div>
  </div>
</template>

<style scoped>
.page { max-width: 1040px; }
.page-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 20px; }
.page-header h2 { font-size: 22px; font-weight: 600; color: #111; }
.count { font-weight: 400; font-size: 15px; color: #999; margin-left: 8px; }

.endpoint-list { background: #fff; border: 1px solid #eee; border-radius: 10px; overflow: hidden; }

.ep-row {
  display: flex; align-items: center; gap: 12px;
  padding: 12px 20px;
  border-bottom: 1px solid #f5f5f5;
  font-size: 14px;
}
.ep-row:last-child { border-bottom: none; }

.method { min-width: 56px; text-align: center; }
.path { font-family: monospace; font-size: 13px; color: #333; min-width: 0; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
.summary { color: #888; font-size: 13px; flex-shrink: 0; max-width: 200px; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
.right { margin-left: auto; display: flex; align-items: center; gap: 6px; flex-shrink: 0; }
.tag { font-size: 11px; }
.tc { font-size: 12px; color: #bbb; }

.empty { text-align: center; padding: 60px 0; color: #bbb; }
</style>
