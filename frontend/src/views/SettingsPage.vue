<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { ElMessageBox } from 'element-plus'
import { getProviders, createProvider, updateProvider, deleteProvider, testProvider, type LLMProvider } from '@/api/llm'

const providers = ref<LLMProvider[]>([])
const loading = ref(false)
const dialog = ref(false)
const editId = ref<string | null>(null)
const form = ref({ name: '', provider_type: 'openai', api_base: 'https://api.openai.com/v1', api_key: '', default_model: 'gpt-4o-mini' })
const saving = ref(false)

const fetch = async () => {
  loading.value = true
  const res = await getProviders().finally(() => loading.value = false)
  providers.value = res.items
}

const open = (p?: LLMProvider) => {
  editId.value = p?.id || null
  form.value = p
    ? { name: p.name, provider_type: p.provider_type, api_base: p.api_base, api_key: '', default_model: p.default_model }
    : { name: '', provider_type: 'openai', api_base: 'https://api.openai.com/v1', api_key: '', default_model: 'gpt-4o-mini' }
  dialog.value = true
}

const save = async () => {
  saving.value = true
  try {
    editId.value ? await updateProvider(editId.value, form.value) : await createProvider(form.value)
    dialog.value = false; await fetch()
  } finally { saving.value = false }
}

const remove = async (p: LLMProvider) => {
  try { await ElMessageBox.confirm(`Delete "${p.name}"?`, 'Confirm', { type: 'warning' }); await deleteProvider(p.id); await fetch() } catch { }
}

const typeLabels: Record<string, string> = { openai: 'OpenAI', anthropic: 'Anthropic', openai_compatible: 'Compatible' }

onMounted(fetch)
</script>

<template>
  <div class="page">
    <div class="header"><h2>LLM 配置</h2><el-button type="primary" @click="open()">添加</el-button></div>

    <div class="grid" v-loading="loading">
      <div v-for="p in providers" :key="p.id" class="card">
        <div class="card-body">
          <div class="row"><h4>{{ p.name }}</h4><el-tag :type="p.is_active?'success':'info'" size="small">{{ p.is_active?'Active':'Off' }}</el-tag></div>
          <p class="desc">{{ typeLabels[p.provider_type] }} · {{ p.default_model }}</p>
          <p class="url">{{ p.api_base }}</p>
        </div>
        <div class="card-actions">
          <el-button text size="small" @click="testProvider(p.id)">Test</el-button>
          <el-button text size="small" @click="open(p)">Edit</el-button>
          <el-button text type="danger" size="small" @click="remove(p)">Delete</el-button>
        </div>
      </div>
    </div>

    <el-dialog v-model="dialog" :title="editId?'Edit':'Add'" width="440px">
      <el-form :model="form" label-width="72px">
        <el-form-item label="Name" required><el-input v-model="form.name" /></el-form-item>
        <el-form-item label="Type"><el-select v-model="form.provider_type" style="width:100%"><el-option label="OpenAI" value="openai" /><el-option label="Anthropic" value="anthropic" /><el-option label="Compatible" value="openai_compatible" /></el-select></el-form-item>
        <el-form-item label="API URL"><el-input v-model="form.api_base" /></el-form-item>
        <el-form-item label="Key"><el-input v-model="form.api_key" type="password" show-password /></el-form-item>
        <el-form-item label="Model"><el-input v-model="form.default_model" /></el-form-item>
      </el-form>
      <template #footer><el-button @click="dialog=false">Cancel</el-button><el-button type="primary" :loading="saving" @click="save">Save</el-button></template>
    </el-dialog>
  </div>
</template>

<style scoped>
.page { max-width: 960px; }
.header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 24px; }
.header h2 { font-size: 22px; font-weight: 600; color: #111; }

.grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(300px, 1fr)); gap: 16px; }
.card { background: #fff; border: 1px solid #eee; border-radius: 10px; display: flex; flex-direction: column; }
.card-body { padding: 20px 20px 8px; flex: 1; }
.card-body h4 { font-size: 15px; color: #111; }
.row { display: flex; justify-content: space-between; align-items: center; margin-bottom: 6px; }
.desc { font-size: 13px; color: #999; }
.url { font-size: 12px; color: #bbb; font-family: monospace; word-break: break-all; margin-top: 4px; }
.card-actions { padding: 8px 12px; border-top: 1px solid #f5f5f5; text-align: right; }
</style>
