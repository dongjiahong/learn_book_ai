# RAG Learning Platform

基于RAG技术的智能学习平台，支持文档上传、智能问答、知识点提取和Anki卡片生成。

## 项目结构

```
rag-learning-platform/
├── frontend/          # Next.js 14 前端应用
├── backend/           # FastAPI 后端应用
├── environment.yml    # Conda环境配置
└── README.md         # 项目说明
```

## 环境配置

### 1. 创建Conda环境

```bash
conda env create -f environment.yml
conda activate rag-learning-platform
```

### 2. 启动后端服务

```bash
cd backend
pip install -r requirements.txt
python main.py
```

后端服务将在 http://localhost:8000 启动

### 3. 启动前端服务

```bash
cd frontend
npm install
npm run dev
```

前端服务将在 http://localhost:3000 启动

## 配置文件

后端配置文件位于 `backend/config.toml`，包含以下配置项：

- 数据库配置
- 认证配置
- LLM配置（支持OpenAI和Ollama）
- 向量数据库配置
- Anki配置
- 服务器配置

## 开发环境

- Python 3.12
- Node.js (推荐 18+)
- Next.js 14 with App Router
- FastAPI
- TypeScript
- Tailwind CSS

## API文档

启动后端服务后，可以访问以下地址查看API文档：

- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc