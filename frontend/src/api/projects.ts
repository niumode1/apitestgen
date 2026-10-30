import apiClient from './client'

export interface Project {
  id: string
  name: string
  description: string
  base_url: string
  spec_count: number
  testcase_count: number
  execution_count: number
  created_at: string
  updated_at: string
}

export interface PaginatedResponse<T> {
  items: T[]
  total: number
  page: number
  page_size: number
  total_pages: number
}

export interface ProjectCreate {
  name: string
  description?: string
  base_url?: string
}

export interface ProjectUpdate {
  name?: string
  description?: string
  base_url?: string
}

export async function getProjects(params?: {
  page?: number
  page_size?: number
  search?: string
}): Promise<PaginatedResponse<Project>> {
  const { data } = await apiClient.get('/projects', { params })
  return data
}

export async function getProject(id: string): Promise<Project> {
  const { data } = await apiClient.get(`/projects/${id}`)
  return data
}

export async function createProject(body: ProjectCreate): Promise<Project> {
  const { data } = await apiClient.post('/projects', body)
  return data
}

export async function updateProject(id: string, body: ProjectUpdate): Promise<Project> {
  const { data } = await apiClient.put(`/projects/${id}`, body)
  return data
}

export async function deleteProject(id: string): Promise<{ message: string }> {
  const { data } = await apiClient.delete(`/projects/${id}`)
  return data
}
