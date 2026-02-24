import { useState } from 'react'
import { Outlet, useNavigate, useLocation } from 'react-router-dom'
import { Layout as AntLayout, Menu, theme } from 'antd'
import {
  DashboardOutlined,
  SettingOutlined,
  FileTextOutlined,
  HistoryOutlined,
} from '@ant-design/icons'
import type { MenuProps } from 'antd'

const { Header, Content, Sider } = AntLayout

const Layout = () => {
  const navigate = useNavigate()
  const location = useLocation()
  const [collapsed, setCollapsed] = useState(false)
  const {
    token: { colorBgContainer, borderRadiusLG },
  } = theme.useToken()

  const menuItems: MenuProps['items'] = [
    {
      key: '/runs',
      icon: <DashboardOutlined />,
      label: '批次管理',
    },
    {
      key: '/rule-params',
      icon: <SettingOutlined />,
      label: '规则参数',
    },
    {
      key: '/mappings',
      icon: <FileTextOutlined />,
      label: '项目映射',
    },
    {
      key: '/audit-logs',
      icon: <HistoryOutlined />,
      label: '审计日志',
    },
  ]

  const handleMenuClick: MenuProps['onClick'] = (e) => {
    navigate(e.key)
  }

  return (
    <AntLayout className="app-layout" style={{ minHeight: '100vh' }}>
      <Sider
        className="app-sider"
        collapsible
        collapsed={collapsed}
        onCollapse={setCollapsed}
      >
        <div
          style={{
            height: 64,
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            color: '#fff',
            fontSize: collapsed ? 16 : 20,
            fontWeight: 'bold',
            transition: 'all 0.2s',
          }}
        >
          {collapsed ? '绩效' : '绩效核算系统'}
        </div>
        <Menu
          theme="dark"
          selectedKeys={[location.pathname]}
          mode="inline"
          items={menuItems}
          onClick={handleMenuClick}
        />
      </Sider>
      <AntLayout className="app-main">
        <Header
          className="app-header"
          style={{
            padding: '0 24px',
            background: colorBgContainer,
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'space-between',
            boxShadow: '0 1px 4px rgba(0,21,41,.08)',
          }}
        >
          <h2 style={{ margin: 0 }}>医院科室绩效核算系统</h2>
          <div style={{ color: '#666' }}>v1.1.0</div>
        </Header>
        <Content className="app-content" style={{ margin: '24px 16px 0' }}>
          <div
            className="app-content-inner"
            style={{
              padding: 24,
              minHeight: 360,
              background: colorBgContainer,
              borderRadius: borderRadiusLG,
            }}
          >
            <Outlet />
          </div>
        </Content>
      </AntLayout>
    </AntLayout>
  )
}

export default Layout
