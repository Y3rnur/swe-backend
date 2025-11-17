# Supplier-Wholesale Exchange Backend

A production-ready FastAPI backend for a B2B supplier-wholesale exchange platform. This system enables suppliers to manage their catalogs, consumers to browse and order products, and provides comprehensive features for link management, order processing, chat communication, complaint handling, and notifications.

## 🚀 Features

### Authentication & Authorization

- User registration and authentication (JWT-based)
- Role-based access control (RBAC)
- Password hashing with bcrypt
- Access and refresh token support
- User profile management

### Link Management

- Consumer link requests to suppliers
- Supplier approval/denial workflow
- Link status state machine (pending → accepted/denied → blocked)
- Access control for catalog visibility

### Product & Catalog Management

- Supplier product CRUD operations
- Product activation/deactivation
- SKU uniqueness validation
- Consumer catalog browsing (requires accepted link)
- Active product filtering

### Order Management

- Order creation with multiple items
- Automatic total calculation
- Order status workflow (pending → accepted/rejected → in_progress → completed)
- Quantity validation
- Access control by role

### Chat System

- Consumer-initiated chat sessions with sales representatives
- Real-time messaging (HTTP polling)
- Order-linked chat sessions
- Participant-only access control

### Complaint Management

- Consumer complaint filing
- Sales rep and manager assignment
- Status escalation workflow (open → escalated → resolved)
- Resolution tracking

### Notifications

- User-scoped notifications
- Read/unread status tracking
- Pagination and filtering support
- Ready for service hook integration

## 🛠 Tech Stack

- **Framework:** FastAPI (Python 3.13.5+)
- **Database:** PostgreSQL with async SQLAlchemy 2.x
- **Migrations:** Alembic
- **Validation:** Pydantic v2
- **Testing:** pytest, httpx, pytest-asyncio
- **Code Quality:** Ruff (linter/formatter), mypy (type checking), pre-commit hooks
- **Authentication:** JWT tokens, bcrypt password hashing

## 📋 Prerequisites

- Python 3.13.5 or higher
- PostgreSQL database
- pip (Python package manager)

## 🏃 Quick Start

### 1. Clone and Setup

```bash
# Create virtual environment
python -m venv .venv

# Activate virtual environment
# Windows PowerShell:
.venv\Scripts\Activate.ps1
# Windows CMD:
.venv\Scripts\activate.bat
# Linux/Mac:
source .venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

### 2. Configure Environment

```bash
# Copy example environment file
cp env.example .env

# Edit .env with your settings:
# - DATABASE_URL: PostgreSQL connection string
# - SECRET_KEY: JWT secret key (change in production!)
# - Other settings as needed
```

### 3. Database Setup

```bash
# Run migrations
python -m alembic upgrade head
```

### 4. Start Server

```bash
# Development mode (with hot reload)
python -m uvicorn app.main:app --reload
```

**Server:** http://localhost:8000 **API Docs:** http://localhost:8000/docs **ReDoc:** http://localhost:8000/redoc

## 🐳 Docker

```bash
# Start services (database + app)
docker-compose up -d

# View logs
docker-compose logs -f

# Stop services
docker-compose down
```

## 📚 API Endpoints

All endpoints are prefixed with `/api/v1`.

### Authentication

- `POST /api/v1/auth/signup` - Register new user
- `POST /api/v1/auth/login` - Authenticate user
- `POST /api/v1/auth/refresh` - Refresh access token

### Users

- `GET /api/v1/users/me` - Get current user profile

### Links

- `POST /api/v1/links/requests` - Create link request (consumer)
- `PATCH /api/v1/links/{id}/status` - Update link status (supplier owner/manager)
- `GET /api/v1/links/{id}` - Get single link
- `GET /api/v1/links` - List consumer's links (paginated)
- `GET /api/v1/links/incoming` - List incoming link requests (supplier owner/manager)

### Products

- `POST /api/v1/products` - Create product (supplier owner/manager)
- `PUT /api/v1/products/{id}` - Update product (supplier owner/manager)
- `DELETE /api/v1/products/{id}` - Delete product (supplier owner/manager)
- `GET /api/v1/products` - List products (paginated, filtered by supplier)

### Catalog

- `GET /api/v1/catalog` - Browse supplier catalog (consumer, requires accepted link)

### Orders

- `POST /api/v1/orders` - Create order (consumer)
- `GET /api/v1/orders/{id}` - Get single order
- `GET /api/v1/orders` - List orders (paginated, filtered by role)
- `PATCH /api/v1/orders/{id}/status` - Update order status (supplier owner/manager)

### Chats

- `POST /api/v1/chats/sessions` - Create chat session (consumer)
- `GET /api/v1/chats/sessions` - List chat sessions (filtered by role)
- `POST /api/v1/chats/sessions/{id}/messages` - Send message (participants only)
- `GET /api/v1/chats/sessions/{id}/messages` - Get messages (participants only, paginated)

### Complaints

- `POST /api/v1/complaints` - Create complaint (consumer)
- `GET /api/v1/complaints/{id}` - Get single complaint
- `GET /api/v1/complaints` - List complaints (filtered by role, paginated)
- `PATCH /api/v1/complaints/{id}/status` - Update complaint status (sales rep/manager)

### Notifications

- `GET /api/v1/notifications` - List notifications (current user, paginated)
- `PATCH /api/v1/notifications/{id}/read` - Mark notification as read

### Health

- `GET /api/v1/health` - Health check endpoint

## 🧪 Testing

```bash
# Run all tests
python -m pytest

