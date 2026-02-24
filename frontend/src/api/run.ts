import api from './index'

export interface Run {
  id: number
  month: string
  dept_name: string
  rule_version: string
  status: string
  created_at: string
  locked_at?: string
}

export interface CreateRunDto {
  month: string
  dept_name: string
  rule_version: string
}

export interface Summary {
  name: string
  role: string
  direct_total: number
  pool_nursing: number
  pool_doctor: number
  surplus: number
  grand_total: number
}

export interface ManualEntry {
  name: string
  amount: number
}

export interface ManualEntryV2 {
  target_type: 'PERSON' | 'POOL'
  target_value: string
  item_type: 'WORKLOAD' | 'STUDY_LEAVE' | 'OTHER'
  amount: number
}

export interface ManualAllocatableItem {
  item_name: string
  amount: number
}

export interface ManualAllocatable {
  items: ManualAllocatableItem[]
}

export interface ValidationResult {
  is_valid: boolean
  error_count: number
  warning_count: number
  info_count: number
  errors: any[]
  warnings: any[]
  info: any[]
}

export interface NightShiftScheduleImportResult {
  status: string
  cleared_existing: boolean
  doctor_rows: number
  doctor_night_total: number
  nurse_rows: number
  nurse_night_total: number
  imported_rows: number
}

// 批次管理
export const runApi = {
  // 获取批次列表
  list: () => api.get<Run[]>('/runs'),

  // 创建批次
  create: (data: CreateRunDto) => api.post<Run>('/runs', data),

  // 锁定批次
  lock: (runId: number) => api.post(`/runs/${runId}/lock`),

  // 导入 Excel
  importExcel: (runId: number, file: File) => {
    const formData = new FormData()
    formData.append('file', file)
    return api.post(`/runs/${runId}/import/excel`, formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
    })
  },

  // 验证数据
  validate: (runId: number) => api.post<ValidationResult>(`/runs/${runId}/validate`),

  // 执行计算
  calculate: (runId: number) => api.post(`/runs/${runId}/calculate`),

  // 获取汇总
  getSummary: (runId: number) => api.get<{ rows: Summary[] }>(`/runs/${runId}/summary`),

  // 获取明细
  getDetail: (runId: number, name?: string) => 
    api.get(`/runs/${runId}/detail`, { params: { name } }),

  // 获取对账
  getReconcile: (runId: number) => api.get(`/runs/${runId}/reconcile`),

  // 获取异常
  getQc: (runId: number) => api.get(`/runs/${runId}/qc`),

  // 导出 Excel
  exportExcel: (runId: number) => {
    return api.get(`/runs/${runId}/export/excel`, {
      responseType: 'blob',
    })
  },
  // 导出 PDF
  exportPdf: (runId: number) => {
    return api.get(`/runs/${runId}/export/pdf`, {
      responseType: 'blob',
    })
  },

  // 手工录入：工作量
  getManualWorkload: (runId: number) => api.get<ManualEntry[]>(`/runs/${runId}/manual/workload`),
  saveManualWorkload: (runId: number, rows: ManualEntry[]) =>
    api.post(`/runs/${runId}/manual/workload`, { rows }),

  // 手工录入：进修产假补贴
  getManualStudyLeave: (runId: number) => api.get<ManualEntry[]>(`/runs/${runId}/manual/study-leave`),
  saveManualStudyLeave: (runId: number, rows: ManualEntry[]) =>
    api.post(`/runs/${runId}/manual/study-leave`, { rows }),

  // 手工录入：新版统一
  getManualEntries: (runId: number) => api.get<ManualEntryV2[]>(`/runs/${runId}/manual/entries`),
  saveManualEntries: (runId: number, rows: ManualEntryV2[]) =>
    api.post(`/runs/${runId}/manual/entries`, { rows }),
  getManualAllocatable: (runId: number) =>
    api.get<ManualAllocatable>(`/runs/${runId}/manual/allocatable`),

  // 原始名单
  getRoster: (runId: number) => api.get<any[]>(`/runs/${runId}/raw/roster`),

  // 原始数据表
  getRawSheet: (runId: number, sheet: string) => api.get<any[]>(`/runs/${runId}/raw/${sheet}`),
  saveRawSheet: (runId: number, sheet: string, rows: any[]) =>
    api.post(`/runs/${runId}/raw/${sheet}`, { rows }),
  importExcelSheet: (runId: number, sheet: string, file: File) => {
    const formData = new FormData()
    formData.append('file', file)
    return api.post(`/runs/${runId}/import/excel/sheet`, formData, {
      params: { sheet },
      headers: { 'Content-Type': 'multipart/form-data' },
    })
  },
  importNightShiftFromSchedules: (
    runId: number,
    doctorFile: File,
    nurseFile: File,
    clearExisting = true,
  ): Promise<NightShiftScheduleImportResult> => {
    const formData = new FormData()
    formData.append('doctor_file', doctorFile)
    formData.append('nurse_file', nurseFile)
    formData.append('clear_existing', String(clearExisting))
    return api.post<NightShiftScheduleImportResult>(`/runs/${runId}/import/night-shift/schedules`, formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
    }) as Promise<NightShiftScheduleImportResult>
  },

  // 批次对比
  compare: (runId1: number, runId2: number) => 
    api.get(`/runs/compare`, { params: { run_id_1: runId1, run_id_2: runId2 } }),

  // 复制批次
  copy: (runId: number, newMonth: string) => 
    api.post(`/runs/${runId}/copy`, { new_month: newMonth }),

  // 删除批次
  delete: (runId: number) => api.delete(`/runs/${runId}`),
}
