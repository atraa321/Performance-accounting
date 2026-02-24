import api from './index'

export interface AuditLog {
  id: number
  run_id?: number
  operation_type: string
  operation_name: string
  operator?: string
  details?: string
  payload?: any
  status: string
  error_message?: string
  created_at: string
  ip_address?: string
}

// 审计日志
export const auditApi = {
  // 获取日志列表
  list: (params?: {
    run_id?: number
    operation_type?: string
    status?: string
    limit?: number
    offset?: number
  }) => api.get<{ logs: AuditLog[]; limit: number; offset: number }>('/audit-logs', { params }),

  // 获取统计
  getStats: (days: number = 7) => 
    api.get('/audit-logs/stats', { params: { days } }),

  // 获取操作类型
  getTypes: () => api.get('/audit-logs/types'),
}
