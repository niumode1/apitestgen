import apiClient from './client'

export interface LLMProvider {
  id: string
  name: string
  provider_type: string
  api_base: string
  default_model: string
  extra_params: Record<string, any>
  is_active: boolean
  created_at: string
  updated_at: string
}

export interface LLMProviderCreate {
  name: string
  provider_type: string
  api_base: string
  api_key?: string
  default_model: string
  extra_params?: Record<string, any>
  is_active?: boolean
}

export async function getProviders(params?: {
  page?: number
  page_size?: number
}): Promise<any> {
  const { data } = await apiClient.get('/llm/providers', { params })
  return data
}

export async function createProvider(body: LLMProviderCreate): Promise<LLMProvider> {
  const { data } = await apiClient.post('/llm/providers', body)
  return data
}

export async function updateProvider(id: string, body: Partial<LLMProviderCreate>): Promise<LLMProvider> {
  const { data } = await apiClient.put(`/llm/providers/${id}`, body)
  return data
}

export async function deleteProvider(id: string): Promise<{ message: string }> {
  const { data } = await apiClient.delete(`/llm/providers/${id}`)
  return data
}

export async function testProvider(id: string): Promise<any> {
  const { data } = await apiClient.post(`/llm/providers/${id}/test`)
  return data
}
