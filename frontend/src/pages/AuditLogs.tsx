import { useState, useEffect } from 'react'
import { Table, Card, Tag, Space, Select, DatePicker, Button, Row, Col, Statistic } from 'antd'
import { ReloadOutlined, FilterOutlined } from '@ant-design/icons'
import type { ColumnsType } from 'antd/es/table'
import { auditApi, type AuditLog } from '@/api/audit'
import dayjs from 'dayjs'

const { RangePicker } = DatePicker

const AuditLogs = () => {
  const [logs, setLogs] = useState<AuditLog[]>([])
  const [stats, setStats] = useState<any>(null)
  const [operationTypes, setOperationTypes] = useState<any[]>([])
  const [loading, setLoading] = useState(false)
  const [filters, setFilters] = useState({
    operation_type: undefined,
    status: undefined,
    limit: 100,
    offset: 0,
  })

  useEffect(() => {
    loadLogs()
    loadStats()
    loadOperationTypes()
  }, [filters])

  const loadLogs = async () => {
    setLoading(true)
    try {
      const data = await auditApi.list(filters)
      setLogs(data.logs)
    } catch (error) {
      console.error('加载日志失败:', error)
    } finally {
      setLoading(false)
    }
  }

  const loadStats = async () => {
    try {
      const data = await auditApi.getStats(7)
      setStats(data)
    } catch (error) {
      console.error('加载统计失败:', error)
    }
  }

  const loadOperationTypes = async () => {
    try {
      const data = await auditApi.getTypes()
      setOperationTypes(data.types)
    } catch (error) {
      console.error('加载操作类型失败:', error)
    }
  }

  const handleFilterChange = (key: string, value: any) => {
    setFilters((prev) => ({ ...prev, [key]: value, offset: 0 }))
  }

  const handleReset = () => {
    setFilters({
      operation_type: undefined,
      status: undefined,
      limit: 100,
      offset: 0,
    })
  }

  const columns: ColumnsType<AuditLog> = [
    {
      title: 'ID',
      dataIndex: 'id',
      key: 'id',
      width: 80,
    },
    {
      title: '批次ID',
      dataIndex: 'run_id',
      key: 'run_id',
      width: 100,
      render: (val: number) => val || '-',
    },
    {
      title: '操作类型',
      dataIndex: 'operation_type',
      key: 'operation_type',
      width: 150,
      render: (type: string) => {
        const typeObj = operationTypes.find((t) => t.code === type)
        return <Tag color="blue">{typeObj?.name || type}</Tag>
      },
    },
    {
      title: '操作名称',
      dataIndex: 'operation_name',
      key: 'operation_name',
      width: 150,
    },
    {
      title: '详情',
      dataIndex: 'details',
      key: 'details',
      ellipsis: true,
    },
    {
      title: '状态',
      dataIndex: 'status',
      key: 'status',
      width: 100,
      render: (status: string) => (
        <Tag color={status === 'SUCCESS' ? 'success' : 'error'}>
          {status === 'SUCCESS' ? '成功' : '失败'}
        </Tag>
      ),
    },
    {
      title: '操作时间',
      dataIndex: 'created_at',
      key: 'created_at',
      width: 180,
      render: (text: string) => dayjs(text).format('YYYY-MM-DD HH:mm:ss'),
    },
  ]

  return (
    <div>
      <Row gutter={16} style={{ marginBottom: 24 }}>
        <Col span={6}>
          <Card>
            <Statistic
              title="总操作数（7天）"
              value={stats?.total_operations || 0}
            />
          </Card>
        </Col>
        <Col span={6}>
          <Card>
            <Statistic
              title="成功率"
              value={stats?.success_rate || 0}
              precision={2}
              suffix="%"
              valueStyle={{ color: '#3f8600' }}
            />
          </Card>
        </Col>
        <Col span={6}>
          <Card>
            <Statistic
              title="成功"
              value={stats?.by_status?.SUCCESS || 0}
              valueStyle={{ color: '#52c41a' }}
            />
          </Card>
        </Col>
        <Col span={6}>
          <Card>
            <Statistic
              title="失败"
              value={stats?.by_status?.FAILED || 0}
              valueStyle={{ color: '#ff4d4f' }}
            />
          </Card>
        </Col>
      </Row>

      <Card
        title="审计日志"
        extra={
          <Space>
            <Select
              placeholder="操作类型"
              style={{ width: 150 }}
              allowClear
              value={filters.operation_type}
              onChange={(val) => handleFilterChange('operation_type', val)}
            >
              {operationTypes.map((type) => (
                <Select.Option key={type.code} value={type.code}>
                  {type.name}
                </Select.Option>
              ))}
            </Select>
            <Select
              placeholder="状态"
              style={{ width: 120 }}
              allowClear
              value={filters.status}
              onChange={(val) => handleFilterChange('status', val)}
            >
              <Select.Option value="SUCCESS">成功</Select.Option>
              <Select.Option value="FAILED">失败</Select.Option>
            </Select>
            <Button icon={<ReloadOutlined />} onClick={handleReset}>
              重置
            </Button>
          </Space>
        }
      >
        <Table
          columns={columns}
          dataSource={logs}
          rowKey="id"
          loading={loading}
          scroll={{ x: 1200 }}
          pagination={{
            current: filters.offset / filters.limit + 1,
            pageSize: filters.limit,
            total: logs.length >= filters.limit ? (filters.offset + filters.limit + 1) : (filters.offset + logs.length),
            onChange: (page, pageSize) => {
              setFilters((prev) => ({
                ...prev,
                offset: (page - 1) * pageSize,
                limit: pageSize,
              }))
            },
          }}
          expandable={{
            expandedRowRender: (record) => (
              <div style={{ padding: 16, background: '#fafafa' }}>
                <Space direction="vertical" style={{ width: '100%' }}>
                  {record.operator && (
                    <div>
                      <strong>操作人：</strong>
                      {record.operator}
                    </div>
                  )}
                  {record.ip_address && (
                    <div>
                      <strong>IP地址：</strong>
                      {record.ip_address}
                    </div>
                  )}
                  {record.error_message && (
                    <div>
                      <strong>错误信息：</strong>
                      <span style={{ color: 'red' }}>{record.error_message}</span>
                    </div>
                  )}
                  {record.payload && (
                    <div>
                      <strong>详细数据：</strong>
                      <pre style={{ background: '#fff', padding: 8, borderRadius: 4 }}>
                        {JSON.stringify(record.payload, null, 2)}
                      </pre>
                    </div>
                  )}
                </Space>
              </div>
            ),
          }}
        />
      </Card>

      {stats?.by_type && (
        <Card title="操作类型统计（7天）" style={{ marginTop: 16 }}>
          <Space direction="vertical" style={{ width: '100%' }}>
            {Object.entries(stats.by_type).map(([type, count]: [string, any]) => {
              const typeObj = operationTypes.find((t) => t.code === type)
              return (
                <div key={type} style={{ display: 'flex', justifyContent: 'space-between' }}>
                  <span>
                    <Tag color="blue">{typeObj?.name || type}</Tag>
                  </span>
                  <strong>{count} 次</strong>
                </div>
              )
            })}
          </Space>
        </Card>
      )}
    </div>
  )
}

export default AuditLogs