# Run with coverage
python -m pytest --cov=app --cov-report=html

# Run specific test file
python -m pytest tests/test_auth_integration.py

# Run with verbose output
python -m pytest -v

# Run with specific test
python -m pytest tests/test_orders_integration.py::test_create_order_as_consumer -xvs
```

**Test Coverage:** 117+ integration and unit tests covering all endpoints and business logic.

## 🛠 Development Commands

```bash
# Development server (hot reload)
python -m uvicorn app.main:app --reload

# Run linter
python -m ruff check app tests

# Format code
python -m ruff format app tests

# Type checking
python -m mypy app

# Create migration
python -m alembic revision --autogenerate -m "description"

# Apply migrations
python -m alembic upgrade head

# Rollback migration
python -m alembic downgrade -1
```

## 📁 Project Structure

```
swe-backend/
├── app/
│   ├── api/
│   │   ├── routers/          # API route handlers
│   │   │   ├── auth.py       # Authentication endpoints
│   │   │   ├── users.py      # User endpoints
│   │   │   ├── links.py      # Link management
│   │   │   ├── products.py   # Product management
│   │   │   ├── catalog.py    # Consumer catalog
│   │   │   ├── orders.py     # Order management
│   │   │   ├── chats.py      # Chat system
│   │   │   ├── complaints.py # Complaint handling
│   │   │   └── notifications.py # Notifications
│   │   ├── deps.py           # FastAPI dependencies
│   │   └── helpers.py        # Helper functions
│   ├── core/
│   │   ├── config.py         # Application settings
│   │   ├── logging.py        # Logging configuration
│   │   ├── middleware.py     # Request/response middleware
│   │   ├── roles.py          # Role definitions
│   │   └── security.py       # JWT & password hashing
│   ├── db/
│   │   ├── base.py           # SQLAlchemy base
│   │   └── session.py        # Database session
│   ├── models/               # SQLAlchemy models
│   ├── schemas/              # Pydantic schemas
│   └── utils/                # Utility functions
├── alembic/                  # Database migrations
├── tests/                    # Test suite
├── docs/                     # Documentation
└── requirements.txt          # Python dependencies
```

## 🔐 User Roles

- **consumer**: End users who purchase products
- **supplier_owner**: Owners of supplier businesses
- **supplier_manager**: Managers within supplier organizations
- **supplier_sales**: Sales representatives for suppliers
- **admin**: System administrators

## 📝 API Standards

### Error Response Format

```json
{
  "detail": "Error message",
  "code": "ERROR_CODE",
  "meta": { ... }
}
```

### Pagination Response Format

```json
{
  "items": [...],
  "page": 1,
  "size": 20,
  "total": 123,
  "pages": 7
}
```

## 🔒 Security Features

- JWT-based authentication
- Password hashing with bcrypt
- Role-based access control (RBAC)
- Request validation with Pydantic
- SQL injection protection (SQLAlchemy ORM)
- CORS configuration
- Environment-based configuration

## 📊 Database Models

The system includes 12 core domain models:

1. **User** - User accounts and authentication
2. **Supplier** - Supplier businesses
3. **Consumer** - Consumer organizations
4. **SupplierStaff** - Supplier staff members
5. **Product** - Product catalog items
6. **Link** - Consumer-Supplier relationships
7. **Order** - Purchase orders
8. **OrderItem** - Order line items
9. **ChatSession** - Chat conversations
10. **ChatMessage** - Chat messages
11. **Complaint** - Customer complaints
12. **Notification** - User notifications

## 🚦 Status

**Current Phase:** Phase 11 (Notifications) - ✅ Complete

**Completed Phases:**

- ✅ Phase 0: Groundwork & Project Setup
- ✅ Phase 1: Project Scaffold
- ✅ Phase 2: Configuration, Logging, DB Session
- ✅ Phase 3: Domain Model Baseline
- ✅ Phase 4: Security & RBAC
- ✅ Phase 5: Auth & User APIs
- ✅ Phase 6: Link Management
- ✅ Phase 7: Catalog & Products
- ✅ Phase 8: Orders
- ✅ Phase 9: Chat
- ✅ Phase 10: Complaints
- ✅ Phase 11: Notifications

## 📖 Documentation

- **API Documentation:** Available at `/docs` (Swagger UI) and `/redoc` (ReDoc)
- **Project Charter:** See `docs/PROJECT_CHARTER.md`

## 🤝 Contributing

1. Follow the existing code style (enforced by Ruff)
2. Write tests for new features
3. Ensure all tests pass before submitting
4. Run type checking with mypy
5. Follow the API versioning and error response standards

## 📄 License

[Add your license here]

---

**Version:** 1.0.0 **Last Updated:** 2025-11-17
