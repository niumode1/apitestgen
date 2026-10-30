import apiClient from './client'

export interface SpecResponse {
  id: string
  project_id: string
  name: string
  version: string
  spec_format: string
  parse_status: string
  parse_error?: string
  endpoint_count: number
  imported_at?: string
  created_at: string
  updated_at: string
}

export interface SpecUploadResponse {
  id: string
  name: string
  version: string
  spec_format: string
  parse_status: string
  endpoint_count: number
  message: string
}

export async function uploadSpec(
  projectId: string,
  file: File
): Promise<SpecUploadResponse> {
  const formData = new FormData()
  formData.append('file', file)
  const { data } = await apiClient.post(`/projects/${projectId}/specs`, formData, {
    headers: { 'Content-Type': 'multipart/form-data' },
  })
  return data
}

export async function getSpecs(projectId: string, params?: {
  page?: number
  page_size?: number
}): Promise<any> {
  const { data } = await apiClient.get(`/projects/${projectId}/specs`, { params })
  return data
}

export async function getSpec(specId: string, projectId: string): Promise<SpecResponse> {
  const { data } = await apiClient.get(`/projects/${projectId}/specs/${specId}`)
  return data
}

export async function deleteSpec(specId: string, projectId: string): Promise<{ message: string }> {
  const { data } = await apiClient.delete(`/projects/${projectId}/specs/${specId}`)
  return data
}
