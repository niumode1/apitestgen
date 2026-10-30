<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { ElMessageBox } from 'element-plus'
import { getProviders, createProvider, updateProvider, deleteProvider, testProvider, type LLMProvider } from '@/api/llm'

const providers = ref<LLMProvider[]>([])
const loading = ref(false)

const showDialog = ref(false)
const editId = ref<string | null>(null)
const form = ref({ name: '', provider_type: 'openai', api_base: 'https://api.openai.com/v1', api_key: '', default_model: 'gpt-4o-mini' })
const saving = ref(false)
const testing = ref(false)

const fetch = async () => {
  loading.value = true
  const res = await getProviders().finally(() => loading.value = false)
  providers.value = res.items
}

const openNew = () => {
  editId.value = null
  form.value = { name: '', provider_type: 'openai', api_base: 'https://api.openai.com/v1', api_key: '', default_model: 'gpt-4o-mini' }
  showDialog.value = true
}

const openEdit = (p: LLMProvider) => {
  editId.value = p.id
  form.value = { name: p.name, provider_type: p.provider_type, api_base: p.api_base, api_key: '', default_model: p.default_model }
  showDialog.value = true
}

const save = async () => {
  saving.value = true
  try {
    editId.value ? await updateProvider(editId.value, form.value) : await createProvider(form.value)
    showDialog.value = false
    await fetch()
  } finally { saving.value = false }
}

const testConn = async (p: LLMProvider) => {
  testing.value = true
  try {
    const res = await testProvider(p.id)
    ElMessageBox.alert(res.message, '连接测试')
  } finally { testing.value = false }
}

const remove = async (p: LLMProvider) => {
  try {
    await ElMessageBox.confirm(`删除「${p.name}」？`, '确认', { type: 'warning' })
    await deleteProvider(p.id)
    await fetch()
  } catch { /* cancelled */ }
}

const types: Record<string, string> = { openai: 'OpenAI', anthropic: 'Anthropic', openai_compatible: '兼容' }

onMounted(fetch)
</script>

<template>
  <div class="page">
    <div class="page-header">
      <h2>LLM 配置</h2>
      <el-button type="primary" @click="openNew">添加</el-button>
    </div>

    <div class="card-grid" v-loading="loading">
      <div v-for="p in providers" :key="p.id" class="card">
        <div class="card-body">
          <div class="card-row">
            <h4>{{ p.name }}</h4>
            <el-tag :type="p.is_active ? 'success' : 'info'" size="small">{{ p.is_active ? '启用' : '停用' }}</el-tag>
          </div>
          <p class="desc">{{ types[p.provider_type] || p.provider_type }} · {{ p.default_model }}</p>
          <p class="desc url">{{ p.api_base }}</p>
        </div>
        <div class="card-actions">
          <el-button text size="small" @click="testConn(p)" :loading="testing">测试</el-button>
          <el-button text size="small" @click="openEdit(p)">编辑</el-button>
          <el-button text type="danger" size="small" @click="remove(p)">删除</el-button>
        </div>
      </div>
    </div>

    <el-dialog v-model="showDialog" :title="editId ? '编辑' : '添加'" width="440px">
      <el-form :model="form" label-width="72px">
        <el-form-item label="名称" required>
          <el-input v-model="form.name" placeholder="DeepSeek" />
        </el-form-item>
        <el-form-item label="类型">
          <el-select v-model="form.provider_type" style="width:100%">
            <el-option label="OpenAI" value="openai" />
            <el-option label="Anthropic" value="anthropic" />
            <el-option label="兼容 OpenAI" value="openai_compatible" />
          </el-select>
        </el-form-item>
        <el-form-item label="API 地址" required>
          <el-input v-model="form.api_base" placeholder="https://api.deepseek.com" />
        </el-form-item>
        <el-form-item label="Key">
          <el-input v-model="form.api_key" type="password" show-password placeholder="sk-..." />
        </el-form-item>
        <el-form-item label="模型">
          <el-input v-model="form.default_model" placeholder="deepseek-chat" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="showDialog = false">取消</el-button>
        <el-button type="primary" :loading="saving" @click="save">保存</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<style scoped>
.page { max-width: 960px; }
.page-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 24px; }
.page-header h2 { font-size: 22px; font-weight: 600; color: #111; }

.card-grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(300px, 1fr)); gap: 16px; }

.card {
  background: #fff; border: 1px solid #eee; border-radius: 10px;
  display: flex; flex-direction: column;
}
.card-body { padding: 20px 20px 8px; flex: 1; }
.card-row { display: flex; justify-content: space-between; align-items: center; margin-bottom: 6px; }
.card-body h4 { font-size: 15px; color: #111; }
.card-body .desc { font-size: 13px; color: #999; }
.card-body .url { font-family: monospace; font-size: 12px; word-break: break-all; }
.card-actions { padding: 0 10px 10px; text-align: right; border-top: 1px solid #f5f5f5; margin: 8px 12px 0; padding-top: 8px; }
</style>
