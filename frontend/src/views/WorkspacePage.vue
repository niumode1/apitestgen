<script setup lang="ts">
import { ref, computed, onMounted, onUnmounted } from 'vue'
import { useRoute } from 'vue-router'
import apiClient from '@/api/client'

const route = useRoute()
const wsId = route.params.id as string

// Workspace data
const ws = ref<any>(null)
const specs = ref<any[]>([])
const tab = ref<'endpoints'|'tests'|'executions'|'reports'>('endpoints')
const loading = ref(false)

// Upload
const uploading = ref(false)

// Generation
const generating = ref(false)
const genProgress = ref({ eps: 0, tests: 0 })

// Execution
const running = ref(false)
const execPoll: any = ref(null)

// Tests
const tests = ref<any[]>([])
const testTotal = ref(0)
const testFilter = ref('')

// Executions
const execs = ref<any[]>([])
const execDetailDialog = ref(false)
const execDetailResults = ref<any[]>([])
const viewingExecName = ref('')

const viewExecDetail = async (eid: string) => {
  const { data } = await apiClient.get(`/projects/${wsId}/executions/${eid}/results`, { params: { page_size: 50 } })
  execDetailResults.value = data.items || []
  viewingExecName.value = `Execution ${eid.slice(0,8)}`
  execDetailDialog.value = true
}

// Reports
const reports = ref<any[]>([])

// Selected spec
const activeSpecId = ref('')
const activeSpecEndpoints = ref<any[]>([])
const endpointSummary = ref<any>(null)

// Viewer
const codeDialog = ref(false)
const reportDialog = ref(false)
const viewingCode = ref('')
const viewingTitle = ref('')
const isReport = ref(false)

const catColors: Record<string, string> = {
  positive: 'success', negative: 'danger', boundary: 'warning',
  security: '', schema: 'info',
}
const catLabels: Record<string, string> = {
  positive: '正向', negative: '负向', boundary: '边界', security: '安全', schema: 'Schema',
}

// ── Data loading ──

const loadAll = async () => {
  loading.value = true
  try {
    // Workspace info
    const { data: w } = await apiClient.get(`/projects/${wsId}`)
    ws.value = w

    // Specs
    const { data: s } = await apiClient.get(`/projects/${wsId}/specs`)
    specs.value = s.items

    // Tests count
    const { data: t } = await apiClient.get(`/projects/${wsId}/testcases`, { params: { page_size: 1 } })
    testTotal.value = t.total

    // Executions
    const { data: e } = await apiClient.get(`/projects/${wsId}/executions`, { params: { page_size: 10 } })
    execs.value = e.items || []

    // Reports
    const { data: r } = await apiClient.get(`/projects/${wsId}/reports`, { params: { page_size: 10 } })
    reports.value = r.items || []
  } finally { loading.value = false }
}

const loadTests = async () => {
  const params: any = { page_size: 100 }
  if (testFilter.value) params.category = testFilter.value
  const { data } = await apiClient.get(`/projects/${wsId}/testcases`, { params })
  tests.value = data.items || []
}

const loadExecutions = async () => {
  const { data } = await apiClient.get(`/projects/${wsId}/executions`, { params: { page_size: 10 } })
  execs.value = data.items || []
}

const loadReports = async () => {
  const { data } = await apiClient.get(`/projects/${wsId}/reports`, { params: { page_size: 10 } })
  reports.value = data.items || []
}

// ── Actions ──

const handleUpload = async (file: any) => {
  uploading.value = true
  try {
    const formData = new FormData()
    formData.append('file', file)
    const { data } = await apiClient.post(`/projects/${wsId}/specs`, formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
    })
    if (data.id) activeSpecId.value = data.id
    await loadAll()
    if (activeSpecId.value) await loadEndpoints()
    tab.value = 'endpoints'
  } finally { uploading.value = false }
  return false
}

const deleteSpec = async (sid: string) => {
  await apiClient.delete(`/projects/${wsId}/specs/${sid}`)
  if (activeSpecId.value === sid) {
    activeSpecId.value = ''
    activeSpecEndpoints.value = []
  }
  await loadAll()
}

const selectSpec = async (sid: string) => {
  activeSpecId.value = sid
  await loadEndpoints()
  tab.value = 'endpoints'
}

const loadEndpoints = async () => {
  if (!activeSpecId.value) return
  const { data } = await apiClient.get(`/specs/${activeSpecId.value}/endpoints`, { params: { page_size: 200 } })
  activeSpecEndpoints.value = data.items || []
  try {
    const { data: s } = await apiClient.get(`/specs/${activeSpecId.value}/endpoints/summary`)
    endpointSummary.value = s
  } catch { }
}

const genStrategy = ref('positive_only')
const genCount = ref(3)

const generateTests = async () => {
  if (!activeSpecId.value) return
  generating.value = true
  genProgress.value = { eps: 0, tests: 0 }
  try {
    const { data } = await apiClient.post(`/specs/${activeSpecId.value}/generate`, {
      strategy: genStrategy.value,
      max_testcases_per_endpoint: genCount.value,
    })
    const gid = data.generation_id
    const poll = setInterval(async () => {
      try {
        const { data: st } = await apiClient.get(`/specs/${activeSpecId.value}/generations/${gid}/status`)
        genProgress.value = { eps: st.endpoints_processed || 0, tests: st.total_testcases_generated || 0 }
        if (st.status === 'completed') { clearInterval(poll); generating.value = false; await loadAll(); await loadTests() }
        if (st.status === 'failed') { clearInterval(poll); generating.value = false }
      } catch { }
    }, 2000)
  } catch { generating.value = false }
}

const runTests = async () => {
  running.value = true
  await apiClient.post(`/projects/${wsId}/executions`, {})
  execPoll.value = setInterval(async () => {
    await loadExecutions()
    const latest = execs.value[0]
    if (latest && latest.status !== 'running') {
      clearInterval(execPoll.value)
      running.value = false
      await loadAll()
    }
  }, 2000)
}

const generateReport = async (eid: string) => {
  await apiClient.post(`/projects/${wsId}/executions/${eid}/reports`)
  await loadReports()
  tab.value = 'reports'
}

const viewCode = async (tcId: string) => {
  const { data } = await apiClient.get(`/projects/${wsId}/testcases/${tcId}`)
  viewingCode.value = data.test_code || ''
  viewingTitle.value = data.name || 'Code'
  isReport.value = false
  codeDialog.value = true
}

const viewReport = async (rid: string) => {
  const { data } = await apiClient.get(`/projects/${wsId}/reports/${rid}`)
  viewingCode.value = data.content || ''
  viewingTitle.value = data.title || 'Report'
  isReport.value = true
  reportDialog.value = true
}

