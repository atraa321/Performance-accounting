import { useEffect, useMemo, useState } from 'react'
import { useNavigate, useParams } from 'react-router-dom'
import {
  Button,
  Card,
  Form,
  Input,
  InputNumber,
  Modal,
  Space,
  Table,
  Upload,
  Select,
} from 'antd'
import { ArrowLeftOutlined, UploadOutlined, SaveOutlined, CalculatorOutlined } from '@ant-design/icons'
import type { UploadFile as AntdUploadFile, UploadProps } from 'antd'
import { runApi } from '@/api/run'
import { getMessageApi } from '@/lib/antdApp'

type FieldType = 'text' | 'number' | 'bool'

type SheetField = {
  key: string
  label: string
  type: FieldType
}

type SheetConfig = {
  key: string
  label: string
  fields: SheetField[]
}

const sheetConfigs: SheetConfig[] = [
  {
    key: 'hospital_perf_item',
    label: '院发绩效表',
    fields: [
      { key: 'item_name', label: '项目名', type: 'text' },
      { key: 'amount', label: '金额', type: 'number' },
    ],
  },
  {
    key: 'roster',
    label: '绩效发放名单',
    fields: [
      { key: 'name', label: '姓名', type: 'text' },
      { key: 'role', label: '岗位', type: 'text' },
      { key: 'perf_score', label: '绩效分数', type: 'number' },
      { key: 'eligible_for_surplus_weight', label: '参与盈余', type: 'bool' },
    ],
  },
  {
    key: 'night_shift',
    label: '夜班统计',
    fields: [
      { key: 'name', label: '姓名', type: 'text' },
      { key: 'night_count', label: '夜班数', type: 'number' },
    ],
  },
  {
    key: 'reading_fee',
    label: '判读费',
    fields: [
      { key: 'category', label: '类别', type: 'text' },
      { key: 'name', label: '姓名', type: 'text' },
      { key: 'amount', label: '金额', type: 'number' },
    ],
  },
  {
    key: 'doctor_workload',
    label: '医师工作量',
    fields: [
      { key: 'name', label: '姓名', type: 'text' },
      { key: 'workload', label: '工作量', type: 'number' },
      { key: 'bed_days', label: '床日数', type: 'number' },
      { key: 'admission_cert_count', label: '住院证数', type: 'number' },
    ],
  },
  {
    key: 'nurse_workload',
    label: '护士工作量',
    fields: [
      { key: 'name', label: '姓名', type: 'text' },
      { key: 'score', label: '分数', type: 'number' },
      { key: 'blood_draw_count', label: '抽血量', type: 'number' },
    ],
  },
]

