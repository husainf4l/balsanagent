# AI Business Advisor - Full-Stack Chat Application

<div align="center">

![AI Business Advisor](https://img.shields.io/badge/AI-Business%20Advisor-blue?style=for-the-badge)
![FastAPI](https://img.shields.io/badge/FastAPI-009688?style=for-the-badge&logo=fastapi&logoColor=white)
![NestJS](https://img.shields.io/badge/NestJS-E0234E?style=for-the-badge&logo=nestjs&logoColor=white)
![Next.js](https://img.shields.io/badge/Next.js-000000?style=for-the-badge&logo=nextdotjs&logoColor=white)
![LangGraph](https://img.shields.io/badge/LangGraph-FF6B6B?style=for-the-badge)

_A production-ready, scalable AI chat system with enterprise-grade architecture_

</div>

## 🎯 Overview

This project implements a comprehensive AI Business Advisor chat application using a modern, scalable three-tier architecture:

- **🤖 AI Agent Layer** (FastAPI + LangGraph) - Intelligent conversation processing
- **🛡️ API Gateway Layer** (NestJS) - Security, validation, and business logic
- **🎨 Frontend Layer** (Next.js) - Modern, responsive user interface

### ✨ Key Features

- 🧠 **Intelligent Conversations** - Powered by LangGraph with persistent memory
- 🔒 **Enterprise Security** - JWT authentication, rate limiting, input validation
- 📊 **Advanced Monitoring** - Comprehensive logging, metrics, and health checks
- 🚀 **High Performance** - Optimized caching, connection pooling, async processing
- 📱 **Modern UI** - Responsive design with real-time chat experience
- 🔧 **Production Ready** - Docker support, environment configuration, error handling

## 🏗️ Architecture

```mermaid
graph LR
    A[👤 User] --> B[🎨 Next.js Frontend<br/>Port 3000]
    B --> C[🛡️ NestJS API Gateway<br/>Port 3001]
    C --> D[🤖 FastAPI AI Agent<br/>Port 8000]
    D --> E[🗄️ PostgreSQL Database]
    D --> F[🧠 LangGraph Engine]
    F --> G[🔗 OpenAI API]

    style A fill:#e1f5fe
    style B fill:#f3e5f5
    style C fill:#e8f5e8
    style D fill:#fff3e0
    style E fill:#fce4ec
    style F fill:#f1f8e9
    style G fill:#e0f2f1
```

### 🎯 Why This Architecture?

| Layer                | Purpose           | Benefits                                     |
| -------------------- | ----------------- | -------------------------------------------- |
| **Next.js Frontend** | User Interface    | Modern React, SSR/SSG, optimal UX            |
| **NestJS Gateway**   | API Management    | Security, validation, monitoring, caching    |
| **FastAPI Agent**    | AI Processing     | High-performance Python, async, ML libraries |
| **PostgreSQL**       | Data Persistence  | ACID compliance, chat history, user data     |
| **LangGraph**        | Conversation Flow | Stateful conversations, memory management    |

## 🚀 Quick Start

### Prerequisites

- Node.js 18+ and npm
- Python 3.9+
- PostgreSQL 12+
- OpenAI API key

### 1. Clone and Setup

```bash
git clone <repository-url>
cd aqlon
```

### 2. FastAPI AI Agent Setup

```bash
# Install Python dependencies
pip install -r requirements.txt

# Configure environment
cp .env.example .env
# Edit .env with your OpenAI API key and database URL

# Start the AI agent
python main.py
```

✅ **AI Agent running on http://localhost:8000**

### 3. NestJS API Gateway Setup

```bash
# Create NestJS project
npm i -g @nestjs/cli
nest new ai-chat-backend
cd ai-chat-backend

# Install dependencies
npm install @nestjs/config @nestjs/throttler axios class-validator class-transformer

# Configure environment
cp .env.example .env

# Start the API gateway
npm run start:dev
```

✅ **API Gateway running on http://localhost:3001**

### 4. Next.js Frontend Setup

```bash
# Create Next.js project
npx create-next-app@latest ai-chat-frontend
cd ai-chat-frontend

# Install additional dependencies
npm install axios @types/node

# Configure environment
echo "NEXT_PUBLIC_API_URL=http://localhost:3001" > .env.local

# Start the frontend
npm run dev
```

✅ **Frontend running on http://localhost:3000**

### 5. Verify Installation

```bash
# Test the complete stack
curl http://localhost:3001/api/health
# Should return: {"status":"healthy","fastapi":true}
```

## 📋 Detailed Setup Guides

| Component            | Documentation                                        | Purpose                                  |
| -------------------- | ---------------------------------------------------- | ---------------------------------------- |
| 🤖 **FastAPI Agent** | [README_API.md](./README_API.md)                     | AI agent setup, endpoints, configuration |
| 🏗️ **Full Stack**    | [README_NESTJS_NEXTJS.md](./README_NESTJS_NEXTJS.md) | Complete NestJS + Next.js integration    |
| 🔧 **API Reference** | [INTEGRATION_COMPLETE.md](./INTEGRATION_COMPLETE.md) | Endpoint documentation and examples      |

## 🛠️ Development Workflow

### Running in Development Mode

```bash
# Terminal 1: AI Agent (FastAPI)
cd aqlon
python main.py

# Terminal 2: API Gateway (NestJS)
cd ai-chat-backend
npm run start:dev

# Terminal 3: Frontend (Next.js)
cd ai-chat-frontend
npm run dev
```

### Testing the API

```bash
# Run automated tests
python test_api.py

# Manual endpoint testing
./test_endpoints.sh
```

### Monitoring and Logs

- **FastAPI**: Built-in automatic documentation at http://localhost:8000/docs
- **NestJS**: Request logging and performance metrics
- **Next.js**: Development console and network inspection

## 🔧 Configuration

### Environment Variables

#### FastAPI (.env)

```env
OPENAI_API_KEY=sk-...
DATABASE_URL=postgresql://user:pass@localhost/dbname
LOG_LEVEL=INFO
MAX_TOKENS=2000
```

#### NestJS (.env)

```env
PORT=3001
FASTAPI_BASE_URL=http://localhost:8000
THROTTLE_TTL=60
THROTTLE_LIMIT=100
JWT_SECRET=your-jwt-secret
```

#### Next.js (.env.local)

```env
NEXT_PUBLIC_API_URL=http://localhost:3001
NEXT_PUBLIC_APP_NAME=AI Business Advisor
```

## 📊 API Reference

### Core Endpoints

| Method   | Endpoint                     | Description         | Authentication |
| -------- | ---------------------------- | ------------------- | -------------- |
| `GET`    | `/health`                    | System health check | None           |
| `POST`   | `/api/sessions`              | Create chat session | Optional       |
| `POST`   | `/api/chat`                  | Send message        | Session ID     |
| `GET`    | `/api/sessions/{id}/history` | Get chat history    | Session ID     |
| `DELETE` | `/api/sessions/{id}`         | Clear session       | Session ID     |

### Example Usage

```javascript
// Create a new session
const session = await fetch("http://localhost:3001/api/sessions", {
  method: "POST",
}).then((res) => res.json());

// Send a message
const response = await fetch("http://localhost:3001/api/chat", {
  method: "POST",
  headers: { "Content-Type": "application/json" },
  body: JSON.stringify({
    message: "What's my business performance?",
    session_id: session.session_id,
  }),
}).then((res) => res.json());

console.log(response.response); // AI assistant's reply
```

## 🚢 Deployment

### Production Deployment Options

<details>
<summary><strong>🐳 Docker Deployment</strong></summary>

```dockerfile
# FastAPI Dockerfile
FROM python:3.9-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY . .
EXPOSE 8000
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
```

```yaml
# docker-compose.yml
version: "3.8"
services:
  fastapi:
    build: .
    ports:
      - "8000:8000"
    environment:
      - DATABASE_URL=postgresql://postgres:password@db:5432/aqlon
    depends_on:
      - db

  nestjs:
    build: ./ai-chat-backend
    ports:
      - "3001:3001"
    environment:
      - FASTAPI_BASE_URL=http://fastapi:8000
    depends_on:
      - fastapi

  nextjs:
    build: ./ai-chat-frontend
    ports:
      - "3000:3000"
    environment:
      - NEXT_PUBLIC_API_URL=http://localhost:3001

  db:
    image: postgres:15
    environment:
      POSTGRES_DB: aqlon
      POSTGRES_USER: postgres
      POSTGRES_PASSWORD: password
    volumes:
      - postgres_data:/var/lib/postgresql/data

volumes:
  postgres_data:
```

```bash
# Deploy with Docker
docker-compose up -d
```

</details>

<details>
<summary><strong>☁️ Cloud Deployment (AWS/GCP/Azure)</strong></summary>

### AWS Deployment

- **FastAPI**: AWS Lambda + API Gateway or ECS
- **NestJS**: AWS ECS or EC2
- **Next.js**: AWS Amplify or S3 + CloudFront
- **Database**: AWS RDS PostgreSQL

### Recommended Infrastructure

```yaml
# Infrastructure as Code example
Resources:
  FastAPIService:
    Type: AWS::ECS::Service
    Properties:
      Cluster: !Ref ECSCluster
      TaskDefinition: !Ref FastAPITaskDefinition
      DesiredCount: 2

  NestJSService:
    Type: AWS::ECS::Service
    Properties:
      Cluster: !Ref ECSCluster
      TaskDefinition: !Ref NestJSTaskDefinition
      DesiredCount: 2

  Database:
    Type: AWS::RDS::DBInstance
    Properties:
      DBInstanceClass: db.t3.micro
      Engine: postgres
      AllocatedStorage: 20
```

</details>

## 🔍 Monitoring and Observability

### Health Checks

```bash
# Check all services
curl http://localhost:8000/health    # FastAPI
curl http://localhost:3001/api/health # NestJS (includes FastAPI check)
curl http://localhost:3000/api/health # Next.js
```

### Logging Strategy

- **FastAPI**: Structured JSON logging with request tracing
- **NestJS**: Centralized logging with performance metrics
- **Next.js**: Client-side error tracking and analytics

### Performance Metrics

- Response times per endpoint
- Token usage and costs
- User session analytics
- Error rates and debugging

## 🤝 Contributing

### Development Guidelines

1. **Code Style**: Follow language-specific conventions (Black for Python, Prettier for TypeScript)
2. **Testing**: Write tests for new features and bug fixes
3. **Documentation**: Update relevant README files
4. **Security**: Follow security best practices for API development

### Project Structure

```
aqlon/
├── 🤖 FastAPI AI Agent
│   ├── main.py              # FastAPI application
│   ├── requirements.txt     # Python dependencies
│   ├── test_api.py         # API tests
│   └── start_server.sh     # Startup script
├── 🛡️ NestJS Gateway
│   ├── src/
│   │   ├── chat/           # Chat module
│   │   ├── common/         # Shared utilities
│   │   └── config/         # Configuration
│   └── package.json        # Node dependencies
├── 🎨 Next.js Frontend
│   ├── lib/chat-api.ts     # API client
│   ├── components/         # React components
│   └── pages/              # Application pages
└── 📖 Documentation
    ├── README.md           # This file
    ├── README_API.md       # FastAPI documentation
    └── README_NESTJS_NEXTJS.md # Full-stack guide
```

## 🔧 Troubleshooting

### Common Issues

<details>
<summary><strong>🚨 "Connection Refused" Error</strong></summary>

**Problem**: Services can't communicate with each other

**Solutions**:

1. Verify all services are running on correct ports
2. Check firewall settings
3. Ensure environment variables are correctly set
4. Test individual endpoints with curl

```bash
# Debug steps
netstat -tulpn | grep :8000  # Check if FastAPI is running
netstat -tulpn | grep :3001  # Check if NestJS is running
curl http://localhost:8000/health  # Test FastAPI directly
```

</details>

<details>
<summary><strong>🔑 "OpenAI API Key" Error</strong></summary>

**Problem**: Invalid or missing OpenAI API key

**Solutions**:

1. Verify API key in `.env` file
2. Check OpenAI account status and billing
3. Ensure correct environment variable name (`OPENAI_API_KEY`)

```bash
# Verify environment
echo $OPENAI_API_KEY
# Should display your API key
```

</details>

<details>
<summary><strong>🗄️ Database Connection Issues</strong></summary>

**Problem**: Cannot connect to PostgreSQL

**Solutions**:

1. Verify PostgreSQL is running
2. Check connection string format
3. Verify database exists and credentials are correct

```bash
# Test database connection
psql $DATABASE_URL
# Should connect successfully
```

</details>

### Getting Help

- 📖 **Documentation**: Check the relevant README files
- 🐛 **Issues**: Create a detailed issue report
- 💬 **Discussions**: Join community discussions
- 📧 **Support**: Contact the development team

## 📜 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- **OpenAI** for GPT models and APIs
- **LangChain/LangGraph** for conversation management
- **FastAPI** for high-performance Python APIs
- **NestJS** for enterprise-grade Node.js framework
- **Next.js** for modern React applications

---

<div align="center">

**Built with ❤️ for intelligent business conversations**

[🚀 Get Started](#-quick-start) • [📖 Documentation](#-detailed-setup-guides) • [🤝 Contributing](#-contributing)

</div>
