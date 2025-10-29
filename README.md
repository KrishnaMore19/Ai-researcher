# 🚀 AI Research Assistant - Full Stack Application

A comprehensive AI-powered research assistant built with **Next.js** (frontend) and **FastAPI** (backend) featuring document management, intelligent chat, advanced analytics, and subscription management.

## ✨ Features

- 📄 **Document Management** - Upload, view, and manage research documents (PDF, TXT, DOCX)
- 💬 **AI-Powered Chat** - Interactive chat with RAG (Retrieval Augmented Generation)
- 🔍 **Advanced Search** - Semantic, keyword, and hybrid search modes
- 📊 **Analytics Dashboard** - Track document usage, queries, and productivity
- 📝 **Smart Notes** - Create and link notes to documents
- 💳 **Subscription Management** - Razorpay payment integration with multiple plans
- 🎨 **Modern UI** - Responsive design with dark mode support
- 🔐 **Authentication** - Secure JWT-based authentication

## 🛠️ Tech Stack

### Frontend
- **Framework**: Next.js 14 (App Router)
- **State Management**: Zustand
- **Styling**: TailwindCSS + shadcn/ui
- **Charts**: Recharts
- **Authentication**: JWT tokens

### Backend
- **Framework**: FastAPI (Python)
- **Database**: PostgreSQL + SQLAlchemy
- **Vector DB**: ChromaDB (for document embeddings)
- **AI Models**: OpenRouter API (Llama 3.2, Mistral, Gemma)
- **Payment**: Razorpay
- **Authentication**: JWT + OAuth2

## 📋 Prerequisites

Before you begin, ensure you have the following installed:

- **Node.js** 18+ and npm/yarn
- **Python** 3.10+
- **PostgreSQL** 15+
- **Git**

## 🚀 Getting Started

### 1. Clone the Repository

```bash
git clone <your-repo-url>
cd <project-folder>
```

### 2. Backend Setup

#### Step 1: Navigate to Backend Directory
```bash
cd backend
```

#### Step 2: Create Virtual Environment
```bash
# Windows
python -m venv venv
venv\Scripts\activate

# macOS/Linux
python3 -m venv venv
source venv/bin/activate
```

#### Step 3: Install Dependencies
```bash
pip install -r requirements.txt
```

#### Step 4: Configure Environment Variables
Create a `.env` file in the `backend` directory (see `.env.example` or use the provided `.env` file):

```env
# App Configuration
APP_NAME=ResearchCopilotPro
APP_ENV=development
APP_HOST=0.0.0.0
APP_PORT=8000

# Database
DATABASE_URL=postgresql+asyncpg://postgres:123456@localhost:5432/researchcopilot_db

# Security
JWT_SECRET_KEY=your-secret-key-here
JWT_ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=60

# AI Models (OpenRouter)
LLAMA_MODEL=meta-llama/llama-3.2-3b-instruct:free
LLAMA_API_KEY=your-openrouter-api-key
DOLPHIN_MODEL=mistralai/mistral-7b-instruct:free
DOLPHIN_API_KEY=your-openrouter-api-key
GEMMA_MODEL=google/gemma-2-9b-it:free
GEMMA_API_KEY=your-openrouter-api-key

# Payment (Razorpay)
RAZORPAY_KEY_ID=your-razorpay-key-id
RAZORPAY_KEY_SECRET=your-razorpay-key-secret

# Storage
UPLOAD_DIR=storage/uploads
CHROMA_DB_DIR=storage/processed/chromadb
```

#### Step 5: Setup PostgreSQL Database
```bash
# Create database
psql -U postgres
CREATE DATABASE researchcopilot_db;
\q

# Run migrations (if using Alembic)
alembic upgrade head
```

#### Step 6: Create Storage Directories
```bash
# Windows
mkdir storage\uploads storage\processed storage\temp storage\processed\chromadb

# macOS/Linux
mkdir -p storage/uploads storage/processed storage/temp storage/processed/chromadb
```

#### Step 7: Start Backend Server
```bash
# Development mode with auto-reload
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# Or using Python directly
python -m uvicorn app.main:app --reload
```

The backend API will be available at: **http://localhost:8000**
- API Docs: http://localhost:8000/docs
- Alternative Docs: http://localhost:8000/redoc

### 3. Frontend Setup

#### Step 1: Navigate to Frontend Directory
```bash
# Open new terminal
cd frontend
```

#### Step 2: Install Dependencies
```bash
npm install
# or
yarn install
```

