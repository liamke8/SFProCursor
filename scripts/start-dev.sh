#!/bin/bash

# SEO Automation Platform - Development Startup Script
echo "🚀 Starting SEO Automation Platform in development mode..."

# Function to check if a port is in use
check_port() {
    if lsof -Pi :$1 -sTCP:LISTEN -t >/dev/null ; then
        echo "❌ Port $1 is already in use"
        return 1
    else
        echo "✅ Port $1 is available"
        return 0
    fi
}

# Check required ports
echo "🔍 Checking port availability..."
check_port 3000  # Frontend
check_port 8000  # Backend API
check_port 5432  # PostgreSQL
check_port 6379  # Redis
check_port 9000  # MinIO

# Create directories if they don't exist
echo "📁 Creating required directories..."
mkdir -p backend/logs
mkdir -p backend/data
mkdir -p backend/alembic/versions

# Check if .env file exists
if [ ! -f .env ]; then
    echo "⚠️  No .env file found. Copying from env.example..."
    cp env.example .env
    echo "📝 Please edit .env file with your configuration before continuing."
    echo "   Especially update database credentials and API keys."
fi

# Start infrastructure services
echo "🐳 Starting infrastructure services (PostgreSQL, Redis, MinIO)..."
docker-compose up -d postgres redis minio

# Wait for services to be ready
echo "⏳ Waiting for services to be ready..."
sleep 10

# Check if database is ready
echo "🔍 Checking database connection..."
until docker-compose exec -T postgres pg_isready -U user -d seo_platform; do
    echo "⏳ Waiting for PostgreSQL to be ready..."
    sleep 2
done

# Run database migrations
echo "📊 Running database migrations..."
cd backend
export DATABASE_URL="postgresql+asyncpg://user:password@localhost:5432/seo_platform"
alembic upgrade head
cd ..

# Install dependencies if needed
if [ ! -d "node_modules" ]; then
    echo "📦 Installing frontend dependencies..."
    npm install
fi

if [ ! -d "backend/.venv" ]; then
    echo "🐍 Setting up Python virtual environment..."
    cd backend
    python -m venv .venv
    source .venv/bin/activate
    pip install -r requirements.txt
    cd ..
fi

# Start the application services
echo "🎯 Starting application services..."

# Start backend API
echo "🔧 Starting FastAPI backend..."
cd backend
source .venv/bin/activate
uvicorn main:app --reload --host 0.0.0.0 --port 8000 &
BACKEND_PID=$!
cd ..

# Start Celery worker
echo "👷 Starting Celery worker..."
cd backend
source .venv/bin/activate
celery -A worker.celery worker --loglevel=info &
WORKER_PID=$!
cd ..

# Start frontend
echo "🎨 Starting Next.js frontend..."
npm run dev &
FRONTEND_PID=$!

# Function to cleanup background processes
cleanup() {
    echo "🧹 Cleaning up processes..."
    kill $BACKEND_PID $WORKER_PID $FRONTEND_PID 2>/dev/null
    docker-compose stop
    exit 0
}

# Trap Ctrl+C
trap cleanup INT

echo ""
echo "🎉 SEO Automation Platform is starting up!"
echo ""
echo "📱 Frontend:     http://localhost:3000"
echo "🔧 Backend API:  http://localhost:8000"
echo "📚 API Docs:     http://localhost:8000/docs"
echo "👷 Task Monitor: http://localhost:5555"
echo "💾 MinIO Console: http://localhost:9001"
echo ""
echo "Press Ctrl+C to stop all services"
echo ""

# Wait for all background processes
wait
