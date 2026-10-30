import apiClient from './client'

export interface EndpointBrief {
  id: string
  path: string
  method: string
  summary: string
  tags: string[]
  deprecated: boolean
  analyzed_at?: string
  testcase_count: number
}

export interface EndpointDetail {
  id: string
  spec_id: string
  path: string
  method: string
  summary: string
  description: string
  operation_id: string
  tags: string[]
  parameters: any[]
  request_body?: any
  responses: Record<string, any>
  security?: any[]
  deprecated: boolean
  analyzed_at?: string
  analysis?: any
  testcase_count: number
  created_at: string
  updated_at: string
}

export interface EndpointSummary {
  total: number
  by_method: Record<string, number>
  by_tag: Record<string, number>
  deprecated_count: number
}

export async function getEndpoints(specId: string, params?: {
  method?: string
  tag?: string
  search?: string
  page?: number
  page_size?: number
}): Promise<any> {
  const { data } = await apiClient.get(`/specs/${specId}/endpoints`, { params })
  return data
}

export async function getEndpoint(specId: string, endpointId: string): Promise<EndpointDetail> {
  const { data } = await apiClient.get(`/specs/${specId}/endpoints/${endpointId}`)
  return data
}

export async function getEndpointsSummary(specId: string): Promise<EndpointSummary> {
  const { data } = await apiClient.get(`/specs/${specId}/endpoints/summary`)
  return data
}
