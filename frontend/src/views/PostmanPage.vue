<script setup lang="ts">
import { ref } from 'vue'
import apiClient from '@/api/client'

const uploading = ref(false)
const importResult = ref<any>(null)
const exportReady = ref(false)
const exportJson = ref('')

const handleImport = async (file: any) => {
  uploading.value = true
  importResult.value = null
  try {
    const formData = new FormData()
    formData.append('file', file)
    const { data } = await apiClient.post('/postman/import', formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
    })
    importResult.value = data
  } catch (e: any) {
    importResult.value = { error: e.response?.data?.detail || 'Import failed' }
  } finally {
    uploading.value = false
  }
  return false
}

const handleExport = async () => {
  try {
    // Get first project
    const { data: projects } = await apiClient.get('/projects')
    const pid = projects.items?.[0]?.id
    if (!pid) { alert('No projects found'); return }

    const { data } = await apiClient.post('/postman/export', { project_id: pid })
    exportJson.value = JSON.stringify(data.collection, null, 2)
    exportReady.value = true

    // Download
    const blob = new Blob([exportJson.value], { type: 'application/json' })
    const url = URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url; a.download = 'postman_collection.json'; a.click()
    URL.revokeObjectURL(url)
  } catch (e: any) {
    alert(e.response?.data?.detail || 'Export failed')
  }
}
</script>

<template>
  <div class="page">
    <h2>Postman 导入 / 导出</h2>

    <el-row :gutter="24" style="margin-top: 20px">
      <el-col :span="12">
        <el-card>
          <template #header>导入 Postman 集合</template>
          <el-upload :show-file-list="false" :before-upload="handleImport" accept=".json" drag>
            <el-icon :size="48"><UploadFilled /></el-icon>
            <p>拖拽或点击上传 .json 文件</p>
            <p style="font-size:12px;color:#999">支持 Postman v2.1 格式</p>
          </el-upload>

          <div v-if="uploading" style="text-align:center;margin-top:12px">
            <el-icon class="is-loading"><Loading /></el-icon> 正在导入...
          </div>

          <div v-if="importResult && !importResult.error" style="margin-top:12px;padding:12px;background:#f0f9eb;border-radius:8px">
            <p>导入成功: {{ importResult.collection_name }}</p>
            <p>创建 {{ importResult.endpoint_count }} 个接口</p>
          </div>
          <div v-if="importResult?.error" style="margin-top:12px;padding:12px;background:#fef0f0;border-radius:8px;color:#f56c6c">
            {{ importResult.error }}
          </div>
        </el-card>
      </el-col>

      <el-col :span="12">
        <el-card>
          <template #header>导出为 Postman 集合</template>
          <p style="margin-bottom:16px;color:#666">将项目中的所有接口导出为 Postman Collection 文件</p>
          <el-button type="primary" @click="handleExport">导出并下载</el-button>

          <div v-if="exportReady" style="margin-top:16px">
            <el-input v-model="exportJson" type="textarea" :rows="10" readonly style="font-family:monospace;font-size:12px" />
          </div>
        </el-card>
      </el-col>
    </el-row>
  </div>
</template>

<style scoped>
.page { max-width: 960px; }
.page h2 { font-size: 22px; font-weight: 600; color: #111; margin-bottom: 8px; }
</style>
