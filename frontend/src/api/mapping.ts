import api from './index'

export interface ItemMapping {
  id: number
  raw_item_name: string
  item_code: string
  priority: number
  is_active: boolean
  behavior_type?: string | null
}

export interface ItemBehavior {
  id: number
  item_code: string
  behavior_type: string
}

export interface AvailableBehaviorType {
  code: string
  name: string
  description: string
}

// 项目映射管理
export const mappingApi = {
  // 获取所有映射
  list: (isActive?: boolean): Promise<ItemMapping[]> =>
    api.get<ItemMapping[]>('/mappings', { params: { is_active: isActive } }) as Promise<ItemMapping[]>,

  // 创建映射
  create: (data: Omit<ItemMapping, 'id'>): Promise<ItemMapping> =>
    api.post<ItemMapping>('/mappings', data) as Promise<ItemMapping>,

  // 更新映射
  update: (id: number, data: Partial<ItemMapping>): Promise<ItemMapping> =>
    api.put<ItemMapping>(`/mappings/${id}`, data) as Promise<ItemMapping>,

  // 删除映射
  delete: (id: number) => api.delete(`/mappings/${id}`),

  // 获取未映射项目
  getUnmatched: (runId?: number): Promise<{ items: string[]; count: number }> =>
    api.get<{ items: string[]; count: number }>('/mapping/unmatched', { params: { run_id: runId } }) as Promise<{ items: string[]; count: number }>,

  // 获取所有行为
  listBehaviors: (): Promise<ItemBehavior[]> => api.get<ItemBehavior[]>('/item-behaviors') as Promise<ItemBehavior[]>,

  // 获取可用行为类型
  getAvailableTypes: (): Promise<{ types: AvailableBehaviorType[] }> =>
    api.get<{ types: AvailableBehaviorType[] }>('/item-behaviors/types/available') as Promise<{ types: AvailableBehaviorType[] }>,
}
