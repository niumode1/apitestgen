<script setup lang="ts">
import { ref, onMounted, computed } from 'vue'
import { useRoute } from 'vue-router'
import { ElMessageBox } from 'element-plus'
import apiClient from '@/api/client'

const route = useRoute()
const projectId = route.params.id as string

const cases = ref<any[]>([])
const loading = ref(false)
const total = ref(0)
const initError = ref('')
const filterCategory = ref('')
const selected = ref<Set<string>>(new Set())
const deleting = ref(false)

// Code viewer
const codeDialog = ref(false)
const viewingCode = ref('')
const viewingName = ref('')
const codeLoading = ref(false)
const codeError = ref('')

const catColors: Record<string, string> = {
  positive: 'success', negative: 'danger', boundary: 'warning',
  security: '', schema: 'info',
}
const catLabels: Record<string, string> = {
  positive: '正向', negative: '负向', boundary: '边界值',
  security: '安全', schema: 'Schema',
}

const allSelected = computed(() =>
  cases.value.length > 0 && selected.value.size === cases.value.length
)

const fetch = async () => {
  loading.value = true
  initError.value = ''
  selected.value = new Set()
  try {
    const params: any = { page_size: 100 }
    if (filterCategory.value) params.category = filterCategory.value
    const { data } = await apiClient.get(`/projects/${projectId}/testcases`, { params })
    cases.value = data.items || []
    total.value = data.total || 0
  } catch (e: any) {
    initError.value = e.response?.data?.detail || e.message || 'Failed to load'
  } finally { loading.value = false }
}

const toggleSelect = (id: string) => {
  const s = new Set(selected.value)
  s.has(id) ? s.delete(id) : s.add(id)
  selected.value = s
}

const toggleAll = () => {
  if (allSelected.value) {
    selected.value = new Set()
  } else {
    selected.value = new Set(cases.value.map((c: any) => c.id))
  }
}

const batchDelete = async () => {
  if (selected.value.size === 0) return
  try {
    await ElMessageBox.confirm(
      `Delete ${selected.value.size} test cases?`,
      'Confirm',
      { type: 'warning', confirmButtonText: 'Delete', cancelButtonText: 'Cancel' }
    )
    deleting.value = true
    await apiClient.post(`/projects/${projectId}/testcases/bulk-delete`, {
      testcase_ids: [...selected.value],
    })
    await fetch()
  } catch { /* cancelled */ }
  finally { deleting.value = false }
}

const viewCode = async (tc: any) => {
  viewingName.value = tc.name
  viewingCode.value = ''
  codeError.value = ''
  codeLoading.value = true
  codeDialog.value = true
  try {
    const { data } = await apiClient.get(`/projects/${projectId}/testcases/${tc.id}`)
    viewingCode.value = data.test_code || '# No code'
  } catch (e: any) {
    codeError.value = e.response?.data?.detail || 'Failed to load'
  } finally { codeLoading.value = false }
}

onMounted(fetch)
</script>

<template>
  <div class="page">
    <el-breadcrumb separator="/" style="margin-bottom: 16px">
      <el-breadcrumb-item :to="{ path: '/projects' }">项目</el-breadcrumb-item>
      <el-breadcrumb-item :to="{ path: `/projects/${projectId}` }">详情</el-breadcrumb-item>
      <el-breadcrumb-item>测试用例</el-breadcrumb-item>
    </el-breadcrumb>

    <div class="page-header">
      <h2>测试用例 <span class="count">{{ total }}</span></h2>
      <div style="display:flex;gap:8px">
        <el-select v-model="filterCategory" placeholder="类别" clearable @change="fetch" style="width:110px">
          <el-option label="正向" value="positive" />
          <el-option label="负向" value="negative" />
          <el-option label="边界值" value="boundary" />
          <el-option label="安全" value="security" />
          <el-option label="Schema" value="schema" />
        </el-select>
        <el-button v-if="selected.size > 0" type="danger" :loading="deleting" @click="batchDelete">
          删除 ({{ selected.size }})
        </el-button>
      </div>
    </div>

    <el-alert v-if="initError" :title="initError" type="error" show-icon style="margin-bottom:16px" />

    <div class="endpoint-list" v-loading="loading">
      <div class="ep-row" style="background:#fafafa" v-if="cases.length > 0">
        <el-checkbox :model-value="allSelected" @change="toggleAll" />
        <span style="color:#999;font-size:12px;flex:1">全选</span>
      </div>
      <div v-for="tc in cases" :key="tc.id" class="ep-row">
        <el-checkbox :model-value="selected.has(tc.id)" @change="() => toggleSelect(tc.id)" />
        <el-tag :type="catColors[tc.category] || 'info'" size="small" effect="dark">{{ catLabels[tc.category] || tc.category }}</el-tag>
        <span class="method-tag">{{ tc.endpoint_method }}</span>
        <code class="ep-path">{{ tc.endpoint_path }}</code>
        <span class="name">{{ tc.name }}</span>
        <span class="right">
          <el-tag size="small" type="info">{{ tc.llm_model }}</el-tag>
          <el-button text size="small" @click="viewCode(tc)">查看代码</el-button>
        </span>
      </div>
      <div v-if="!loading && cases.length === 0" class="empty">
        暂无用例 — 先导入文档，再点击「生成测试」
      </div>
    </div>

    <!-- Code Dialog -->
    <el-dialog v-model="codeDialog" :title="viewingName" width="700px" top="3vh">
      <div v-loading="codeLoading">
        <el-alert v-if="codeError" :title="codeError" type="error" show-icon style="margin-bottom:12px" />
        <pre class="code-block" v-if="viewingCode"><code>{{ viewingCode }}</code></pre>
      </div>
    </el-dialog>
  </div>
</template>

<style scoped>
.page { max-width: 1100px; }
.page-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 20px; }
.page-header h2 { font-size: 22px; font-weight: 600; color: #111; }
.count { font-weight: 400; font-size: 15px; color: #999; margin-left: 8px; }

.endpoint-list { background: #fff; border: 1px solid #eee; border-radius: 10px; overflow: hidden; }

.ep-row {
  display: flex; align-items: center; gap: 10px;
  padding: 10px 20px; border-bottom: 1px solid #f5f5f5; font-size: 14px;
}
.ep-row:last-child { border-bottom: none; }
.ep-row:hover { background: #fafafa; }

.method-tag { font-size: 12px; color: #666; font-weight: 600; min-width: 36px; }
.ep-path { font-size: 13px; color: #333; min-width: 140px; }
.name { color: #666; font-size: 13px; flex: 1; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
.right { margin-left: auto; display: flex; align-items: center; gap: 8px; flex-shrink: 0; }

.empty { text-align: center; padding: 60px 0; color: #999; font-size: 14px; }

.code-block {
  background: #1e1e2e; color: #a6e3a1; padding: 20px; border-radius: 8px;
  font-size: 13px; line-height: 1.6; overflow-x: auto; max-height: 68vh;
  white-space: pre; font-family: Consolas, monospace;
}
</style>
