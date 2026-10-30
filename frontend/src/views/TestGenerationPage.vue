<script setup lang="ts">
import { ref, onMounted, onUnmounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import apiClient from '@/api/client'
import { getEndpointsSummary } from '@/api/endpoints'

const route = useRoute()
const router = useRouter()
const projectId = route.params.id as string
const specId = route.params.specId as string

const generating = ref(false)
const status = ref('')
const result = ref<any>(null)
const error = ref('')
const strategy = ref('positive_only')
const maxPerEndpoint = ref(3)

// Progress tracking
const progress = ref({ endpoints_processed: 0, total_testcases_generated: 0 })
const totalEndpoints = ref(0)
let pollTimer: any = null

onMounted(async () => {
  try {
    const s = await getEndpointsSummary(specId)
    totalEndpoints.value = s.total
  } catch { /* ignore */ }
})

onUnmounted(() => {
  if (pollTimer) clearInterval(pollTimer)
})

const triggerGeneration = async () => {
  generating.value = true
  result.value = null
  error.value = ''
  progress.value = { endpoints_processed: 0, total_testcases_generated: 0 }
  status.value = 'requesting'

  try {
    // 1. Auto-fetch LLM provider
    let providerId = ''
    try {
      const { data: providers } = await apiClient.get('/llm/providers')
      const active = providers.items?.find((p: any) => p.is_active)
      if (active) providerId = active.id
    } catch { /* ignore */ }

    // 2. Trigger generation (returns immediately)
    const resp = await apiClient.post(`/specs/${specId}/generate`, {
      strategy: strategy.value,
      max_testcases_per_endpoint: maxPerEndpoint.value,
      review_enabled: false,
      llm_provider_id: providerId || undefined,
    })
    const genId = resp.data.generation_id
    status.value = 'polling'

    // 2. Poll for progress every 2 seconds
    pollTimer = setInterval(async () => {
      try {
        const { data: statusData } = await apiClient.get(
          `/specs/${specId}/generations/${genId}/status`
        )
        status.value = statusData.status
        progress.value = {
          endpoints_processed: statusData.endpoints_processed || 0,
          total_testcases_generated: statusData.total_testcases_generated || 0,
        }

        if (statusData.status === 'completed') {
          clearInterval(pollTimer)
          result.value = statusData
          generating.value = false
          ElMessage.success(`Completed: ${statusData.total_testcases_generated} tests`)
        } else if (statusData.status === 'failed') {
          clearInterval(pollTimer)
          error.value = statusData.errors?.join(', ') || 'Generation failed'
          generating.value = false
          ElMessage.error(error.value)
        }
      } catch (e) {
        // polling error, continue
      }
    }, 2000)

  } catch (e: any) {
    generating.value = false
    error.value = e.response?.data?.detail || e.message || 'Failed to start generation'
    ElMessage.error(error.value)
  }
}

const goToTestCases = () => {
  router.push(`/projects/${projectId}/testcases`)
}
</script>

<template>
  <div class="generation-page">
    <el-page-header @back="router.push(`/projects/${projectId}/specs/${specId}`)" title="AI 生成测试用例" />

    <el-row :gutter="24" style="margin-top: 20px">
      <el-col :span="7">
        <el-card>
          <template #header>配置</template>
          <el-form label-width="110px" size="default">
            <el-form-item label="策略">
              <el-select v-model="strategy" style="width: 100%">
                <el-option label="全部类型" value="all" />
                <el-option label="正向用例" value="positive_only" />
                <el-option label="负向用例" value="negative_only" />
                <el-option label="边界值测试" value="boundary_only" />
                <el-option label="安全测试" value="security_only" />
                <el-option label="Schema 校验" value="schema_only" />
              </el-select>
            </el-form-item>
            <el-form-item label="每接口用例数">
              <el-input-number v-model="maxPerEndpoint" :min="1" :max="10" style="width: 100%" />
            </el-form-item>
            <el-form-item>
              <el-button type="primary" :loading="generating" @click="triggerGeneration" style="width: 100%" size="large">
                <el-icon><MagicStick /></el-icon>
                {{ generating ? '生成中...' : '开始生成' }}
              </el-button>
            </el-form-item>
          </el-form>

          <div v-if="totalEndpoints > 0" style="margin-top: 12px; color: #909399; font-size: 13px">
            共 {{ totalEndpoints }} 个接口
          </div>
        </el-card>
      </el-col>

      <el-col :span="17">
        <!-- Error -->
        <el-alert v-if="error" :title="error" type="error" show-icon closable @close="error = ''" style="margin-bottom: 16px" />

        <!-- Progress -->
        <el-card v-if="generating" style="text-align: center">
          <div style="padding: 32px 0">
            <el-icon class="is-loading" :size="40" color="#409eff"><Loading /></el-icon>
            <h3 style="margin: 16px 0 8px">
              {{ status === 'requesting' ? '正在提交请求...' :
                 status === 'polling' && progress.endpoints_processed === 0 ? '正在连接 AI...' :
                 '正在生成...' }}
            </h3>
            <p v-if="progress.endpoints_processed > 0" style="font-size: 16px; color: #303133">
              已处理 <strong>{{ progress.endpoints_processed }}</strong> 个接口，
              生成 <strong>{{ progress.total_testcases_generated }}</strong> 条用例
            </p>
            <p v-else style="font-size: 14px; color: #909399">
              {{ status === 'requesting' ? '请稍候...' : 'DeepSeek 正在分析接口，约需 10-30 秒' }}
            </p>
          </div>
        </el-card>

        <!-- Result -->
        <el-card v-if="result">
          <template #header>
            <span>生成结果</span>
            <el-tag :type="result.status === 'completed' ? 'success' : 'danger'" style="margin-left: 8px">
              {{ result.status }}
            </el-tag>
          </template>

          <el-row :gutter="16">
            <el-col :span="8">
              <el-statistic title="处理接口" :value="result.endpoints_processed" />
            </el-col>
            <el-col :span="8">
              <el-statistic title="生成用例" :value="result.total_testcases_generated">
                <template #suffix>
                  <el-tag v-if="result.total_testcases_generated > 0" type="success" size="small">OK</el-tag>
                </template>
              </el-statistic>
            </el-col>
            <el-col :span="8">
              <el-statistic title="Prompt Tokens" :value="result.total_prompt_tokens" />
            </el-col>
          </el-row>

          <el-divider />
          <el-button type="primary" @click="goToTestCases">查看全部用例</el-button>
        </el-card>

        <!-- Empty -->
        <el-empty v-if="!result && !error && !generating" description="配置后点击「开始生成」" />
      </el-col>
    </el-row>
  </div>
</template>
