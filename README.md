# SEO Automation Platform

An AI-powered SEO automation platform for content optimization at scale. This platform allows you to crawl websites, process content with AI, manage SEO optimizations in spreadsheet-like tables, and publish results back to your CMS.

## Features

### 🕷️ Advanced Web Crawler
- JavaScript rendering with Playwright
- Bot detection workarounds
- Respect robots.txt with override options
- Full site crawls or directed CSV-based crawls
- Extract all SEO elements automatically

### 🧠 AI-Powered Content Processing
- HTML to Markdown conversion with content cleanup
- Vector embeddings for semantic search
- RAG-powered chat agent with site context
- 30+ built-in SEO prompt templates

### 📊 Spreadsheet-Like Interface
- Filter and sort pages by any criteria
- Bulk run AI optimizations across rows
- Context columns for prompt input
- Inline editing with change history

### 🤖 SEO Chat Agent
- Site-aware AI assistant
- Built-in SEO tools (SERP analysis, schema validation, etc.)
- Content gap analysis
- Optimization recommendations

### 📤 Export & Publishing
- CSV export for external workflows
- WordPress integration with plugin
- Compatible with Yoast, RankMath, AIOSEO, The SEO Framework
- Approval workflows before publishing

## Architecture

### Frontend
- **Next.js 14** with App Router
- **React 18** with TypeScript
- **TanStack Table** for advanced data tables
- **TanStack Query** for server state management
- **Tailwind CSS** for styling
- **Radix UI** for accessible components

### Backend
- **FastAPI** (Python) for API server
- **SQLAlchemy** with async support
- **PostgreSQL** with pgvector extension
- **Celery** for background task processing
- **Redis** for caching and task queues

### AI/ML Stack
- **Sentence Transformers** for embeddings
- **LiteLLM** for multi-provider LLM access
- **Ollama** for local LLM inference
- **OpenAI/Anthropic/Google** API support

### Infrastructure
- **Docker Compose** for development
- **MinIO** for S3-compatible storage
- **Playwright** for web crawling
- **Alembic** for database migrations

## Quick Start

### Prerequisites
- Docker and Docker Compose
- Node.js 18+ (for local development)
- Python 3.11+ (for local development)

### 1. Clone and Setup

```bash
git clone <repository-url>
cd seo-automation-platform
cp env.example .env
```

### 2. Configure Environment

Edit `.env` file with your settings:
- Database credentials
- API keys for LLM providers
- Authentication settings (Clerk or Supabase)

### 3. Start with Docker

```bash
# Start all services
docker-compose up -d

# Check service health
docker-compose ps

# View logs
docker-compose logs -f backend
```

### 4. Initialize Database

```bash
# Run migrations
docker-compose exec backend alembic upgrade head

# Create initial data (optional)
docker-compose exec backend python scripts/seed_data.py
```

### 5. Access Applications

- **Frontend**: http://localhost:3000
- **Backend API**: http://localhost:8000
- **API Docs**: http://localhost:8000/docs
- **Task Monitor**: http://localhost:5555
- **MinIO Console**: http://localhost:9001

## Development

### Backend Development

```bash
cd backend

# Install dependencies
pip install -r requirements.txt

# Run database
docker-compose up postgres redis -d

# Run migrations
alembic upgrade head

# Start development server
uvicorn main:app --reload

# Start worker
celery -A worker.celery worker --loglevel=info
```

### Frontend Development

```bash
# Install dependencies
npm install

# Start development server
npm run dev

# Type checking
npm run type-check

# Linting
npm run lint
```

## API Documentation

The API is fully documented with OpenAPI/Swagger:
- Interactive docs: http://localhost:8000/docs
- OpenAPI spec: http://localhost:8000/openapi.json

### Key Endpoints

| Endpoint | Description |
|----------|-------------|
| `POST /api/auth/register` | Register new user |
| `GET /api/sites` | List sites |
| `POST /api/crawls` | Start site crawl |
| `GET /api/pages` | List pages with filters |
| `POST /api/runs` | Execute prompt templates |
| `POST /api/chat` | Chat with SEO agent |
| `POST /api/exports/csv` | Export data to CSV |

