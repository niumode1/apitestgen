<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import apiClient from '@/api/client'

const router = useRouter()
const summary = ref<any>(null)
const recent = ref<any[]>([])

onMounted(async () => {
  try {
    const [s, r] = await Promise.all([
      apiClient.get('/dashboard/summary'),
      apiClient.get('/dashboard/recent'),
    ])
    summary.value = s.data
    recent.value = r.data.activities || []
  } catch { /* ignore */ }
})

const catLabels: Record<string, string> = {
  positive: '正向', negative: '负向', boundary: '边界值',
  security: '安全', schema: 'Schema',
}
</script>

<template>
  <div class="page">
    <h2>仪表盘</h2>

    <!-- Stats Cards -->
    <el-row :gutter="16" style="margin: 20px 0" v-if="summary">
      <el-col :span="6"><el-card><el-statistic title="项目" :value="summary.total_projects" /></el-card></el-col>
      <el-col :span="6"><el-card><el-statistic title="接口" :value="summary.total_endpoints" /></el-card></el-col>
      <el-col :span="6"><el-card><el-statistic title="测试用例" :value="summary.total_testcases" /></el-card></el-col>
      <el-col :span="6"><el-card><el-statistic title="执行次数" :value="summary.total_executions" /></el-card></el-col>
    </el-row>

    <el-row :gutter="16" v-if="summary">
      <el-col :span="12">
        <el-card>
          <template #header>总通过率</template>
          <div style="text-align:center;padding:20px">
            <span style="font-size:48px;font-weight:700" :style="{ color: summary.overall_pass_rate > 80 ? '#67c23a' : summary.overall_pass_rate > 50 ? '#e6a23c' : '#f56c6c' }">
              {{ summary.overall_pass_rate }}%
            </span>
          </div>
        </el-card>
      </el-col>
      <el-col :span="12">
        <el-card>
          <template #header>用例分类</template>
          <div style="padding:8px">
            <el-tag v-for="(count, cat) in summary.testcases_by_category" :key="cat" style="margin:4px" size="large">
              {{ catLabels[cat] || cat }}: {{ count }}
            </el-tag>
          </div>
        </el-card>
      </el-col>
    </el-row>

    <!-- Recent Activity -->
    <el-card style="margin-top:16px" v-if="recent.length > 0">
      <template #header>最近活动</template>
      <div v-for="(a, i) in recent" :key="i" style="padding:8px 0;border-bottom:1px solid #f5f5f5">
        <strong>{{ a.title }}</strong> —
        {{ a.description }} —
        <span style="color:#999">{{ a.project_name }}</span>
        <span style="float:right;color:#bbb;font-size:12px">{{ new Date(a.timestamp).toLocaleString() }}</span>
      </div>
    </el-card>

    <el-empty v-if="!summary" description="暂无数据，创建一个项目开始" />
  </div>
</template>

<style scoped>
.page { max-width: 960px; }
.page h2 { font-size: 22px; font-weight: 600; color: #111; margin-bottom: 8px; }
</style>
