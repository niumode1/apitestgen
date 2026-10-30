import { ref } from 'vue'
import { defineStore } from 'pinia'
import { getProjects, type Project } from '@/api/projects'

export const useProjectStore = defineStore('project', () => {
  const projects = ref<Project[]>([])
  const currentProject = ref<Project | null>(null)
  const loading = ref(false)

  const fetchProjects = async () => {
    loading.value = true
    try {
      const res = await getProjects()
      projects.value = res.items
    } finally {
      loading.value = false
    }
  }

  return { projects, currentProject, loading, fetchProjects }
})
