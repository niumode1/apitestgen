<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessageBox } from 'element-plus'
import { getProjects, createProject, deleteProject, type Project } from '@/api/projects'
import apiClient from '@/api/client'

const router = useRouter()
const projects = ref<Project[]>([])
const loading = ref(false)
const shownNew = ref(false)
const form = ref({ name: '', base_url: 'http://localhost:9001' })
const saving = ref(false)
const selected = ref<Set<string>>(new Set())

const fetch = async () => {
  loading.value = true
  const res = await getProjects().finally(() => loading.value = false)
  projects.value = res.items
  selected.value = new Set()
}

const create = async () => {
  if (!form.value.name.trim()) return
  saving.value = true
  try {
    await createProject(form.value)
    shownNew.value = false
    form.value = { name: '', base_url: 'http://localhost:9001' }
    await fetch()
  } finally { saving.value = false }
}

const batchDelete = async () => {
  if (selected.value.size === 0) return
  try {
    await ElMessageBox.confirm(`Delete ${selected.value.size} workspaces?`, 'Confirm', { type: 'warning' })
    await apiClient.post('/projects/bulk-delete', { project_ids: [...selected.value] })
    await fetch()
  } catch { }
}

const toggle = (id: string) => {
  const s = new Set(selected.value)
  s.has(id) ? s.delete(id) : s.add(id)
  selected.value = s
}

onMounted(fetch)
</script>

<template>
  <div class="page">
    <div class="header">
      <h2>工作区</h2>
      <div style="display:flex;gap:8px">
        <el-button v-if="selected.size > 0" type="danger" @click="batchDelete">删除 ({{ selected.size }})</el-button>
        <el-button type="primary" @click="shownNew = true">新建工作区</el-button>
      </div>
    </div>

    <div class="grid" v-loading="loading">
      <div v-for="p in projects" :key="p.id" class="card" @click="router.push(`/workspaces/${p.id}`)">
        <el-checkbox :model-value="selected.has(p.id)" @click.stop @change="() => toggle(p.id)" style="position:absolute;top:12px;left:12px" />
        <div class="card-inner">
          <h4>{{ p.name }}</h4>
          <p class="url" v-if="p.base_url">{{ p.base_url }}</p>
          <div class="meta">
            <span>{{ p.spec_count }} 文档</span>
            <span>{{ p.testcase_count }} 用例</span>
            <span>{{ p.execution_count }} 执行</span>
          </div>
        </div>
      </div>
    </div>

    <el-dialog v-model="shownNew" title="新建工作区" width="400px">
      <el-form :model="form" label-width="72px">
        <el-form-item label="名称" required><el-input v-model="form.name" placeholder="My API" /></el-form-item>
        <el-form-item label="Base URL"><el-input v-model="form.base_url" placeholder="http://localhost:8080" /></el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="shownNew = false">Cancel</el-button>
        <el-button type="primary" :loading="saving" @click="create">Create</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<style scoped>
.page { max-width: 960px; }
.header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 24px; }
.header h2 { font-size: 22px; font-weight: 600; color: #111; }

.grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(280px, 1fr)); gap: 16px; }

.card {
  background: #fff; border: 1px solid #eee; border-radius: 10px;
  cursor: pointer; position: relative; transition: box-shadow 0.15s;
}
.card:hover { box-shadow: 0 2px 12px rgba(0,0,0,0.06); }
.card-inner { padding: 20px; padding-left: 40px; }
.card-inner h4 { font-size: 15px; color: #111; margin-bottom: 4px; }
.url { font-size: 12px; color: #aaa; font-family: monospace; margin-bottom: 10px; }
.meta { display: flex; gap: 16px; font-size: 12px; color: #bbb; }
</style>
