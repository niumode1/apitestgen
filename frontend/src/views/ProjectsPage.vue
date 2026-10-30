<script setup lang="ts">
import { ref, onMounted, computed } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessageBox } from 'element-plus'
import { getProjects, createProject, deleteProject, type Project } from '@/api/projects'
import apiClient from '@/api/client'

const router = useRouter()
const projects = ref<Project[]>([])
const loading = ref(false)
const selected = ref<Set<string>>(new Set())
const deleting = ref(false)

const showDialog = ref(false)
const form = ref({ name: '', description: '', base_url: '' })
const saving = ref(false)

const allSelected = computed(() =>
  projects.value.length > 0 && selected.value.size === projects.value.length
)

const fetchProjects = async () => {
  loading.value = true
  selected.value = new Set()
  const res = await getProjects().finally(() => loading.value = false)
  projects.value = res.items
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
    selected.value = new Set(projects.value.map(p => p.id))
  }
}

const batchDelete = async () => {
  if (selected.value.size === 0) return
  try {
    await ElMessageBox.confirm(
      `Delete ${selected.value.size} projects? This cannot be undone.`,
      'Confirm',
      { type: 'warning', confirmButtonText: 'Delete', cancelButtonText: 'Cancel' }
    )
    deleting.value = true
    await apiClient.post('/projects/bulk-delete', { project_ids: [...selected.value] })
    await fetchProjects()
  } catch { /* cancelled */ }
  finally { deleting.value = false }
}

const handleCreate = async () => {
  if (!form.value.name.trim()) return
  saving.value = true
  try {
    await createProject(form.value)
    showDialog.value = false
    form.value = { name: '', description: '', base_url: '' }
    await fetchProjects()
  } finally { saving.value = false }
}

const handleDelete = async (p: Project) => {
  try {
    await ElMessageBox.confirm(`Delete "${p.name}"?`, 'Confirm', { type: 'warning' })
    await deleteProject(p.id)
    await fetchProjects()
  } catch { /* cancelled */ }
}

onMounted(fetchProjects)
</script>

<template>
  <div class="page">
    <div class="page-header">
      <h2>项目</h2>
      <div style="display:flex;gap:8px">
        <el-button v-if="selected.size > 0" type="danger" :loading="deleting" @click="batchDelete">
          删除 ({{ selected.size }})
        </el-button>
        <el-button type="primary" @click="showDialog = true">新建项目</el-button>
      </div>
    </div>

    <div v-if="projects.length > 0" style="margin-bottom:12px">
      <el-checkbox :model-value="allSelected" @change="toggleAll" label="全选" />
    </div>

    <div class="card-grid" v-loading="loading">
      <div v-for="p in projects" :key="p.id" class="card">
        <div class="card-check">
          <el-checkbox :model-value="selected.has(p.id)" @change="() => toggleSelect(p.id)" />
        </div>
        <div class="card-body" @click="router.push(`/projects/${p.id}`)">
          <h4>{{ p.name }}</h4>
          <p class="desc">{{ p.description || 'No description' }}</p>
          <div class="meta">
            <span>{{ p.spec_count }} docs</span>
            <span>{{ p.testcase_count }} tests</span>
            <span>{{ p.execution_count }} runs</span>
          </div>
        </div>
        <div class="card-actions">
          <el-button text type="danger" size="small" @click.stop="handleDelete(p)">删除</el-button>
        </div>
      </div>

      <div v-if="!loading && projects.length === 0" class="empty">
        <p>No projects yet. Click "New Project" to start.</p>
      </div>
    </div>

    <el-dialog v-model="showDialog" title="New Project" width="440px">
      <el-form :model="form" label-width="72px">
        <el-form-item label="Name" required>
          <el-input v-model="form.name" placeholder="Project name" />
        </el-form-item>
        <el-form-item label="Description">
          <el-input v-model="form.description" placeholder="Optional" />
        </el-form-item>
        <el-form-item label="Base URL">
          <el-input v-model="form.base_url" placeholder="http://localhost:9001" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="showDialog = false">Cancel</el-button>
        <el-button type="primary" :loading="saving" @click="handleCreate">Create</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<style scoped>
.page { max-width: 960px; }
.page-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 24px; }
.page-header h2 { font-size: 22px; font-weight: 600; color: #111; }

.card-grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(280px, 1fr)); gap: 16px; }

.card {
  background: #fff; border: 1px solid #eee; border-radius: 10px;
  transition: box-shadow 0.15s; display: flex; flex-direction: column; position: relative;
}
.card:hover { box-shadow: 0 2px 12px rgba(0,0,0,0.06); }
.card-check { position: absolute; top: 12px; left: 12px; z-index: 1; }

.card-body { padding: 20px 20px 12px; flex: 1; cursor: pointer; }
.card-body h4 { font-size: 15px; color: #111; margin-bottom: 6px; padding-left: 24px; }
.card-body .desc { font-size: 13px; color: #999; margin-bottom: 12px; line-height: 1.5; padding-left: 24px; }
.card-body .meta { display: flex; gap: 16px; font-size: 12px; color: #bbb; padding-left: 24px; }

.card-actions { padding: 0 12px 10px; text-align: right; }

.empty { grid-column: 1/-1; text-align: center; padding: 80px 0; color: #bbb; }
</style>
