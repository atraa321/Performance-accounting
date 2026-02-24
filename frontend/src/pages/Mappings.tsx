import { useState, useEffect } from 'react'
import {
  Table,
  Button,
  Space,
  Modal,
  Form,
  Input,
  InputNumber,
  Select,
  Card,
  Tag,
  Popconfirm,
  Alert,
} from 'antd'
import { PlusOutlined, EditOutlined, DeleteOutlined } from '@ant-design/icons'
import type { ColumnsType } from 'antd/es/table'
import { mappingApi, type AvailableBehaviorType, type ItemMapping } from '@/api/mapping'
import { getMessageApi } from '@/lib/antdApp'

const Mappings = () => {
  const [mappings, setMappings] = useState<ItemMapping[]>([])
  const [unmatchedItems, setUnmatchedItems] = useState<string[]>([])
  const [behaviorTypes, setBehaviorTypes] = useState<AvailableBehaviorType[]>([])
  const [loading, setLoading] = useState(false)
  const [modalOpen, setModalOpen] = useState(false)
  const [editingMapping, setEditingMapping] = useState<ItemMapping | null>(null)
  const [form] = Form.useForm()

  useEffect(() => {
    loadMappings()
    loadUnmatched()
    loadBehaviorTypes()
  }, [])

  const loadMappings = async () => {
    setLoading(true)
    try {
      const data = await mappingApi.list()
      setMappings(data)
    } catch (error) {
      console.error('加载映射失败:', error)
    } finally {
      setLoading(false)
    }
  }

  const loadUnmatched = async () => {
    try {
      const data = await mappingApi.getUnmatched()
      setUnmatchedItems(data.items)
    } catch (error) {
      console.error('加载未映射项目失败:', error)
    }
  }

  const loadBehaviorTypes = async () => {
    try {
      const data = await mappingApi.getAvailableTypes()
      setBehaviorTypes(data.types)
    } catch (error) {
      console.error('加载行为类型失败:', error)
    }
  }

  const handleCreate = () => {
    setEditingMapping(null)
    form.resetFields()
    setModalOpen(true)
  }

  const handleEdit = (record: ItemMapping) => {
    setEditingMapping(record)
    form.setFieldsValue(record)
    setModalOpen(true)
  }

  const handleDelete = async (id: number) => {
    try {
      await mappingApi.delete(id)
      getMessageApi()?.success('删除成功')
      loadMappings()
    } catch (error) {
      console.error('删除失败:', error)
    }
  }

  const handleSubmit = async (values: any) => {
    try {
      if (editingMapping) {
        await mappingApi.update(editingMapping.id, values)
        getMessageApi()?.success('更新成功')
      } else {
        await mappingApi.create(values)
        getMessageApi()?.success('创建成功')
      }
      setModalOpen(false)
      form.resetFields()
      loadMappings()
      loadUnmatched()
    } catch (error) {
      console.error('保存失败:', error)
    }
  }

  const handleQuickAdd = (itemName: string) => {
    form.setFieldsValue({
      raw_item_name: itemName,
      priority: 100,
      is_active: true,
      behavior_type: undefined,
    })
    setEditingMapping(null)
    setModalOpen(true)
  }

  const columns: ColumnsType<ItemMapping> = [
    {
      title: 'ID',
      dataIndex: 'id',
      key: 'id',
      width: 80,
    },
    {
      title: '原始项目名',
      dataIndex: 'raw_item_name',
      key: 'raw_item_name',
      width: 200,
    },
    {
      title: '项目编码',
      dataIndex: 'item_code',
      key: 'item_code',
      width: 200,
    },
    {
      title: '行为类型',
      dataIndex: 'behavior_type',
      key: 'behavior_type',
      width: 140,
      render: (behaviorType: string | null | undefined) =>
        behaviorType ? <Tag color="processing">{behaviorType}</Tag> : '-',
    },
    {
      title: '优先级',
      dataIndex: 'priority',
      key: 'priority',
      width: 100,
      sorter: (a, b) => a.priority - b.priority,
    },
    {
      title: '状态',
      dataIndex: 'is_active',
      key: 'is_active',
      width: 100,
      render: (active: boolean) => (
        <Tag color={active ? 'success' : 'default'}>{active ? '启用' : '禁用'}</Tag>
      ),
    },
    {
      title: '操作',
      key: 'action',
      fixed: 'right',
      width: 150,
      render: (_, record) => (
        <Space size="small">
          <Button
            type="link"
            size="small"
            icon={<EditOutlined />}
            onClick={() => handleEdit(record)}
          >
            编辑
          </Button>
          <Popconfirm
            title="确定要删除吗？"
            onConfirm={() => handleDelete(record.id)}
          >
            <Button type="link" size="small" icon={<DeleteOutlined />} danger>
              删除
            </Button>
          </Popconfirm>
        </Space>
      ),
    },
  ]

  return (
    <div>
      {unmatchedItems.length > 0 && (
        <Alert
          message={`发现 ${unmatchedItems.length} 个未映射项目`}
          description={
            <div>
              <p>以下项目尚未配置映射，请及时添加：</p>
              <Space wrap>
                {unmatchedItems.slice(0, 10).map((item) => (
                  <Tag
                    key={item}
                    color="warning"
                    style={{ cursor: 'pointer' }}
                    onClick={() => handleQuickAdd(item)}
                  >
                    {item}
                  </Tag>
                ))}
                {unmatchedItems.length > 10 && <span>...</span>}
              </Space>
            </div>
          }
          type="warning"
          showIcon
          closable
          style={{ marginBottom: 16 }}
        />
      )}

      <Card
        title="项目映射管理"
        extra={
          <Button type="primary" icon={<PlusOutlined />} onClick={handleCreate}>
            新建映射
          </Button>
        }
      >
        <Table
          columns={columns}
          dataSource={mappings}
          rowKey="id"
          loading={loading}
          scroll={{ x: 900 }}
        />
      </Card>

      <Card title="行为类型说明" style={{ marginTop: 16 }}>
        <Space direction="vertical" style={{ width: '100%' }}>
          {behaviorTypes.map((type) => (
            <div key={type.code}>
              <Tag color="blue">{type.code}</Tag>
              <strong>{type.name}</strong>: {type.description}
            </div>
          ))}
        </Space>
      </Card>

      <Modal
        title={editingMapping ? '编辑映射' : '新建映射'}
        open={modalOpen}
        onOk={() => form.submit()}
        onCancel={() => {
          setModalOpen(false)
          form.resetFields()
        }}
        width={600}
      >
        <Form
          form={form}
          layout="vertical"
          onFinish={handleSubmit}
          initialValues={{
            priority: 100,
            is_active: true,
          }}
        >
          <Form.Item
            name="raw_item_name"
            label="原始项目名"
            rules={[{ required: true, message: '请输入原始项目名' }]}
            extra="Excel 中的项目名称，支持模糊匹配"
          >
            <Input placeholder="例如：科主任判读费" />
          </Form.Item>
          <Form.Item
            name="item_code"
            label="项目编码"
            rules={[{ required: true, message: '请输入项目编码' }]}
            extra="系统内部使用的项目编码，需与行为配置对应"
          >
            <Input placeholder="例如：LEAD_READING_FEE" />
          </Form.Item>
          <Form.Item
            name="behavior_type"
            label="行为类型"
            extra="可选：保存映射时同步设置该项目编码的行为类型"
          >
            <Select
              allowClear
              placeholder="请选择行为类型"
              options={behaviorTypes.map((type) => ({
                label: `${type.code} - ${type.name}`,
                value: type.code,
              }))}
            />
          </Form.Item>
          <Form.Item
            name="priority"
            label="优先级"
            rules={[{ required: true, message: '请输入优先级' }]}
            extra="数字越小优先级越高，用于处理多个映射匹配的情况"
          >
            <InputNumber style={{ width: '100%' }} min={1} max={999} />
          </Form.Item>
          <Form.Item
            name="is_active"
            label="状态"
            rules={[{ required: true, message: '请选择状态' }]}
          >
            <Select>
              <Select.Option value={true}>启用</Select.Option>
              <Select.Option value={false}>禁用</Select.Option>
            </Select>
          </Form.Item>
        </Form>
      </Modal>
    </div>
  )
}

export default Mappings