const renderedReport = computed(() => {
  if (!viewingCode.value) return ''
  return viewingCode.value
    .replace(/### (.+)/g, '<h3>$1</h3>')
    .replace(/## (.+)/g, '<h2>$1</h2>')
    .replace(/\*\*(.+?)\*\*/g, '<strong>$1</strong>')
    .replace(/```([^`]+)```/g, '<pre class="r-code">$1</pre>')
    .replace(/\n/g, '<br>')
})

const methodColors: Record<string, string> = {
  GET: 'success', POST: 'primary', PUT: 'warning', DELETE: 'danger', PATCH: 'info',
}

onMounted(async () => {
  await loadAll()
  if (specs.value.length > 0) {
    activeSpecId.value = specs.value[0].id
    await loadEndpoints()
  }
  await loadTests()
})

onUnmounted(() => { if (execPoll.value) clearInterval(execPoll.value) })
</script>

<template>
  <div class="workspace" v-loading="loading">
    <!-- Header -->
    <div class="ws-top">
      <div>
        <h2>{{ ws?.name || 'Loading...' }}</h2>
        <span class="sub" v-if="ws?.base_url">{{ ws.base_url }}</span>
      </div>
      <el-upload :show-file-list="false" :before-upload="(f:any) => handleUpload(f)" accept=".json,.yaml,.yml">
        <el-button type="primary" :loading="uploading">导入 OpenAPI</el-button>
      </el-upload>
    </div>

    <!-- Pipeline -->
    <!-- Pipeline -->
    <div class="pipeline">
      <div class="step done" @click="tab = 'endpoints'">
        <span class="dot">1</span> 导入
      </div>
      <div class="step" :class="{ done: activeSpecId, active: generating }" @click="activeSpecId && (tab = 'tests')">
        <span class="dot">2</span> 生成
      </div>
      <div class="step" :class="{ done: execs.length > 0, active: running }" @click="execs.length > 0 && (tab = 'executions')">
        <span class="dot">3</span> 执行
      </div>
      <div class="step" :class="{ done: reports.length > 0 }" @click="reports.length > 0 && (tab = 'reports')">
        <span class="dot">4</span> 报告
      </div>
    </div>

    <!-- Spec selector -->
    <div class="spec-tabs" v-if="specs.length > 0">
      <span
        v-for="s in specs" :key="s.id"
        class="spec-tab"
        :class="{ active: activeSpecId === s.id }"
        @click="selectSpec(s.id)"
      >
        {{ s.name }}
        <span class="count">{{ s.endpoint_count }}</span>
        <el-icon class="close" @click.stop="deleteSpec(s.id)"><Close /></el-icon>
      </span>
    </div>

    <!-- Generation progress -->
    <div v-if="generating" class="gen-bar">
      <el-icon class="is-loading"><Loading /></el-icon>
      生成中: {{ genProgress.eps }} 接口 / {{ genProgress.tests }} 用例
    </div>

    <!-- Content tabs -->
    <div class="tabs" v-if="activeSpecId">
      <button :class="{ active: tab === 'endpoints' }" @click="tab = 'endpoints'">接口 ({{ activeSpecEndpoints.length }})</button>
      <button :class="{ active: tab === 'tests' }" @click="tab = 'tests'">用例 ({{ testTotal }})</button>
      <button :class="{ active: tab === 'executions' }" @click="tab = 'executions'">执行 ({{ execs.length }})</button>
      <button :class="{ active: tab === 'reports' }" @click="tab = 'reports'">报告 ({{ reports.length }})</button>

      <div style="margin-left:auto;display:flex;gap:6px;align-items:center">
        <el-select v-if="activeSpecId" v-model="genStrategy" size="small" style="width:110px">
          <el-option label="正向" value="positive_only" />
          <el-option label="全部" value="all" />
          <el-option label="负向" value="negative_only" />
          <el-option label="边界" value="boundary_only" />
          <el-option label="安全" value="security_only" />
          <el-option label="Schema" value="schema_only" />
        </el-select>
        <el-button v-if="activeSpecId" size="small" type="primary" :loading="generating" @click="generateTests">生成</el-button>
        <el-button v-if="testTotal > 0" size="small" type="success" :loading="running" @click="runTests">执行</el-button>
      </div>
    </div>

    <div class="tab-content">
      <!-- Endpoints -->
      <div v-if="tab === 'endpoints'" class="list">
        <div v-if="endpointSummary" class="summary-bar">
          {{ endpointSummary.total }} 接口 ·
          GET {{ endpointSummary.by_method?.GET||0 }} ·
          POST {{ endpointSummary.by_method?.POST||0 }} ·
          PUT {{ endpointSummary.by_method?.PUT||0 }} ·
          DELETE {{ endpointSummary.by_method?.DELETE||0 }}
        </div>
        <div v-for="ep in activeSpecEndpoints" :key="ep.id" class="list-row">
          <el-tag :type="methodColors[ep.method] as any || 'info'" size="small" effect="dark">{{ ep.method }}</el-tag>
          <code>{{ ep.path }}</code>
          <span class="desc">{{ ep.summary }}</span>
        </div>
        <div v-if="activeSpecEndpoints.length === 0" class="empty">暂无接口</div>
      </div>

      <!-- Tests -->
      <div v-if="tab === 'tests'">
        <div style="margin-bottom:8px">
          <el-radio-group v-model="testFilter" size="small" @change="loadTests">
            <el-radio-button value="">全部</el-radio-button>
            <el-radio-button value="positive">正向</el-radio-button>
            <el-radio-button value="negative">负向</el-radio-button>
            <el-radio-button value="boundary">边界</el-radio-button>
            <el-radio-button value="security">安全</el-radio-button>
            <el-radio-button value="schema">Schema</el-radio-button>
          </el-radio-group>
        </div>
        <div class="list">
          <div v-for="tc in tests" :key="tc.id" class="list-row">
            <el-tag :type="catColors[tc.category] as any || 'info'" size="small" effect="dark">{{ catLabels[tc.category] || tc.category }}</el-tag>
            <span>{{ tc.endpoint_method }} {{ tc.endpoint_path }}</span>
            <span class="desc">{{ tc.name }}</span>
            <el-button text size="small" style="margin-left:auto" @click="viewCode(tc.id)">代码</el-button>
          </div>
          <div v-if="tests.length === 0" class="empty">暂无用例，点上方「生成测试」</div>
        </div>
      </div>

      <!-- Executions -->
      <div v-if="tab === 'executions'" class="list">
        <div v-for="e in execs" :key="e.id" class="list-row" style="cursor:pointer" @click="viewExecDetail(e.id)">
          <el-tag :type="e.status === 'completed' ? 'success' : e.status === 'running' ? 'warning' : 'info'" size="small" effect="dark">{{ e.status }}</el-tag>
          <span>{{ e.name }}</span>
          <span class="desc">
            <span style="color:#67c23a">{{ e.passed }} passed</span>
            <span v-if="e.failed" style="color:#f56c6c;margin-left:8px">{{ e.failed }} failed</span>
          </span>
          <span style="margin-left:auto;font-weight:600">{{ e.pass_rate }}%</span>
          <el-button size="small" style="margin-left:8px" @click="generateReport(e.id)">生成报告</el-button>
        </div>
        <div v-if="execs.length === 0" class="empty">暂无执行记录，点「执行测试」</div>
      </div>

      <!-- Reports -->
      <div v-if="tab === 'reports'" class="list">
        <div v-for="r in reports" :key="r.id" class="list-row">
          <el-tag :type="r.pass_rate > 80 ? 'success' : r.pass_rate > 50 ? 'warning' : 'danger'" size="small" effect="dark">{{ r.pass_rate }}%</el-tag>
          <span>{{ r.title }}</span>
          <span class="desc">{{ r.failed_count }} failed</span>
          <el-button size="small" style="margin-left:auto" @click="viewReport(r.id)">查看</el-button>
        </div>
        <div v-if="reports.length === 0" class="empty">暂无报告</div>
      </div>
    </div>

    <!-- Code viewer -->
    <el-dialog v-model="codeDialog" :title="viewingTitle" width="85vw" top="2vh">
      <pre class="code"><code>{{ viewingCode }}</code></pre>
    </el-dialog>

    <!-- Execution detail -->
    <el-dialog v-model="execDetailDialog" :title="viewingExecName" width="800px" top="3vh">
      <div class="list">
        <div v-for="r in execDetailResults" :key="r.id" class="list-row">
          <el-tag :type="r.status === 'passed' ? 'success' : 'danger'" size="small" effect="dark">{{ r.status }}</el-tag>
          <span style="flex:1;font-size:13px">{{ r.test_name.split('::').pop() || r.test_name }}</span>
          <span style="font-size:12px;color:#888" v-if="r.duration_ms">{{ r.duration_ms }}ms</span>
        </div>
        <div v-if="execDetailResults.length === 0" class="empty">No results</div>
      </div>
    </el-dialog>

    <!-- Report viewer -->
    <el-dialog v-model="reportDialog" :title="viewingTitle" width="90vw" top="2vh" class="report-dlg">
      <div class="report-body" v-html="renderedReport" />
    </el-dialog>
  </div>
</template>

<style scoped>
.workspace { max-width: 1040px; }

.ws-top {
  display: flex; justify-content: space-between; align-items: center;
  margin-bottom: 20px;
}
.ws-top h2 { font-size: 22px; font-weight: 600; color: #111; }
.sub { font-size: 13px; color: #999; }

/* Pipeline */
.pipeline {
  display: flex; gap: 0; margin-bottom: 20px;
  background: #fff; border: 1px solid #eee; border-radius: 10px; overflow: hidden;
}
.step {
  flex: 1; text-align: center; padding: 14px 0; font-size: 13px; color: #bbb;
  position: relative; cursor: pointer; transition: background 0.15s;
}
.step:hover { background: #f5f7fa; }
.step .dot {
  display: inline-flex; align-items: center; justify-content: center;
  width: 22px; height: 22px; border-radius: 50%;
  background: #eee; color: #999; font-size: 11px; font-weight: 700;
  margin-right: 6px;
}
.step.done { color: #67c23a; }
.step.done .dot { background: #67c23a; color: #fff; }
.step.active { color: #409eff; }
.step.active .dot { background: #409eff; color: #fff; animation: pulse 1s infinite; }
@keyframes pulse { 0%,100%{opacity:1} 50%{opacity:0.5} }

/* Spec tabs */
.spec-tabs { display: flex; gap: 4px; margin-bottom: 16px; }
.spec-tab {
  padding: 6px 14px; border-radius: 6px; font-size: 13px; cursor: pointer;
  border: 1px solid #eee; color: #666; display: flex; align-items: center; gap: 6px;
  transition: all 0.15s;
}
.spec-tab:hover { border-color: #409eff; color: #409eff; }
.spec-tab.active { background: #e8f0fe; border-color: #409eff; color: #409eff; font-weight: 600; }
.spec-tab .count { font-size: 11px; background: #f0f0f0; padding: 1px 6px; border-radius: 10px; }
.spec-tab .close { font-size: 12px; opacity: 0; transition: opacity 0.15s; }
.spec-tab:hover .close { opacity: 0.5; }
.spec-tab .close:hover { opacity: 1; color: #f56c6c; }

.gen-bar {
  display: flex; align-items: center; gap: 8px;
  padding: 10px 16px; margin-bottom: 16px;
  background: #e8f0fe; color: #409eff; border-radius: 8px; font-size: 14px;
}

/* Tabs */
.tabs {
  display: flex; gap: 0; border-bottom: 2px solid #eee; margin-bottom: 0;
  align-items: center; padding: 0 4px;
}
.tabs button {
  background: none; border: none; padding: 10px 16px; font-size: 14px;
  color: #888; cursor: pointer; border-bottom: 2px solid transparent;
  margin-bottom: -2px; transition: all 0.15s;
}
.tabs button:hover { color: #409eff; }
.tabs button.active { color: #409eff; border-bottom-color: #409eff; font-weight: 600; }

.tab-content { background: #fff; border: 1px solid #eee; border-top: none; border-radius: 0 0 10px 10px; }

/* Lists */
.list { min-height: 100px; }
.summary-bar { padding: 10px 20px; font-size: 13px; color: #888; border-bottom: 1px solid #f5f5f5; }
.list-row {
  display: flex; align-items: center; gap: 12px;
  padding: 10px 20px; border-bottom: 1px solid #f5f5f5; font-size: 14px;
}
.list-row:last-child { border-bottom: none; }
.list-row:hover { background: #fafafa; }
.list-row .desc { color: #888; font-size: 13px; flex: 1; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
.list-row code { font-size: 13px; color: #333; }

.empty { text-align: center; padding: 40px 0; color: #bbb; }

.code {
  background: #1e1e2e; color: #a6e3a1; padding: 20px; border-radius: 8px;
  font-size: 13px; line-height: 1.6; max-height: 82vh; overflow: auto;
  white-space: pre; font-family: Consolas, monospace;
}

/* Report viewer */
.report-body {
  font-size: 14px; line-height: 1.8; color: #333;
  max-height: 80vh; overflow-y: auto; padding: 10px;
}
.report-body :deep(h2) { font-size: 20px; margin: 20px 0 12px; color: #111; border-bottom: 2px solid #eee; padding-bottom: 8px; }
.report-body :deep(h3) { font-size: 16px; margin: 16px 0 8px; color: #333; }
.report-body :deep(strong) { color: #111; }
.report-body :deep(table) { border-collapse: collapse; width: 100%; margin: 12px 0; }
.report-body :deep(td) { border: 1px solid #ddd; padding: 8px 12px; font-size: 13px; }
.report-body :deep(.r-code) {
  background: #1e1e2e; color: #a6e3a1; padding: 14px; border-radius: 6px;
  font-size: 12px; line-height: 1.5; overflow-x: auto; font-family: Consolas, monospace; white-space: pre;
}
</style>
