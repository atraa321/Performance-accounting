# 绩效核算系统 - 前端

基于 React 18 + TypeScript + Vite + Ant Design 5 构建的现代化前端应用。

## 技术栈

- **框架**: React 18.2
- **语言**: TypeScript 5.2
- **构建工具**: Vite 5.0
- **UI 组件库**: Ant Design 5.12
- **路由**: React Router 6.21
- **HTTP 客户端**: Axios 1.6
- **状态管理**: Zustand 4.4
- **图表**: Recharts 2.10
- **日期处理**: Day.js 1.11

## 功能模块

### 1. 批次管理
- ✅ 批次列表展示
- ✅ 创建新批次
- ✅ 批次详情查看
- ✅ 批次锁定
- ✅ 批次复制

### 2. 数据导入与计算
- ✅ Excel 文件上传
- ✅ 数据验证
- ✅ 执行计算
- ✅ 结果展示（汇总、明细、对账、异常）
- ✅ Excel 导出

### 3. 规则参数配置
- ✅ 按类别展示参数
- ✅ 参数编辑
- ✅ 批量保存
- ✅ 参数说明

### 4. 项目映射管理
- ✅ 映射列表
- ✅ 创建/编辑/删除映射
- ✅ 未映射项目提示
- ✅ 快速添加映射

### 5. 审计日志
- ✅ 日志列表
- ✅ 多维度筛选
- ✅ 统计分析
- ✅ 详情展开

## 快速开始

### 安装依赖

```bash
cd frontend
npm install
```

### 开发模式

```bash
npm run dev
```

访问：http://localhost:3000

### 生产构建

```bash
npm run build
```

构建产物在 `dist` 目录。

### 预览构建

```bash
npm run preview
```

## 项目结构

```
frontend/
├── src/
│   ├── api/              # API 接口
│   │   ├── index.ts      # Axios 配置
│   │   ├── run.ts        # 批次相关接口
│   │   ├── ruleParam.ts  # 规则参数接口
│   │   ├── mapping.ts    # 项目映射接口
│   │   └── audit.ts      # 审计日志接口
│   ├── components/       # 公共组件
│   │   └── Layout.tsx    # 布局组件
│   ├── pages/            # 页面组件
│   │   ├── RunList.tsx   # 批次列表
│   │   ├── RunDetail.tsx # 批次详情
│   │   ├── RuleParams.tsx # 规则参数
│   │   ├── Mappings.tsx  # 项目映射
│   │   └── AuditLogs.tsx # 审计日志
│   ├── App.tsx           # 应用入口
│   ├── main.tsx          # 主文件
│   └── index.css         # 全局样式
├── index.html            # HTML 模板
├── package.json          # 依赖配置
├── tsconfig.json         # TypeScript 配置
├── vite.config.ts        # Vite 配置
└── README.md             # 说明文档
```

## API 代理配置

开发环境下，所有 `/api` 开头的请求会被代理到后端服务：

```typescript
// vite.config.ts
proxy: {
  '/api': {
    target: 'http://localhost:8000',
    changeOrigin: true,
    rewrite: (path) => path.replace(/^\/api/, ''),
  },
}
```

## 环境要求

- Node.js 16+
- npm 8+ 或 yarn 1.22+

## 开发建议

### 代码规范

项目使用 ESLint 进行代码检查：

```bash
npm run lint
```

### TypeScript

所有组件和函数都应该有明确的类型定义。

### 组件开发

- 使用函数组件和 Hooks
- 遵循 React 最佳实践
- 保持组件单一职责

### API 调用

所有 API 调用都应该通过 `src/api` 目录下的模块进行：

```typescript
import { runApi } from '@/api/run'

const data = await runApi.list()
```

## 常见问题

### Q1: 启动时端口被占用

修改 `vite.config.ts` 中的端口配置：

```typescript
server: {
  port: 3001, // 修改为其他端口
}
```

### Q2: API 请求失败

1. 确保后端服务已启动（http://localhost:8000）
2. 检查浏览器控制台的网络请求
3. 查看后端日志

### Q3: 构建失败

1. 删除 `node_modules` 和 `package-lock.json`
2. 重新安装依赖：`npm install`
3. 清除缓存：`npm run build -- --force`

## 浏览器支持

- Chrome >= 90
- Firefox >= 88
- Safari >= 14
- Edge >= 90

## 贡献指南

1. Fork 项目
2. 创建特性分支
3. 提交变更
4. 推送到分支
5. 创建 Pull Request

## 许可证

MIT