#### Step 3: Configure Environment Variables
Create a `.env.local` file in the `frontend` directory:

```env
NEXT_PUBLIC_API_URL=http://localhost:8000/api/v1
```

#### Step 4: Start Development Server
```bash
npm run dev
# or
yarn dev
```

The frontend will be available at: **http://localhost:3000**

## 🔑 API Keys Setup

### 1. OpenRouter API Key (Required for AI features)
1. Visit [OpenRouter.ai](https://openrouter.ai/)
2. Sign up and get your API key
3. Add it to backend `.env` file:
   ```env
   LLAMA_API_KEY=sk-or-v1-your-key-here
   DOLPHIN_API_KEY=sk-or-v1-your-key-here
   GEMMA_API_KEY=sk-or-v1-your-key-here
   ```

### 2. Razorpay Setup (Required for payments)
1. Visit [Razorpay Dashboard](https://dashboard.razorpay.com/)
2. Sign up and get Test/Live keys
3. Add to backend `.env`:
   ```env
   RAZORPAY_KEY_ID=rzp_test_your_key_id
   RAZORPAY_KEY_SECRET=your_key_secret
   ```

## 📱 Usage

### 1. Register/Login
- Navigate to http://localhost:3000
- Click "Sign up" to create an account
- Or login with existing credentials

### 2. Upload Documents
- Go to "Documents" page
- Click "Upload Document"
- Select PDF, TXT, or DOCX files (max 10MB)
- Wait for processing to complete

### 3. Chat with AI
- Go to "Chat" page
- Select documents (optional)
- Choose AI model (Llama, Dolphin, or Gemma)
- Type your question and get AI responses

### 4. View Analytics
- Go to "Dashboard" page
- See document uploads, query statistics, and trends

### 5. Manage Subscription
- Go to "Subscription" page
- Choose plan: Starter (Free), Pro (₹29.99), or Enterprise (₹99.99)
- Complete payment via Razorpay

## 🏗️ Project Structure

```
project-root/
│
├── backend/                 # FastAPI backend
│   ├── app/
│   │   ├── api/v1/         # API routes
│   │   ├── core/           # Configuration
│   │   ├── models/         # Database models
│   │   ├── schemas/        # Pydantic schemas
│   │   ├── services/       # Business logic
│   │   └── utils/          # Utilities
│   ├── storage/            # File storage
│   ├── .env                # Environment variables
│   └── requirements.txt    # Python dependencies
│
├── frontend/               # Next.js frontend
│   ├── app/                # App router pages
│   ├── components/         # React components
│   ├── store/              # Zustand stores
│   ├── .env.local          # Environment variables
│   └── package.json        # Node dependencies
│
└── README.md
```

## 🐛 Troubleshooting

### Backend Issues

**Database Connection Error**
```bash
# Check PostgreSQL is running
# Windows: Check Services
# macOS: brew services list
# Linux: systemctl status postgresql

# Verify credentials in .env match your PostgreSQL setup
```

**Import Errors**
```bash
# Ensure virtual environment is activated
# Reinstall dependencies
pip install -r requirements.txt --force-reinstall
```

**Port Already in Use**
```bash
# Change port in .env or kill process
# Windows: netstat -ano | findstr :8000
# macOS/Linux: lsof -ti:8000 | xargs kill -9
```

### Frontend Issues

**Module Not Found**
```bash
# Clear cache and reinstall
rm -rf node_modules package-lock.json
npm install
```

**API Connection Error**
```bash
# Verify backend is running on http://localhost:8000
# Check NEXT_PUBLIC_API_URL in .env.local
```

## 📚 API Documentation

Once the backend is running, visit:
- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

## 🔐 Default Test Credentials

For testing purposes, you can create an account or use:
- **Email**: test@example.com
- **Password**: Test123!

## 📊 Available Plans

| Plan | Price | Documents | Queries | Storage |
|------|-------|-----------|---------|---------|
| **Starter** | Free | 10 | 100/month | 1 GB |
| **Pro** | ₹29.99/month | 100 | 1,000/month | 10 GB |
| **Enterprise** | ₹99.99/month | 1,000 | 10,000/month | 100 GB |

## 🤝 Contributing

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

## 📄 License

This project is licensed under the MIT License.

## 🆘 Support

For support, email support@example.com or open an issue on GitHub.

## 🙏 Acknowledgments

- OpenRouter for AI model API
- Razorpay for payment gateway
- ChromaDB for vector database
