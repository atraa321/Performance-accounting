import { useState, useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import {
  Table,
  Button,
  Space,
  Tag,
  Modal,
  Form,
  Input,
  Popconfirm,
  Card,
  Statistic,
  Row,
  Col,
} from 'antd'
import {
  PlusOutlined,
  FileExcelOutlined,
  CalculatorOutlined,
  LockOutlined,
  EyeOutlined,
  CopyOutlined,
  DeleteOutlined,
  ReloadOutlined,
} from '@ant-design/icons'
import type { ColumnsType } from 'antd/es/table'
import { runApi, type Run } from '@/api/run'
import dayjs from 'dayjs'
import { getMessageApi } from '@/lib/antdApp'

const RunList = () => {
  const navigate = useNavigate()
  const [runs, setRuns] = useState<Run[]>([])
  const [loading, setLoading] = useState(false)
  const [createModalOpen, setCreateModalOpen] = useState(false)
  const [form] = Form.useForm()

  useEffect(() => {
    loadRuns()
  }, [])

  const loadRuns = async () => {
    setLoading(true)
    try {
      const data = await runApi.list()
      setRuns(data)
    } catch (error) {
      console.error('加载批次列表失败:', error)
    } finally {
      setLoading(false)
    }
  }

  const handleCreate = async (values: any) => {
    try {
      await runApi.create(values)
      getMessageApi()?.success('批次创建成功')
      setCreateModalOpen(false)
      form.resetFields()
      loadRuns()
    } catch (error) {
      console.error('创建批次失败:', error)
    }
  }

  const handleLock = async (runId: number) => {
    try {
      await runApi.lock(runId)
      getMessageApi()?.success('批次已锁定')
      loadRuns()
    } catch (error) {
      console.error('锁定批次失败:', error)
    }
  }

  const handleRecalculate = async (runId: number) => {
    try {
      await runApi.calculate(runId)
      getMessageApi()?.success('重新计算完成')
      loadRuns()
    } catch (error: any) {
      if (error.response?.data?.detail) {
        getMessageApi()?.error(error.response.data.detail)
      } else {
        getMessageApi()?.error('重新计算失败')
      }
      console.error('重新计算失败:', error)
    }
  }

  const handleCopy = async (run: Run) => {
    Modal.confirm({
      title: '复制批次',
      content: (
        <Form
          id="copyForm"
          initialValues={{ new_month: dayjs().format('YYYY-MM') }}
        >
          <Form.Item
            name="new_month"
            label="新月份"
            rules={[{ required: true, message: '请输入月份' }]}
          >
            <Input placeholder="YYYY-MM" />
          </Form.Item>
        </Form>
      ),
      onOk: async () => {
        const formElement = document.getElementById('copyForm') as any
        const newMonth = formElement?.querySelector('input')?.value
        if (newMonth) {
          try {
            await runApi.copy(run.id, newMonth)
            getMessageApi()?.success('批次复制成功')
            loadRuns()
          } catch (error) {
            console.error('复制批次失败:', error)
          }
        }
      },
    })
  }

  const handleDelete = async (runId: number) => {
    try {
      await runApi.delete(runId)
      getMessageApi()?.success('批次删除成功')
      loadRuns()
    } catch (error: any) {
      if (error.response?.data?.detail) {
        getMessageApi()?.error(error.response.data.detail)
      } else {
        getMessageApi()?.error('删除批次失败')
      }
      console.error('删除批次失败:', error)
    }
  }

  const columns: ColumnsType<Run> = [
    {
      title: 'ID',
      dataIndex: 'id',
      key: 'id',
      width: 80,
    },
    {
      title: '月份',
      dataIndex: 'month',
      key: 'month',
      width: 120,
    },
    {
      title: '科室',
      dataIndex: 'dept_name',
      key: 'dept_name',
      width: 150,
    },
    {
      title: '规则版本',
      dataIndex: 'rule_version',
      key: 'rule_version',
      width: 120,
    },
    {
      title: '状态',
      dataIndex: 'status',
      key: 'status',
      width: 120,
      render: (status: string) => {
        const colorMap: Record<string, string> = {
          DRAFT: 'default',
          CALCULATED: 'success',
          LOCKED: 'error',
        }
        const textMap: Record<string, string> = {
          DRAFT: '草稿',
          CALCULATED: '已计算',
          LOCKED: '已锁定',
        }
        return <Tag color={colorMap[status]}>{textMap[status] || status}</Tag>
      },
    },
    {
      title: '创建时间',
      dataIndex: 'created_at',
      key: 'created_at',
      width: 180,
      render: (text: string) => dayjs(text).format('YYYY-MM-DD HH:mm:ss'),
    },
    {
      title: '操作',
      key: 'action',
      fixed: 'right',
      width: 420,
      render: (_, record) => (
        <Space size="small">
          <Button
            type="link"
            size="small"
            icon={<EyeOutlined />}
            onClick={() => navigate(`/runs/${record.id}`)}
          >
            查看
          </Button>
          <Button
            type="link"
            size="small"
            icon={<CopyOutlined />}
            onClick={() => handleCopy(record)}
          >
            复制
          </Button>
          {record.status !== 'LOCKED' && (
            <>
              {record.status === 'CALCULATED' && (
                <Popconfirm
                  title="确定要重新计算此批次吗？"
                  description="将根据最新规则参数重新计算，并覆盖原有计算结果"
                  onConfirm={() => handleRecalculate(record.id)}
                >
                  <Button type="link" size="small" icon={<ReloadOutlined />}>
                    重新计算
                  </Button>
                </Popconfirm>
              )}
              <Popconfirm
                title="确定要锁定此批次吗？"
                description="锁定后将无法修改"
                onConfirm={() => handleLock(record.id)}
              >
                <Button type="link" size="small" icon={<LockOutlined />} danger>
                  锁定
                </Button>
              </Popconfirm>
              <Popconfirm
                title="确定要删除此批次吗？"
                description="删除后将无法恢复，所有相关数据都会被删除"
                onConfirm={() => handleDelete(record.id)}
                okText="确定删除"
                cancelText="取消"
                okButtonProps={{ danger: true }}
              >
                <Button type="link" size="small" icon={<DeleteOutlined />} danger>
                  删除
                </Button>
              </Popconfirm>
            </>
          )}
        </Space>
      ),
    },
  ]

  // 统计数据
  const stats = {
    total: runs.length,
    draft: runs.filter((r) => r.status === 'DRAFT').length,
    calculated: runs.filter((r) => r.status === 'CALCULATED').length,
    locked: runs.filter((r) => r.status === 'LOCKED').length,
  }

  return (
    <div>
      <Row gutter={16} style={{ marginBottom: 24 }}>
        <Col span={6}>
          <Card>
            <Statistic title="总批次数" value={stats.total} />
          </Card>
        </Col>
        <Col span={6}>
          <Card>
            <Statistic title="草稿" value={stats.draft} valueStyle={{ color: '#999' }} />
          </Card>
        </Col>
        <Col span={6}>
          <Card>
            <Statistic title="已计算" value={stats.calculated} valueStyle={{ color: '#52c41a' }} />
          </Card>
        </Col>
        <Col span={6}>
          <Card>
            <Statistic title="已锁定" value={stats.locked} valueStyle={{ color: '#ff4d4f' }} />
          </Card>
        </Col>
      </Row>

      <div style={{ marginBottom: 16 }}>
        <Button
          type="primary"
          icon={<PlusOutlined />}
          onClick={() => setCreateModalOpen(true)}
        >
          新建批次
        </Button>
      </div>

      <Table
        columns={columns}
        dataSource={runs}
        rowKey="id"
        loading={loading}
        scroll={{ x: 1200 }}
      />

      <Modal
        title="新建批次"
        open={createModalOpen}
        onOk={() => form.submit()}
        onCancel={() => {
          setCreateModalOpen(false)
          form.resetFields()
        }}
      >
        <Form
          form={form}
          layout="vertical"
          onFinish={handleCreate}
          initialValues={{
            month: dayjs().format('YYYY-MM'),
            rule_version: 'default',
          }}
        >
          <Form.Item
            name="month"
            label="月份"
            rules={[{ required: true, message: '请输入月份' }]}
          >
            <Input placeholder="YYYY-MM" />
          </Form.Item>
          <Form.Item
            name="dept_name"
            label="科室名称"
            rules={[{ required: true, message: '请输入科室名称' }]}
          >
            <Input placeholder="例如：内科" />
          </Form.Item>
          <Form.Item
            name="rule_version"
            label="规则版本"
            rules={[{ required: true, message: '请输入规则版本' }]}
          >
            <Input placeholder="default" />
          </Form.Item>
        </Form>
      </Modal>
    </div>
  )
}

export default RunList
