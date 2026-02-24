import { useEffect } from 'react'
import { App as AntdApp } from 'antd'
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom'
import Layout from './components/Layout'
import RunList from './pages/RunList'
import RunDetail from './pages/RunDetail'
import DataImportEdit from './pages/DataImportEdit'
import RuleParams from './pages/RuleParams'
import Mappings from './pages/Mappings'
import AuditLogs from './pages/AuditLogs'
import { setMessageApi } from './lib/antdApp'

function AppInner() {
  const { message } = AntdApp.useApp()

  useEffect(() => {
    setMessageApi(message)
  }, [message])

  return (
    <BrowserRouter>
      <Routes>
        <Route path="/" element={<Layout />}>
          <Route index element={<Navigate to="/runs" replace />} />
          <Route path="runs" element={<RunList />} />
          <Route path="runs/:runId" element={<RunDetail />} />
          <Route path="runs/:runId/data-edit" element={<DataImportEdit />} />
          <Route path="rule-params" element={<RuleParams />} />
          <Route path="mappings" element={<Mappings />} />
          <Route path="audit-logs" element={<AuditLogs />} />
        </Route>
      </Routes>
    </BrowserRouter>
  )
}

function App() {
  return (
    <AntdApp>
      <AppInner />
    </AntdApp>
  )
}

export default App
