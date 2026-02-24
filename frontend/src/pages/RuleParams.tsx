import { useState, useEffect } from 'react'
import {
  Card,
  Form,
  Input,
  InputNumber,
  Button,
  Collapse,
  Space,
  Descriptions,
  Tag,
} from 'antd'
import { SaveOutlined, ReloadOutlined } from '@ant-design/icons'
import { ruleParamApi, type RuleParam } from '@/api/ruleParam'
import { getMessageApi } from '@/lib/antdApp'

const { Panel } = Collapse

const RuleParams = () => {
  const [form] = Form.useForm()
  const [loading, setLoading] = useState(false)
  const [categories, setCategories] = useState<Record<string, RuleParam[]>>({})

  useEffect(() => {
    loadParams()
  }, [])

  const loadParams = async () => {
    setLoading(true)
    try {
      const data = await ruleParamApi.getByCategory()
      setCategories(data)
      
      // 设置表单初始值
      const initialValues: Record<string, number> = {}
      Object.values(data).flat().forEach((param) => {
        initialValues[param.param_key] = param.param_value_num || 0
      })
      form.setFieldsValues(initialValues)
    } catch (error) {
      console.error('加载参数失败:', error)
    } finally {
      setLoading(false)
    }
  }

  const handleSave = async (values: any) => {
    setLoading(true)
    try {
      const updates = Object.entries(values).map(([param_key, value]) => ({
        param_key,
        param_value: String(value),
        param_value_num: Number(value),
      }))
      
      await ruleParamApi.batchUpdate(updates)
      getMessageApi()?.success('参数保存成功')
      loadParams()
    } catch (error) {
      console.error('保存参数失败:', error)
    } finally {
      setLoading(false)
    }
  }

  const handleReset = () => {
    form.resetFields()
    loadParams()
  }

  const renderParamInput = (param: RuleParam) => {
    const isPercentage = param.param_key.includes('ratio') || param.param_key.includes('coeff')
    const isMoney = param.param_key.includes('unit') || param.param_key.includes('fee')
    
    return (
      <Form.Item
        key={param.param_key}
        name={param.param_key}
        label={param.param_desc || param.param_key}
        rules={[{ required: true, message: '请输入参数值' }]}
        extra={
          <Space size="small">
            <Tag color="blue">当前值: {param.param_value}</Tag>
            {isPercentage && <span style={{ color: '#999' }}>（比例值，如 0.7 表示 70%）</span>}
          </Space>
        }
      >
        <InputNumber
          style={{ width: '100%' }}
          min={0}
          max={isPercentage ? 1 : undefined}
          step={isPercentage ? 0.01 : isMoney ? 1 : 1}
          precision={isPercentage ? 2 : isMoney ? 2 : 0}
        />
      </Form.Item>
    )
  }

  return (
    <div>
      <Card
        title="规则参数配置"
        extra={
          <Space>
            <Button icon={<ReloadOutlined />} onClick={handleReset}>
              重置
            </Button>
            <Button
              type="primary"
              icon={<SaveOutlined />}
              onClick={() => form.submit()}
              loading={loading}
            >
              保存
            </Button>
          </Space>
        }
      >
        <Descriptions bordered column={1} style={{ marginBottom: 24 }}>
          <Descriptions.Item label="说明">
            规则参数用于控制绩效计算的各项比例和系数。修改后需要重新计算才能生效。
          </Descriptions.Item>
          <Descriptions.Item label="注意事项">
            <ul style={{ margin: 0, paddingLeft: 20 }}>
              <li>比例参数使用小数表示，如 0.7 表示 70%</li>
              <li>修改参数后请确保所有相关比例之和为 1</li>
              <li>参数修改会影响后续所有计算，请谨慎操作</li>
            </ul>
          </Descriptions.Item>
        </Descriptions>

        <Form form={form} layout="vertical" onFinish={handleSave}>
          <Collapse defaultActiveKey={Object.keys(categories)}>
            {Object.entries(categories).map(([category, params]) => (
              <Panel
                header={
                  <Space>
                    <span style={{ fontWeight: 'bold' }}>{category}</span>
                    <Tag color="blue">{params.length} 个参数</Tag>
                  </Space>
                }
                key={category}
              >
                {params.map((param) => renderParamInput(param))}
              </Panel>
            ))}
          </Collapse>
        </Form>
      </Card>

      <Card title="参数说明" style={{ marginTop: 16 }}>
        <Descriptions bordered column={1}>
          <Descriptions.Item label="判读费分配">
            化验判读费按医师和护理池比例分配，其他判读费全部分配给医师
          </Descriptions.Item>
          <Descriptions.Item label="科主任判读费">
            按主任、副主任、护士长比例分配，通常为 80%、0%、20%
          </Descriptions.Item>
          <Descriptions.Item label="床补分配">
            按医师和护理池比例分配，医师部分按床日数分配
          </Descriptions.Item>
          <Descriptions.Item label="护理池分配">
            按护理工作量分数分配，护士长分数为平均分×系数（通常为1.4）
          </Descriptions.Item>
          <Descriptions.Item label="医师池分配">
            按工作量分配，工作量为0的医师使用最小权重（通常为0.8）
          </Descriptions.Item>
          <Descriptions.Item label="科室盈余">
            主任和护士长按固定比例分配，剩余部分按绩效分数分配
          </Descriptions.Item>
          <Descriptions.Item label="住院证单价">
            每张住院证的补贴金额（元）
          </Descriptions.Item>
        </Descriptions>
      </Card>
    </div>
  )
}

export default RuleParams
