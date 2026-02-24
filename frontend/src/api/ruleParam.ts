import api from './index'

export interface RuleParam {
  id: number
  param_key: string
  param_value: string
  param_value_num?: number
  param_desc?: string
}

export interface UpdateRuleParamDto {
  param_value: string
  param_value_num?: number
  param_desc?: string
}

// 规则参数管理
export const ruleParamApi = {
  // 获取所有参数
  list: () => api.get<RuleParam[]>('/rule-params'),

  // 获取单个参数
  get: (paramKey: string) => api.get<RuleParam>(`/rule-params/${paramKey}`),

  // 更新参数
  update: (paramKey: string, data: UpdateRuleParamDto) => 
    api.put<RuleParam>(`/rule-params/${paramKey}`, data),

  // 按类别获取
  getByCategory: () => api.get<Record<string, RuleParam[]>>('/rule-params/grouped/by-category'),

  // 批量更新
  batchUpdate: (updates: any[]) => 
    api.post('/rule-params/batch-update', { updates }),
}
