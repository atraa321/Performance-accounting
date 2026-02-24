import { useState, useEffect } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import {
  Tabs,
  Button,
  Upload,
  Space,
  Table,
  Card,
  Statistic,
  Row,
  Col,
  Alert,
  Tag,
  Modal,
  Descriptions,
  Form,
  InputNumber,
  Select,
} from 'antd'
import {
  UploadOutlined,
  CalculatorOutlined,
  DownloadOutlined,
  CheckCircleOutlined,
  ExclamationCircleOutlined,
  ArrowLeftOutlined,
} from '@ant-design/icons'
import type { UploadProps } from 'antd'
import { runApi, type ManualAllocatable, type ManualEntryV2, type Summary } from '@/api/run'
import { getMessageApi } from '@/lib/antdApp'

const RunDetail = () => {
  const { runId } = useParams<{ runId: string }>()
  const navigate = useNavigate()
  const [loading, setLoading] = useState(false)
  const [summary, setSummary] = useState<Summary[]>([])
  const [validation, setValidation] = useState<any>(null)
  const [qcIssues, setQcIssues] = useState<any[]>([])
  const [reconcile, setReconcile] = useState<any[]>([])
  const [activeTab, setActiveTab] = useState('summary')
  const [manualEntries, setManualEntries] = useState<ManualEntryV2[]>([])
  const [manualModalOpen, setManualModalOpen] = useState(false)
  const [manualForm] = Form.useForm()
  const [rosterOptions, setRosterOptions] = useState<{ label: string; value: string }[]>([])
  const [manualAllocatable, setManualAllocatable] = useState<ManualAllocatable>({ items: [] })
  const [editingManualIndex, setEditingManualIndex] = useState<number | null>(null)

  useEffect(() => {
    if (runId) {
      loadSummary()
      loadQc()
      loadReconcile()
      loadManualEntries()
      loadManualAllocatable()
      loadRoster()
    }
  }, [runId])

  const loadSummary = async () => {
    try {
      const data = await runApi.getSummary(Number(runId))
      const roleRank = (role: string) => {
        if (role.includes('科主任')) return 0
        if (role.includes('副主任')) return 1
        if (role.includes('医师')) return 2
        if (role.includes('护士长')) return 3
        if (role.includes('护士') || role.includes('护理')) return 4
        return 9
      }
      const sorted = [...data.rows].sort((a, b) => {
        const rankA = roleRank(a.role || '')
        const rankB = roleRank(b.role || '')
        if (rankA !== rankB) return rankA - rankB
        return a.name.localeCompare(b.name, 'zh-Hans-CN')
      })
      setSummary(sorted)
    } catch (error) {
      console.error('加载汇总失败:', error)
    }
  }

  const loadQc = async () => {
    try {
      const data = await runApi.getQc(Number(runId))
      setQcIssues(data)
    } catch (error) {
      console.error('加载异常失败:', error)
    }
  }

  const loadReconcile = async () => {
    try {
      const data = await runApi.getReconcile(Number(runId))
      setReconcile(data)
    } catch (error) {
      console.error('加载对账失败:', error)
    }
  }

  const loadManualEntries = async () => {
    try {
      const data = await runApi.getManualEntries(Number(runId))
      setManualEntries(data)
    } catch (error) {
      console.error('加载手工录入失败:', error)
    }
  }

  const loadRoster = async () => {
    try {
      const data = await runApi.getRoster(Number(runId))
      const options: { label: string; value: string }[] = []
      const seen = new Set<string>()
      data.forEach((row: any) => {
        const name = String(row.name || '').trim()
        if (!name) return
        if (seen.has(name)) return
        seen.add(name)
        const role = String(row.role || '').trim()
        const label = role ? `${name}（${role}）` : name
        options.push({ label, value: name })
      })
      setRosterOptions(options)
    } catch (error) {
      console.error('加载绩效发放名单失败:', error)
    }
  }

  const loadManualAllocatable = async () => {
    try {
      const data = await runApi.getManualAllocatable(Number(runId))
      setManualAllocatable(data)
    } catch (error) {
      console.error('加载手工项目可分配金额失败:', error)
    }
  }

  const handleUpload: UploadProps['customRequest'] = async (options) => {
    const { file, onSuccess, onError } = options
    try {
      setLoading(true)
      await runApi.importExcel(Number(runId), file as File)
      getMessageApi()?.success('Excel 导入成功')
      onSuccess?.('ok')
      loadQc()
      loadRoster()
      loadManualAllocatable()
    } catch (error) {
      console.error('导入失败:', error)
      onError?.(error as Error)
    } finally {
      setLoading(false)
    }
  }

  const handleValidate = async () => {
    try {
      setLoading(true)
      const result = await runApi.validate(Number(runId))
      setValidation(result)
      Modal.info({
        title: '数据验证结果',
        width: 600,
        content: (
          <div>
            <Descriptions column={2} size="small">
              <Descriptions.Item label="验证状态">
                {result.is_valid ? (
                  <Tag color="success">通过</Tag>
                ) : (
                  <Tag color="error">未通过</Tag>
                )}
              </Descriptions.Item>
              <Descriptions.Item label="错误数">{result.error_count}</Descriptions.Item>
              <Descriptions.Item label="警告数">{result.warning_count}</Descriptions.Item>
              <Descriptions.Item label="信息数">{result.info_count}</Descriptions.Item>
            </Descriptions>
            {result.errors.length > 0 && (
              <div style={{ marginTop: 16 }}>
                <h4>错误：</h4>
                {result.errors.map((err: any, idx: number) => (
                  <Alert key={idx} message={err.message} type="error" style={{ marginBottom: 8 }} />
                ))}
              </div>
            )}
            {result.warnings.length > 0 && (
              <div style={{ marginTop: 16 }}>
                <h4>警告：</h4>
                {result.warnings.slice(0, 5).map((warn: any, idx: number) => (
                  <Alert key={idx} message={warn.message} type="warning" style={{ marginBottom: 8 }} />
                ))}
              </div>
            )}
          </div>
        ),
      })
      loadQc()
    } catch (error) {
      console.error('验证失败:', error)
    } finally {
      setLoading(false)
    }
  }

  const handleCalculate = async () => {
    Modal.confirm({
      title: '确认计算',
      content: '确定要执行绩效计算吗？',
      onOk: async () => {
        try {
          setLoading(true)
          await runApi.calculate(Number(runId))
          getMessageApi()?.success('计算完成')
          loadSummary()
          loadReconcile()
        } catch (error) {
          console.error('计算失败:', error)
        } finally {
          setLoading(false)
        }
      },
    })
  }

  const handleExport = async () => {
    try {
      const blob = await runApi.exportExcel(Number(runId))
      const url = window.URL.createObjectURL(blob as any)
      const a = document.createElement('a')
      a.href = url
      a.download = `run_${runId}_export.xlsx`
      a.click()
      window.URL.revokeObjectURL(url)
      getMessageApi()?.success('导出成功')
    } catch (error) {
      console.error('导出失败:', error)
    }
  }

  const handleExportPdf = async () => {
    try {
      const blob = await runApi.exportPdf(Number(runId))
      const url = window.URL.createObjectURL(blob as any)
      const a = document.createElement('a')
      a.href = url
      a.download = `run_${runId}_export.pdf`
      a.click()
      window.URL.revokeObjectURL(url)
      getMessageApi()?.success('PDF 导出成功')
    } catch (error) {
      console.error('PDF 导出失败:', error)
    }
  }

  const handleManualRecalculate = async () => {
    if (!runId) return
    try {
      setLoading(true)
      await runApi.saveManualEntries(Number(runId), manualEntries)
      await runApi.calculate(Number(runId))
      getMessageApi()?.success('已保存并重新计算')
      loadSummary()
      loadReconcile()
    } catch (error) {
      console.error('重新计算失败:', error)
    } finally {
      setLoading(false)
    }
  }

  const manualColumns = (onEdit: (index: number) => void, onRemove: (index: number) => void) => [
    {
      title: '对象',
      dataIndex: 'target_type',
      key: 'target_type',
      width: 100,
      render: (val: string) => (val === 'POOL' ? '池子' : '个人'),
    },
    {
      title: '姓名/池子',
      dataIndex: 'target_value',
      key: 'target_value',
      width: 140,
      render: (val: string, record: ManualEntryV2) => {
        if (record.target_type === 'POOL') {
          if (val === 'NURSING_POOL') return '护士池'
          if (val === 'DOCTOR_POOL') return '医生池'
        }
        return val
      },
    },
    {
      title: '项目',
      dataIndex: 'item_type',
      key: 'item_type',
      width: 140,
      render: (val: string) => {
        if (val === 'WORKLOAD') return '工作量'
        if (val === 'STUDY_LEAVE') return '进修产假补贴'
        if (val === 'OTHER') return '其他'
        return val
      },
    },
    {
      title: '金额',
      dataIndex: 'amount',
      key: 'amount',
      width: 120,
      render: (val: number) => val.toFixed(2),
    },
    {
      title: '操作',
      key: 'action',
      width: 80,
      render: (_: any, __: ManualEntryV2, index: number) => (
        <Space>
          <Button type="link" onClick={() => onEdit(index)}>
            编辑
          </Button>
          <Button type="link" danger onClick={() => onRemove(index)}>
            删除
          </Button>
        </Space>
      ),
    },
  ]

  const summaryColumns = [
    { title: '姓名', dataIndex: 'name', key: 'name', width: 100 },
    { title: '岗位', dataIndex: 'role', key: 'role', width: 120 },
    {
      title: '直接发放',
      dataIndex: 'direct_total',
      key: 'direct_total',
      width: 120,
      render: (val: number) => val.toFixed(2),
    },
    {
      title: '护理池',
      dataIndex: 'pool_nursing',
      key: 'pool_nursing',
      width: 120,
      render: (val: number) => val.toFixed(2),
    },
    {
      title: '医师池',
      dataIndex: 'pool_doctor',
      key: 'pool_doctor',
      width: 120,
      render: (val: number) => val.toFixed(2),
    },
    {
      title: '合计',
      dataIndex: 'grand_total',
      key: 'grand_total',
      width: 120,
      render: (val: number) => <strong>{val.toFixed(2)}</strong>,
    },
  ]

  const qcColumns = [
    { title: '类型', dataIndex: 'issue_type', key: 'issue_type', width: 200 },
    { title: '消息', dataIndex: 'message', key: 'message' },
    {
      title: '严重级别',
      dataIndex: 'severity',
      key: 'severity',
      width: 100,
      render: (val: string) => (
        <Tag color={val === 'ERROR' ? 'error' : 'warning'}>{val}</Tag>
      ),
    },
  ]

  const reconcileColumns = [
    // 按需求：在对账中，“项目编码”这一列展示原始项目名（来自后端返回的 item_name）
    { title: '项目编码', dataIndex: 'item_name', key: 'item_name', width: 240 },
    {
      title: '来源金额',
      dataIndex: 'source_amount',
      key: 'source_amount',
      width: 120,
      render: (val: number) => val.toFixed(2),
    },
    {
      title: '已分配',
      dataIndex: 'allocated_amount',
      key: 'allocated_amount',
      width: 120,
      render: (val: number) => val.toFixed(2),
    },
    {
      title: '差额',
      dataIndex: 'delta',
      key: 'delta',
      width: 120,
      render: (val: number) => (
        <span style={{ color: Math.abs(val) > 0.01 ? 'red' : 'inherit' }}>
          {val.toFixed(2)}
        </span>
      ),
    },
    { title: '备注', dataIndex: 'note', key: 'note' },
  ]

  const manualTotal = manualEntries.reduce((sum, item) => sum + item.amount, 0)
  const allocationBalance = reconcile.reduce((sum, item) => sum + (item.delta ?? 0), 0)
  const allocatedTotal = reconcile.reduce((sum, item) => sum + (item.allocated_amount ?? 0), 0)
  const sourceTotal = reconcile.reduce((sum, item) => sum + (item.source_amount ?? 0), 0)

  const tabItems = [
    {
      key: 'summary',
      label: '汇总结果',
      children: (
        <Table
          columns={summaryColumns}
          dataSource={summary}
          rowKey="name"
          scroll={{ x: 900 }}
          pagination={{ pageSize: 20 }}
        />
      ),
    },
    {
      key: 'manual',
      label: '手工录入',
      children: (
        <Card
          title="手工录入"
          extra={
            <Space>
              <Button
                onClick={() => {
                  manualForm.resetFields()
                  setEditingManualIndex(null)
                  setManualModalOpen(true)
                }}
              >
                新增
              </Button>
              <Button
                icon={<CalculatorOutlined />}
                onClick={handleManualRecalculate}
                loading={loading}
              >
                重新计算
              </Button>
              <Button
                onClick={async () => {
                  if (!runId) return
                  await runApi.saveManualEntries(Number(runId), manualEntries)
                  getMessageApi()?.success('手工录入已保存')
                }}
              >
                保存
              </Button>
              <Button
                danger
                onClick={async () => {
                  if (!runId) return
                  await runApi.saveManualEntries(Number(runId), [])
                  setManualEntries([])
                  getMessageApi()?.success('已清空手工录入')
                }}
              >
                清空
              </Button>
            </Space>
          }
        >
          <Table
            columns={manualColumns(
              (index) => {
                const entry = manualEntries[index]
                if (!entry) return
                manualForm.setFieldsValue(entry)
                setEditingManualIndex(index)
                setManualModalOpen(true)
              },
              (index) => {
                setManualEntries((prev) => prev.filter((_, i) => i !== index))
              },
            )}
            dataSource={manualEntries}
            rowKey={(row, idx) => `${row.target_type}-${row.target_value}-${row.item_type}-${idx}`}
            pagination={{ pageSize: 10 }}
          />
          <div style={{ textAlign: 'right', marginTop: 12 }}>
            <span>手工分配合计：</span>
            <strong>{manualTotal.toFixed(2)}</strong>
          </div>
        </Card>
      ),
    },
    {
      key: 'qc',
      label: `异常 (${qcIssues.length})`,
      children: <Table columns={qcColumns} dataSource={qcIssues} rowKey="id" />,
    },
    {
      key: 'reconcile',
      label: '对账',
      children: <Table columns={reconcileColumns} dataSource={reconcile} rowKey="item_code" />,
    },
  ]

  const personOptions = rosterOptions
  const poolOptions = [
    { label: '护士池', value: 'NURSING_POOL' },
    { label: '医生池', value: 'DOCTOR_POOL' },
  ]
  const itemOptions = manualAllocatable.items.map((item) => ({
    label: `${item.item_name}（${item.amount.toFixed(2)}）`,
    value: item.item_name,
  }))

  return (
    <div>
      <div style={{ marginBottom: 16 }}>
        <Space>
          <Button icon={<ArrowLeftOutlined />} onClick={() => navigate('/runs')}>
            返回
          </Button>
          <Upload customRequest={handleUpload} showUploadList={false} accept=".xlsx,.xls">
            <Button icon={<UploadOutlined />} loading={loading}>
              导入 Excel
            </Button>
          </Upload>
          <Button onClick={() => navigate(`/runs/${runId}/data-edit`)}>
            数据编辑
          </Button>
          <Button icon={<CheckCircleOutlined />} onClick={handleValidate} loading={loading}>
            验证数据
          </Button>
          <Button
            type="primary"
            icon={<CalculatorOutlined />}
            onClick={handleCalculate}
            loading={loading}
          >
            执行计算
          </Button>
          <Button icon={<DownloadOutlined />} onClick={handleExport}>
            导出 Excel
          </Button>
          <Button icon={<DownloadOutlined />} onClick={handleExportPdf}>
            导出 PDF
          </Button>
        </Space>
      </div>

      {qcIssues.length > 0 && (
        <Alert
          message={`发现 ${qcIssues.length} 个异常问题`}
          type="warning"
          showIcon
          icon={<ExclamationCircleOutlined />}
          style={{ marginBottom: 16 }}
          action={
            <Button size="small" onClick={() => setActiveTab('qc')}>
              查看详情
            </Button>
          }
        />
      )}

      <Row gutter={16} style={{ marginBottom: 24 }}>
        <Col span={6}>
          <Card>
            <Statistic title="总人数" value={summary.length} suffix="人" />
          </Card>
        </Col>
        <Col span={6}>
          <Card>
            <Statistic
              title="院发绩效总数"
              value={sourceTotal}
              precision={2}
              suffix="元"
              valueStyle={{ color: '#3f8600' }}
            />
          </Card>
        </Col>
        <Col span={6}>
          <Card>
            <Statistic title="已分配金额" value={allocatedTotal} precision={2} suffix="元" />
          </Card>
        </Col>
        <Col span={6}>
          <Card>
            <Statistic
              title="分配余额"
              value={allocationBalance}
              precision={2}
              suffix="元"
            />
          </Card>
        </Col>
      </Row>

      <Tabs activeKey={activeTab} onChange={setActiveTab} items={tabItems} />

      <Modal
        title={editingManualIndex === null ? '新增手工分配' : '编辑手工分配'}
        open={manualModalOpen}
        onCancel={() => {
          setManualModalOpen(false)
          setEditingManualIndex(null)
          manualForm.resetFields()
        }}
        onOk={async () => {
          const values = await manualForm.validateFields()
          if (editingManualIndex === null) {
            setManualEntries((prev) => [...prev, values])
          } else {
            setManualEntries((prev) =>
              prev.map((entry, idx) => (idx === editingManualIndex ? values : entry)),
            )
          }
          manualForm.resetFields()
          setManualModalOpen(false)
          setEditingManualIndex(null)
        }}
      >
        <Form form={manualForm} layout="vertical">
          <Form.Item
            name="target_type"
            label="分配对象"
            rules={[{ required: true, message: '请选择分配对象' }]}
          >
            <Select
              options={[
                { label: '个人', value: 'PERSON' },
                { label: '池子', value: 'POOL' },
              ]}
              placeholder="选择个人或池子"
              onChange={() => {
                manualForm.setFieldValue('target_value', undefined)
              }}
            />
          </Form.Item>
          <Form.Item
            shouldUpdate={(prev, curr) => prev.target_type !== curr.target_type}
            noStyle
          >
            {() => {
              const targetType = manualForm.getFieldValue('target_type')
              const options = targetType === 'POOL' ? poolOptions : personOptions
              const label = targetType === 'POOL' ? '选择池子' : '选择人员'
              return (
                <Form.Item
                  name="target_value"
                  label={label}
                  rules={[{ required: true, message: '请选择分配对象' }]}
                >
                  <Select
                    options={options}
                    showSearch
                    optionFilterProp="label"
                    placeholder={label}
                  />
                </Form.Item>
              )
            }}
          </Form.Item>
          <Form.Item
            name="item_type"
            label="项目"
            rules={[{ required: true, message: '请选择项目' }]}
          >
            <Select options={itemOptions} placeholder="选择项目" />
          </Form.Item>
          <Form.Item
            shouldUpdate={(prev, curr) => prev.item_type !== curr.item_type || prev.amount !== curr.amount}
            noStyle
          >
            {() => {
              const itemType = manualForm.getFieldValue('item_type') as string | undefined
              if (!itemType) {
                return null
              }
              const allocatable =
                manualAllocatable.items.find((item) => item.item_name === itemType)?.amount ?? 0
              const used = manualEntries
                .filter((entry) => entry.item_type === itemType)
                .reduce((sum, entry) => sum + entry.amount, 0)
              const remain = allocatable - used
              return (
                <div style={{ marginBottom: 12, color: '#666' }}>
                  可分配金额：{allocatable.toFixed(2)}，已录入：{used.toFixed(2)}，剩余：{remain.toFixed(2)}
                </div>
              )
            }}
          </Form.Item>
          <Form.Item name="amount" label="金额" rules={[{ required: true, message: '请输入金额' }]}>
            <InputNumber min={0} style={{ width: '100%' }} />
          </Form.Item>
        </Form>
      </Modal>
    </div>
  )
}

export default RunDetail