const DataImportEdit = () => {
  const { runId } = useParams<{ runId: string }>()
  const navigate = useNavigate()
  const [loading, setLoading] = useState(false)
  const [sheetData, setSheetData] = useState<Record<string, any[]>>({})
  const [activeSheet, setActiveSheet] = useState<string>(sheetConfigs[0].key)
  const [editModalOpen, setEditModalOpen] = useState(false)
  const [editingIndex, setEditingIndex] = useState<number | null>(null)
  const [editingSheetKey, setEditingSheetKey] = useState<string | null>(null)
  const [nightScheduleModalOpen, setNightScheduleModalOpen] = useState(false)
  const [doctorScheduleFile, setDoctorScheduleFile] = useState<File | null>(null)
  const [nurseScheduleFile, setNurseScheduleFile] = useState<File | null>(null)
  const [editForm] = Form.useForm()

  useEffect(() => {
    if (!runId) return
    loadAllSheets()
  }, [runId])

  const loadAllSheets = async () => {
    if (!runId) return
    setLoading(true)
    try {
      const entries = await Promise.all(
        sheetConfigs.map(async (cfg) => {
          const rows = await runApi.getRawSheet(Number(runId), cfg.key)
          return [cfg.key, rows] as const
        }),
      )
      const next: Record<string, any[]> = {}
      entries.forEach(([key, rows]) => {
        next[key] = rows
      })
      setSheetData(next)
    } catch (error) {
      console.error('加载原始数据失败:', error)
    } finally {
      setLoading(false)
    }
  }

  const handleImportAll: UploadProps['customRequest'] = async (options) => {
    const { file, onSuccess, onError } = options
    try {
      setLoading(true)
      await runApi.importExcel(Number(runId), file as File)
      getMessageApi()?.success('总表导入成功')
      onSuccess?.('ok')
      await loadAllSheets()
    } catch (error) {
      console.error('导入失败:', error)
      onError?.(error as Error)
    } finally {
      setLoading(false)
    }
  }

  const handleImportSheet = (sheet: string): UploadProps['customRequest'] => {
    return async (options) => {
      const { file, onSuccess, onError } = options
      try {
        setLoading(true)
        await runApi.importExcelSheet(Number(runId), sheet, file as File)
        getMessageApi()?.success('分表导入成功')
        onSuccess?.('ok')
        await loadAllSheets()
      } catch (error) {
        console.error('导入失败:', error)
        onError?.(error as Error)
      } finally {
        setLoading(false)
      }
    }
  }

  const handleSaveSheet = async (sheet: string) => {
    if (!runId) return
    const rows = sheetData[sheet] || []
    await runApi.saveRawSheet(Number(runId), sheet, rows)
    getMessageApi()?.success('保存成功')
    await loadAllSheets()
  }

  const handleSaveAll = async () => {
    if (!runId) return
    setLoading(true)
    try {
      for (const cfg of sheetConfigs) {
        const rows = sheetData[cfg.key] || []
        await runApi.saveRawSheet(Number(runId), cfg.key, rows)
      }
      getMessageApi()?.success('全部保存成功')
      await loadAllSheets()
    } catch (error) {
      console.error('保存失败:', error)
    } finally {
      setLoading(false)
    }
  }

  const handleSaveAndCalculate = async () => {
    if (!runId) return
    setLoading(true)
    try {
      for (const cfg of sheetConfigs) {
        const rows = sheetData[cfg.key] || []
        await runApi.saveRawSheet(Number(runId), cfg.key, rows)
      }
      await runApi.calculate(Number(runId))
      getMessageApi()?.success('保存并计算完成')
    } catch (error) {
      console.error('保存并计算失败:', error)
    } finally {
      setLoading(false)
    }
  }

  const toUploadList = (file: File | null, uid: string): AntdUploadFile[] =>
    file
      ? [
          {
            uid,
            name: file.name,
            status: 'done',
            size: file.size,
            type: file.type,
          },
        ]
      : []

  const createNightScheduleUploadProps = (
    type: 'doctor' | 'nurse',
  ): UploadProps => {
    const file = type === 'doctor' ? doctorScheduleFile : nurseScheduleFile
    const setFile = type === 'doctor' ? setDoctorScheduleFile : setNurseScheduleFile
    return {
      accept: '.xls,.xlsx',
      maxCount: 1,
      beforeUpload: (nextFile) => {
        setFile(nextFile as File)
        return false
      },
      onRemove: () => {
        setFile(null)
      },
      fileList: toUploadList(file, `night-${type}`),
    }
  }

  const handleImportNightShiftFromSchedules = async () => {
    if (!runId) return
    if (!doctorScheduleFile || !nurseScheduleFile) {
      getMessageApi()?.warning('请先选择医师排班表和护理排班表')
      return
    }
    setLoading(true)
    try {
      const result = await runApi.importNightShiftFromSchedules(
        Number(runId),
        doctorScheduleFile,
        nurseScheduleFile,
        true,
      )
      getMessageApi()?.success(`夜班统计已更新，共 ${result.imported_rows} 人`)
      setNightScheduleModalOpen(false)
      setDoctorScheduleFile(null)
      setNurseScheduleFile(null)
      setActiveSheet('night_shift')
      await loadAllSheets()
    } catch (error) {
      console.error('按排班表计算夜班失败:', error)
    } finally {
      setLoading(false)
    }
  }

  const openEditor = (sheet: string, index: number | null) => {
    setEditingSheetKey(sheet)
    setEditingIndex(index)
    const row = index === null ? {} : (sheetData[sheet] || [])[index] || {}
    editForm.setFieldsValue(row)
    setEditModalOpen(true)
  }

  const handleDeleteRow = (sheet: string, index: number) => {
    setSheetData((prev) => ({
      ...prev,
      [sheet]: (prev[sheet] || []).filter((_, i) => i !== index),
    }))
  }

  const handleSaveRow = async () => {
    const values = await editForm.validateFields()
    if (!editingSheetKey) return
    setSheetData((prev) => {
      const rows = [...(prev[editingSheetKey] || [])]
      if (editingIndex === null) {
        rows.push(values)
      } else {
        rows[editingIndex] = { ...rows[editingIndex], ...values }
      }
      return { ...prev, [editingSheetKey]: rows }
    })
    setEditModalOpen(false)
    setEditingIndex(null)
    setEditingSheetKey(null)
    editForm.resetFields()
  }

  const activeConfig = useMemo(
    () => sheetConfigs.find((cfg) => cfg.key === activeSheet) || sheetConfigs[0],
    [activeSheet],
  )

  const renderEditorField = (field: SheetField) => {
    if (field.type === 'number') {
      return <InputNumber min={0} style={{ width: '100%' }} />
    }
    if (field.type === 'bool') {
      return (
        <Select
          options={[
            { label: '是', value: true },
            { label: '否', value: false },
          ]}
        />
      )
    }
    return <Input />
  }

  const columns = activeConfig.fields.map((field) => {
    return {
      title: field.label,
      dataIndex: field.key,
      key: field.key,
      render: (val: any) => {
        if (field.type === 'bool') {
          if (val === true) return '是'
          if (val === false) return '否'
        }
        return val
      },
    }
  })

  const dataSource = sheetData[activeConfig.key] || []

  return (
    <div>
      <Space style={{ marginBottom: 16 }}>
        <Button icon={<ArrowLeftOutlined />} onClick={() => navigate(`/runs/${runId}`)}>
          返回批次
        </Button>
        <Upload customRequest={handleImportAll} showUploadList={false} accept=".xlsx,.xls">
          <Button icon={<UploadOutlined />} loading={loading}>
            导入总表
          </Button>
        </Upload>
        <Button icon={<SaveOutlined />} onClick={handleSaveAll} loading={loading}>
          保存全部
        </Button>
        <Button icon={<CalculatorOutlined />} onClick={handleSaveAndCalculate} loading={loading}>
          保存并计算
        </Button>
        <Button onClick={() => setNightScheduleModalOpen(true)} loading={loading}>
          排班表算夜班
        </Button>
      </Space>

      <Space style={{ marginBottom: 16 }} wrap>
        {sheetConfigs.map((cfg) => (
          <Button
            key={cfg.key}
            type={cfg.key === activeSheet ? 'primary' : 'default'}
            onClick={() => setActiveSheet(cfg.key)}
          >
            {cfg.label}
          </Button>
        ))}
      </Space>

      <Card
        title={activeConfig.label}
        extra={
          <Space>
            <Upload
              customRequest={handleImportSheet(activeConfig.key)}
              showUploadList={false}
              accept=".xlsx,.xls"
            >
              <Button icon={<UploadOutlined />} loading={loading}>
                导入该表
              </Button>
            </Upload>
            <Button onClick={() => openEditor(activeConfig.key, null)}>新增</Button>
            <Button
              icon={<SaveOutlined />}
              onClick={() => handleSaveSheet(activeConfig.key)}
              loading={loading}
            >
              保存
            </Button>
            <Button
              icon={<CalculatorOutlined />}
              onClick={handleSaveAndCalculate}
              loading={loading}
            >
              保存并计算
            </Button>
          </Space>
        }
      >
        <Table
          columns={[
            ...columns,
            {
              title: '操作',
              key: 'action',
              width: 120,
              render: (_: any, __: any, index: number) => (
                <Space>
                  <Button type="link" onClick={() => openEditor(activeConfig.key, index)}>
                    编辑
                  </Button>
                  <Button type="link" danger onClick={() => handleDeleteRow(activeConfig.key, index)}>
                    删除
                  </Button>
                </Space>
              ),
            },
          ]}
          dataSource={dataSource}
          rowKey={(_, idx) => `${activeConfig.key}-${idx}`}
          loading={loading}
          pagination={{ pageSize: 20 }}
        />
      </Card>

      <Modal
        title={editingIndex === null ? '新增数据' : '编辑数据'}
        open={editModalOpen}
        onCancel={() => {
          setEditModalOpen(false)
          setEditingIndex(null)
          setEditingSheetKey(null)
          editForm.resetFields()
        }}
        onOk={handleSaveRow}
      >
        <Form form={editForm} layout="vertical">
          {activeConfig.fields.map((field) => (
            <Form.Item
              key={field.key}
              name={field.key}
              label={field.label}
              rules={[{ required: field.key === 'name' || field.key === 'item_name', message: '必填' }]}
            >
              {renderEditorField(field)}
            </Form.Item>
          ))}
        </Form>
      </Modal>

      <Modal
        title="根据排班表自动计算夜班"
        open={nightScheduleModalOpen}
        onCancel={() => {
          setNightScheduleModalOpen(false)
          setDoctorScheduleFile(null)
          setNurseScheduleFile(null)
        }}
        onOk={handleImportNightShiftFromSchedules}
        okText="导入并覆盖夜班统计"
        confirmLoading={loading}
      >
        <Space direction="vertical" style={{ width: '100%' }}>
          <Upload {...createNightScheduleUploadProps('doctor')} showUploadList>
            <Button icon={<UploadOutlined />}>选择医师组排班表（.xls/.xlsx）</Button>
          </Upload>
          <Upload {...createNightScheduleUploadProps('nurse')} showUploadList>
            <Button icon={<UploadOutlined />}>选择护理组排班表（.xls/.xlsx）</Button>
          </Upload>
        </Space>
      </Modal>
    </div>
  )
}

export default DataImportEdit