## Database Schema

### Core Tables
- `organizations` - Multi-tenant organization structure
- `users` - User accounts with role-based access
- `sites` - Websites to crawl and optimize
- `pages` - Individual web pages with content
- `page_elements` - Extracted SEO elements
- `page_embeddings` - Vector embeddings for search

### AI/Processing Tables
- `prompt_templates` - Reusable AI prompt templates
- `prompt_runs` - Bulk AI processing jobs
- `row_generations` - Individual AI outputs
- `crawls` - Website crawling jobs

### Integration Tables
- `wordpress_integrations` - WordPress site connections
- `publish_jobs` - Content publishing tasks
- `credit_ledger` - Usage tracking and billing

## Prompt Templates

The platform ships with 30+ built-in SEO templates:

### Title & Meta Templates
- **Title Tag Generator**: Creates optimized page titles
- **Meta Description Generator**: Writes compelling descriptions
- **Primary Keywords Extractor**: Identifies main keywords

### Content Templates
- **Content Gap Analysis**: Find missing topics
- **Internal Link Suggestions**: Recommend link opportunities
- **Tone Guide Generator**: Create brand voice guidelines

### Technical SEO Templates
- **Schema Generator**: Create JSON-LD structured data
- **Element Scorer**: Rate current SEO elements
- **Typo & Grammar Checker**: Fix content issues

## WordPress Integration

### Plugin Installation
1. Download the plugin from `/wordpress-plugin/`
2. Install via WordPress admin or upload manually
3. Configure API endpoint and authentication

### Supported SEO Plugins
- **Yoast SEO**: Full meta field integration
- **RankMath**: Title and description support
- **All in One SEO**: Complete field mapping
- **The SEO Framework**: Core meta fields

### Publishing Workflow
1. Generate content with AI templates
2. Review in spreadsheet interface
3. Approve and queue for publishing
4. Monitor publish jobs status
5. Verify changes in WordPress

## Chat Agent Tools

### Built-in Tools
- `site_search()` - Semantic search across pages
- `get_page()` - Retrieve page details
- `serp_analysis()` - Analyze search results
- `char_count()` / `word_count()` - Text metrics
- `schema_validate()` - Validate structured data
- `compare_pages()` - Compare page differences

### Custom Workflows
- Find pages needing refresh
- Generate brand tone guides
- Content gap analysis vs competitors
- Schema markup recommendations

## Deployment

### Production Deployment

1. **Database Setup**
   ```bash
   # Use managed PostgreSQL with pgvector
   # Configure connection string in production
   ```

2. **Backend Deployment**
   ```bash
   # Build production image
   docker build -t seo-platform-backend ./backend
   
   # Deploy to your container platform
   # Set environment variables
   ```

3. **Frontend Deployment**
   ```bash
   # Build Next.js app
   npm run build
   
   # Deploy to Vercel, Netlify, or similar
   ```

### Environment Variables

See `env.example` for all configuration options.

Critical production settings:
- `DATABASE_URL` - PostgreSQL connection
- `REDIS_URL` - Redis for tasks and caching
- `SECRET_KEY` - JWT signing secret
- `OPENAI_API_KEY` - For AI features
- `CLERK_SECRET_KEY` - Authentication

## Contributing

### Development Workflow
1. Fork the repository
2. Create a feature branch
3. Make changes with tests
4. Submit a pull request

### Code Standards
- **Python**: Black formatting, type hints
- **TypeScript**: Strict mode, ESLint rules
- **Database**: Alembic migrations for all changes
- **API**: OpenAPI documentation required

### Testing
```bash
# Backend tests
cd backend
pytest

# Frontend tests
npm test

# End-to-end tests
npm run test:e2e
```

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Support

- **Documentation**: [docs.example.com](https://docs.example.com)
- **Issues**: [GitHub Issues](https://github.com/example/issues)
- **Discord**: [Community Server](https://discord.gg/example)
- **Email**: support@example.com
