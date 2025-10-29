# QuickPoll Backend API

A robust, real-time polling platform backend built with FastAPI, PostgreSQL, and Redis. This RESTful API provides comprehensive functionality for creating polls, managing votes, user authentication, and real-time updates via WebSockets.

## 📋 Table of Contents

- [Overview](#overview)
- [Features](#features)
- [Tech Stack](#tech-stack)
- [Prerequisites](#prerequisites)
- [Installation](#installation)
- [Configuration](#configuration)
- [Running the Application](#running-the-application)
- [API Documentation](#api-documentation)
- [Database Models](#database-models)
- [Project Structure](#project-structure)
- [Testing](#testing)
- [Deployment](#deployment)
- [Contributing](#contributing)

## 🎯 Overview

QuickPoll Backend is a high-performance API server designed to handle real-time polling operations. It provides:

- **RESTful API** endpoints for all core operations
- **WebSocket support** for real-time updates
- **JWT-based authentication** for secure user management
- **Redis caching** for improved performance
- **PostgreSQL database** for reliable data persistence
- **Comprehensive error handling** and logging
- **Rate limiting** and security middleware

## ✨ Features

### Core Features

- **Poll Management**
  - Create, read, update, and delete polls
  - Support for single-choice and multiple-choice polls
  - Poll expiration and activation/deactivation
  - Poll search and filtering
  - Trending, popular, and recent polls
  - Poll statistics and analytics

- **Voting System**
  - Cast votes (authenticated and anonymous)
  - Support for single and multiple votes
  - Vote validation and duplicate prevention
  - Real-time vote count updates
  - Vote statistics and analytics

- **User Management**
  - User registration and authentication
  - JWT-based token system
  - User profiles and settings
  - User poll history
  - User statistics

- **Likes System**
  - Like/unlike polls
  - Like count tracking
  - Real-time like updates

- **Real-Time Updates**
  - WebSocket connections for poll-specific updates
  - Global updates broadcasting
  - User-specific notifications
  - Live vote count updates

- **Analytics & Statistics**
  - Poll analytics
  - Vote statistics
  - User analytics
  - Trending polls algorithm

- **Security Features**
  - Password hashing with bcrypt
  - JWT token authentication
  - CORS middleware
  - Rate limiting
  - Input validation
  - SQL injection prevention

## 🛠 Tech Stack

### Core Framework
- **FastAPI** (v0.104.1) - Modern, fast web framework for building APIs
- **Python** (v3.11.9) - Programming language
- **Uvicorn** - ASGI server for running FastAPI
- **Gunicorn** - Production WSGI HTTP Server

### Database
- **PostgreSQL** - Primary relational database
- **SQLAlchemy** (v2.0.23) - SQL toolkit and ORM
- **Alembic** (v1.12.1) - Database migration tool
- **psycopg2-binary** (v2.9.9) - PostgreSQL adapter

### Caching & Real-Time
- **Redis** (v5.0.1) - In-memory data structure store for caching
- **aioredis** (v2.0.1) - Async Redis client
- **websockets** (v12.0) - WebSocket library

### Authentication & Security
- **python-jose** (v3.3.0) - JWT implementation
- **passlib** (v1.7.4) - Password hashing library (bcrypt)
- **python-multipart** (v0.0.6) - For handling form data

### Utilities
- **Pydantic** (v2.5.0) - Data validation using Python type annotations
- **pydantic-settings** (v2.1.0) - Settings management
- **python-dotenv** (v1.0.0) - Environment variable management
- **structlog** (v23.2.0) - Structured logging
- **slowapi** (v0.1.9) - Rate limiting
- **httpx** (v0.25.2) - HTTP client
- **aiohttp** (v3.9.1) - Async HTTP client

### Development & Testing
- **pytest** (v7.4.3) - Testing framework
- **pytest-asyncio** (v0.21.1) - Async test support
- **pytest-cov** (v4.1.0) - Test coverage

## 📦 Prerequisites

Before you begin, ensure you have the following installed:

- **Python** 3.10 or higher
- **PostgreSQL** 12 or higher
- **Redis** 6.0 or higher (optional but recommended)
- **pip** - Python package manager
- **virtualenv** (recommended) - For creating isolated Python environments

## 🚀 Installation

### 1. Clone the Repository

```bash
git clone <repository-url>
cd backend
```

### 2. Create Virtual Environment

```bash
# On Windows
python -m venv venv
venv\Scripts\activate

# On macOS/Linux
python3 -m venv venv
source venv/bin/activate
```

### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

### 4. Set Up PostgreSQL Database

Create a new PostgreSQL database:

```sql
CREATE DATABASE quickpoll;
```

Or using command line:

```bash
createdb quickpoll
```

### 5. Set Up Redis (Optional)

Install and start Redis:

```bash
# On macOS (using Homebrew)
brew install redis
brew services start redis

# On Ubuntu/Debian
sudo apt-get install redis-server
sudo systemctl start redis

# On Windows
# Download from https://redis.io/download
```

## ⚙️ Configuration

### Environment Variables

Create a `.env` file in the `backend` directory with the following variables:

```env
# Application Settings
APP_NAME=QuickPoll
APP_VERSION=1.0.0
DEBUG=True
ENVIRONMENT=development

# Database Configuration
DATABASE_URL=postgresql://postgres:password@localhost:5432/quickpoll

# Redis Configuration
REDIS_URL=redis://localhost:6379
REDIS_PASSWORD=

# Upstash Redis (Optional - for production)
UPSTASH_REDIS_REST_URL=
UPSTASH_REDIS_REST_TOKEN=

# Security Configuration
SECRET_KEY=your-secret-key-change-in-production-use-a-long-random-string
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30

# CORS Configuration
ALLOWED_ORIGINS=["http://localhost:3000","http://127.0.0.1:3000"]

# WebSocket Configuration
WEBSOCKET_HEARTBEAT_INTERVAL=30
WEBSOCKET_MAX_CONNECTIONS=1000

# Rate Limiting
RATE_LIMIT_REQUESTS=100
RATE_LIMIT_WINDOW=60

# File Upload Configuration
MAX_FILE_SIZE=5242880
ALLOWED_FILE_TYPES=["image/jpeg","image/png","image/gif"]
```

### Configuration Notes

- **SECRET_KEY**: Generate a secure random string for production. Never commit this to version control.
- **DATABASE_URL**: Format: `postgresql://username:password@host:port/database`
- **REDIS_URL**: Format: `redis://host:port` or `redis://:password@host:port`

## 🏃 Running the Application

### Development Mode

```bash
# Activate virtual environment
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Run with auto-reload
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

Or using Python directly:

```bash
python -m app.main
```

The API will be available at:
- **API**: http://localhost:8000
- **Interactive API Docs**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

### Production Mode

Using Gunicorn with Uvicorn workers:

```bash
gunicorn app.main:app \
    --workers 4 \
    --worker-class uvicorn.workers.UvicornWorker \
    --bind 0.0.0.0:8000
```

### Using Docker (Optional)

Create a `Dockerfile`:

```dockerfile
FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

CMD ["gunicorn", "app.main:app", "--workers", "4", "--worker-class", "uvicorn.workers.UvicornWorker", "--bind", "0.0.0.0:8000"]
```

## 📚 API Documentation

### Base URL

```
http://localhost:8000
```

### Authentication

Most endpoints require authentication using JWT tokens. Include the token in the Authorization header:

```
Authorization: Bearer <your-token>
```

### API Endpoints

#### Health Check

- **GET** `/health` - Health check endpoint
- **GET** `/` - Root endpoint with API information
- **GET** `/api/info` - API information and configuration

#### User Endpoints

- **POST** `/api/users/register` - Register a new user
- **POST** `/api/users/login` - Login user
- **GET** `/api/users/me` - Get current user profile
- **GET** `/api/users` - Get list of users (paginated)
- **GET** `/api/users/count` - Get total user count
- **GET** `/api/users/{user_id}` - Get user by ID
- **GET** `/api/users/{user_id}/polls` - Get user's polls

#### Poll Endpoints

- **GET** `/api/polls` - Get list of polls (paginated)
- **GET** `/api/polls/trending` - Get trending polls
- **GET** `/api/polls/popular` - Get popular polls
- **GET** `/api/polls/recent` - Get recent polls
- **GET** `/api/polls/search?q={query}` - Search polls
- **GET** `/api/polls/stats` - Get poll statistics
- **GET** `/api/polls/{poll_id}` - Get poll by ID
- **POST** `/api/polls` - Create a new poll (requires auth)
- **PUT** `/api/polls/{poll_id}` - Update poll (requires auth)
- **DELETE** `/api/polls/{poll_id}` - Delete poll (requires auth)
- **POST** `/api/polls/{poll_id}/activate` - Activate poll
- **POST** `/api/polls/{poll_id}/deactivate` - Deactivate poll

#### Vote Endpoints

- **POST** `/api/votes` - Cast vote(s) (requires auth)
- **GET** `/api/votes/poll/{poll_id}` - Get votes for a poll
- **GET** `/api/votes/poll/{poll_id}/stats` - Get vote statistics
- **GET** `/api/votes/user/{user_id}` - Get user's votes
- **GET** `/api/votes/{vote_id}` - Get vote by ID
- **DELETE** `/api/votes/{vote_id}` - Delete vote (requires auth)

#### Like Endpoints

- **POST** `/api/likes` - Like a poll (requires auth)
- **DELETE** `/api/likes/{like_id}` - Unlike a poll (requires auth)
- **GET** `/api/likes/user/{user_id}` - Get user's likes

#### WebSocket Endpoints

- **WS** `/ws/poll/{poll_id}` - Connect to poll-specific updates
- **WS** `/ws/user/{user_id}` - Connect to user-specific updates
- **WS** `/ws/global` - Connect to global updates

### Request/Response Examples

#### Register User

```bash
POST /api/users/register
Content-Type: application/json

{
  "username": "johndoe",
  "email": "john@example.com",
  "password": "securepassword123"
}
```

#### Create Poll

```bash
POST /api/polls
Authorization: Bearer <token>
Content-Type: application/json

{
  "title": "What's your favorite programming language?",
  "description": "Let's find out what the community prefers",
  "options": ["Python", "JavaScript", "Rust", "Go"],
  "allow_multiple": false
}
```

#### Cast Vote

```bash
POST /api/votes
Authorization: Bearer <token>
Content-Type: application/json

{
  "poll_id": "550e8400-e29b-41d4-a716-446655440000",
  "option_ids": ["6ba7b810-9dad-11d1-80b4-00c04fd430c8"]
}
```

## 🗄️ Database Models

### User Model

- `id` (UUID) - Primary key
- `username` (String) - Unique username
- `email` (String) - Unique email address
- `hashed_password` (String) - Bcrypt hashed password
- `is_active` (Boolean) - Account status
- `is_verified` (Boolean) - Email verification status
- `created_at` (DateTime) - Account creation timestamp
- `updated_at` (DateTime) - Last update timestamp
- `last_login` (DateTime) - Last login timestamp

### Poll Model

- `id` (UUID) - Primary key
- `title` (String, max 200) - Poll title
- `description` (Text) - Poll description
- `slug` (String) - URL-friendly slug
- `author_id` (UUID) - Foreign key to User
- `is_active` (Boolean) - Poll active status
- `allow_multiple` (Boolean) - Multiple votes allowed
- `is_public` (Boolean) - Public visibility
- `expires_at` (DateTime) - Expiration timestamp
- `total_votes` (Integer) - Denormalized vote count
- `likes_count` (Integer) - Denormalized likes count
- `views_count` (Integer) - View count
- `created_at` (DateTime) - Creation timestamp
- `updated_at` (DateTime) - Update timestamp

### Option Model

- `id` (UUID) - Primary key
- `poll_id` (UUID) - Foreign key to Poll
- `text` (String, max 100) - Option text
- `vote_count` (Integer) - Denormalized vote count
- `position` (Integer) - Display order

### Vote Model

- `id` (UUID) - Primary key
- `poll_id` (UUID) - Foreign key to Poll
- `option_id` (UUID) - Foreign key to Option
- `user_id` (UUID) - Foreign key to User (nullable)
- `anon_id` (String) - Anonymous identifier
- `ip_address` (String) - Voter IP address
- `user_agent` (String) - Browser user agent
- `created_at` (DateTime) - Vote timestamp

### Like Model

- `id` (UUID) - Primary key
- `poll_id` (UUID) - Foreign key to Poll
- `user_id` (UUID) - Foreign key to User (nullable)
- `anon_id` (String) - Anonymous identifier
- `ip_address` (String) - Liker IP address
- `created_at` (DateTime) - Like timestamp

## 📁 Project Structure

```
backend/
├── app/
│   ├── __init__.py
│   ├── main.py                 # FastAPI application entry point
│   │
│   ├── core/                   # Core configuration and utilities
│   │   ├── config.py           # Application settings
│   │   ├── db.py               # Database connection and session
│   │   ├── redis_client.py     # Redis client configuration
│   │   ├── security.py         # Authentication and security utilities
│   │   └── upstash_redis_client.py  # Upstash Redis client
│   │
│   ├── models/                 # SQLAlchemy database models
│   │   ├── user.py
│   │   ├── poll.py
│   │   ├── option.py
│   │   ├── vote.py
│   │   └── like.py
│   │
│   ├── schemas/                # Pydantic schemas for validation
│   │   ├── user.py
│   │   ├── poll.py
│   │   ├── option.py
│   │   ├── vote.py
│   │   └── like.py
│   │
│   ├── crud/                   # Database CRUD operations
│   │   ├── user.py
│   │   ├── poll.py
│   │   ├── option.py
│   │   ├── vote.py
│   │   └── like.py
│   │
│   ├── routes/                 # API route handlers
│   │   ├── user_routes.py
│   │   ├── poll_routes.py
│   │   ├── vote_routes.py
│   │   ├── like_routes.py
│   │   └── websocket_routes.py
│   │
│   ├── services/               # Business logic services
│   │   ├── poll_service.py
│   │   ├── analytics_service.py
│   │   ├── notification_service.py
│   │   └── websocket_service.py
│   │
│   ├── utils/                  # Utility functions
│   │   ├── exceptions.py       # Custom exceptions
│   │   ├── logger.py           # Logging configuration
│   │   └── response_helper.py  # Response formatting helpers
│   │
│   ├── tests/                  # Test files
│   │   ├── conftest.py
│   │   ├── test_polls.py
│   │   ├── test_votes.py
│   │   └── test_likes.py
│   │
│   └── websocket_manager.py    # WebSocket connection manager
│
├── requirements.txt            # Python dependencies
├── runtime.txt                # Python runtime version
└── README.md                  # This file
```

## 🧪 Testing

### Run Tests

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=app --cov-report=html

# Run specific test file
pytest tests/test_polls.py

# Run with verbose output
pytest -v
```

### Test Structure

Tests are located in the `app/tests/` directory. The test suite includes:

- **Unit tests** for CRUD operations
- **Integration tests** for API endpoints
- **WebSocket tests** for real-time functionality

## 🚢 Deployment

### Production Checklist

- [ ] Set `DEBUG=False` in environment variables
- [ ] Use a strong `SECRET_KEY`
- [ ] Configure production database (PostgreSQL)
- [ ] Set up Redis for caching
- [ ] Configure CORS with production frontend URL
- [ ] Set up SSL/TLS certificates
- [ ] Configure environment variables securely
- [ ] Set up logging and monitoring
- [ ] Configure rate limiting
- [ ] Set up database backups

### Platform-Specific Deployment

#### Heroku

1. Create `Procfile`:
```
web: gunicorn app.main:app --workers 4 --worker-class uvicorn.workers.UvicornWorker --bind 0.0.0.0:$PORT
```

2. Deploy:
```bash
heroku create your-app-name
heroku addons:create heroku-postgresql
heroku addons:create heroku-redis
heroku config:set SECRET_KEY=your-secret-key
git push heroku main
```

#### Railway

1. Set environment variables in Railway dashboard
2. Connect your GitHub repository
3. Railway will auto-detect and deploy

#### Docker

```bash
# Build image
docker build -t quickpoll-backend .

# Run container
docker run -d \
  -p 8000:8000 \
  -e DATABASE_URL=postgresql://... \
  -e SECRET_KEY=... \
  quickpoll-backend
```

### Environment Variables for Production

Ensure all required environment variables are set:

```bash
export DATABASE_URL=postgresql://...
export REDIS_URL=redis://...
export SECRET_KEY=your-secure-random-key
export ENVIRONMENT=production
export DEBUG=False
export ALLOWED_ORIGINS=["https://yourdomain.com"]
```

## 🔒 Security Best Practices

1. **Never commit secrets** to version control
2. **Use environment variables** for sensitive data
3. **Enable HTTPS** in production
4. **Configure CORS** properly
5. **Use strong passwords** and password hashing
6. **Implement rate limiting** to prevent abuse
7. **Validate all inputs** on the server side
8. **Keep dependencies updated** regularly
9. **Use parameterized queries** (SQLAlchemy handles this)
10. **Monitor logs** for suspicious activity

## 📝 API Rate Limits

Default rate limits:
- **100 requests per minute** per IP address
- Rate limit headers are included in responses:
  - `X-RateLimit-Limit`: Maximum requests allowed
  - `X-RateLimit-Remaining`: Remaining requests
  - `X-RateLimit-Reset`: Reset time

## 🐛 Troubleshooting

### Common Issues

1. **Database Connection Error**
   - Verify PostgreSQL is running
   - Check `DATABASE_URL` is correct
   - Ensure database exists

2. **Redis Connection Error**
   - Verify Redis is running
   - Check `REDIS_URL` is correct
   - Application will continue without Redis (with reduced performance)

3. **Import Errors**
   - Ensure virtual environment is activated
   - Verify all dependencies are installed: `pip install -r requirements.txt`

4. **Port Already in Use**
   - Change port: `uvicorn app.main:app --port 8001`
   - Or kill the process using the port

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add some amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## 📄 License

This project is licensed under the MIT License.

## 👥 Support

For support, please open an issue in the repository or contact the development team.

## 🔗 Related Documentation

- [FastAPI Documentation](https://fastapi.tiangolo.com/)
- [SQLAlchemy Documentation](https://docs.sqlalchemy.org/)
- [PostgreSQL Documentation](https://www.postgresql.org/docs/)
- [Redis Documentation](https://redis.io/documentation)

---

**Built with ❤️ using FastAPI and Python**

