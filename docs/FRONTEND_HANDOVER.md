# Frontend Handover Guide

This document provides everything frontend teams need to integrate with the B2B Supplier-Wholesale Exchange Platform API.

## 📋 Table of Contents

1. [API Base URL](#api-base-url)
2. [Authentication](#authentication)
3. [CORS Configuration](#cors-configuration)
4. [OpenAPI Documentation](#openapi-documentation)
5. [End-to-End Flows](#end-to-end-flows)
6. [Sample cURL Commands](#sample-curl-commands)
7. [Postman Collection](#postman-collection)
8. [Common Patterns](#common-patterns)
9. [Error Handling](#error-handling)

## 🌐 API Base URL

- **Development**: `http://localhost:8000`
- **Staging**: `https://api-staging.example.com`
- **Production**: `https://api.example.com`

All API endpoints are prefixed with `/api/v1` (e.g., `/api/v1/auth/login`).

## 🔐 Authentication

### JWT Token Flow

1. **Login/Signup** → Receive `access_token` and `refresh_token`
2. **Include Token** → Add to `Authorization` header: `Bearer <access_token>`
3. **Token Expiry** → Access token expires after 30 minutes
4. **Refresh Token** → Use `/api/v1/auth/refresh` to get new tokens

### Request Headers

```http
Authorization: Bearer <access_token>
Content-Type: application/json
X-Correlation-ID: <optional-correlation-id>
```

### Response Headers

```http
X-Correlation-ID: <correlation-id>
```

### Example: Authenticated Request

```bash
curl -X GET "http://localhost:8000/api/v1/products" \
  -H "Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..." \
  -H "Content-Type: application/json"
```

## 🌍 CORS Configuration

### Allowed Origins

- **Development**: `http://localhost:3000`, `http://localhost:8000`
- **Production**: Configured via `CORS_ORIGINS` environment variable

### CORS Headers

The API automatically handles CORS for configured origins:

- `Access-Control-Allow-Origin`: Set to requesting origin
- `Access-Control-Allow-Credentials`: `true`
- `Access-Control-Allow-Methods`: `*` (all methods)
- `Access-Control-Allow-Headers`: `*` (all headers)

### Preflight Requests

The API handles OPTIONS preflight requests automatically. No special handling needed in frontend.

## 📚 OpenAPI Documentation

### Accessing Documentation

- **Swagger UI**: `http://localhost:8000/docs`
- **ReDoc**: `http://localhost:8000/redoc`
- **OpenAPI JSON**: `http://localhost:8000/openapi.json`

### OpenAPI Schema

The `/openapi.json` endpoint provides a stable OpenAPI 3.0 schema that can be imported into:
- Postman
- Insomnia
- Swagger Codegen
- OpenAPI Generator
- Frontend code generators

### Example: Fetch OpenAPI Schema

```bash
curl http://localhost:8000/openapi.json > openapi.json
```

## 🔄 End-to-End Flows

### Consumer Flow

1. **Signup** → Create consumer account
2. **Login** → Get access token
3. **Request Link** → Request connection to supplier
4. **Wait for Approval** → Supplier approves/denies link
5. **View Catalog** → Browse supplier products (after link accepted)
6. **Place Order** → Create order with items
7. **Chat** → Start chat session with sales rep
8. **File Complaint** → Create complaint if needed

### Supplier Flow

1. **Signup** → Create supplier owner account
2. **Login** → Get access token
3. **Add Staff** → Create manager/sales rep accounts
4. **Manage Products** → Create/update products
5. **Approve/Deny Links** → Manage consumer link requests
6. **Manage Orders** → View and update order status
7. **Handle Complaints** → Respond to consumer complaints

## 📝 Sample cURL Commands

### Authentication

#### 1. Consumer Signup

```bash
curl -X POST "http://localhost:8000/api/v1/auth/signup" \
  -H "Content-Type: application/json" \
  -d '{
    "email": "consumer@example.com",
    "password": "SecurePass123",
    "role": "consumer"
  }'
```

**Response:**
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer"
}
```

#### 2. Login

```bash
curl -X POST "http://localhost:8000/api/v1/auth/login" \
  -H "Content-Type: application/json" \
  -d '{
    "email": "consumer@example.com",
    "password": "SecurePass123"
  }'
```

#### 3. Refresh Token

```bash
curl -X POST "http://localhost:8000/api/v1/auth/refresh" \
  -H "Content-Type: application/json" \
  -d '{
    "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
  }'
```

### Link Management

#### 4. Request Link (Consumer)

```bash
curl -X POST "http://localhost:8000/api/v1/links" \
  -H "Authorization: Bearer <access_token>" \
  -H "Content-Type: application/json" \
  -d '{
    "supplier_id": 1
  }'
```

#### 5. Approve Link (Supplier Owner)

```bash
curl -X PATCH "http://localhost:8000/api/v1/links/1/status" \
  -H "Authorization: Bearer <supplier_owner_token>" \
  -H "Content-Type: application/json" \
  -d '{
    "status": "accepted"
  }'
```

### Product Management

#### 6. Create Product (Supplier Owner/Manager)

```bash
curl -X POST "http://localhost:8000/api/v1/products" \
  -H "Authorization: Bearer <supplier_token>" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Premium Widget",
    "description": "High-quality widget for industrial use",
    "price_kzt": "15000.00",
    "currency": "KZT",
    "sku": "WID-001",
    "stock_qty": 100,
    "is_active": true
  }'
```

#### 7. List Products (Consumer - after link accepted)

```bash
curl -X GET "http://localhost:8000/api/v1/catalog/suppliers/1/products?page=1&size=20" \
  -H "Authorization: Bearer <consumer_token>"
```

### Order Management

#### 8. Create Order (Consumer)

```bash
curl -X POST "http://localhost:8000/api/v1/orders" \
  -H "Authorization: Bearer <consumer_token>" \
  -H "Content-Type: application/json" \
  -d '{
    "supplier_id": 1,
    "items": [
      {"product_id": 1, "qty": 5},
      {"product_id": 2, "qty": 3}
    ]
  }'
```

#### 9. Update Order Status (Supplier Owner/Manager)

```bash
curl -X PATCH "http://localhost:8000/api/v1/orders/1/status" \
  -H "Authorization: Bearer <supplier_token>" \
  -H "Content-Type: application/json" \
  -d '{
    "status": "accepted"
  }'
```

### Chat

#### 10. Create Chat Session (Consumer)

```bash
curl -X POST "http://localhost:8000/api/v1/chats/sessions" \
  -H "Authorization: Bearer <consumer_token>" \
  -H "Content-Type: application/json" \
  -d '{
    "sales_rep_id": 3,
    "order_id": 1
  }'
```

#### 11. Send Message

```bash
curl -X POST "http://localhost:8000/api/v1/chats/sessions/1/messages" \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{
    "text": "Hello, I have a question about my order"
  }'
```

### Complaints

#### 12. Create Complaint (Consumer)

```bash
curl -X POST "http://localhost:8000/api/v1/complaints" \
  -H "Authorization: Bearer <consumer_token>" \
  -H "Content-Type: application/json" \
  -d '{
    "order_id": 1,
    "sales_rep_id": 3,
    "manager_id": 2,
    "description": "Product arrived damaged. Need replacement or refund."
  }'
```

#### 13. Update Complaint Status (Sales Rep/Manager)

```bash
curl -X PATCH "http://localhost:8000/api/v1/complaints/1/status" \
  -H "Authorization: Bearer <supplier_token>" \
  -H "Content-Type: application/json" \
  -d '{
    "status": "resolved",
    "resolution": "Replacement product shipped. Tracking number: TRACK123456"
  }'
```

### Supplier Staff Management

#### 14. Add Staff Member (Supplier Owner)

```bash
curl -X POST "http://localhost:8000/api/v1/users/staff" \
  -H "Authorization: Bearer <supplier_owner_token>" \
  -H "Content-Type: application/json" \
  -d '{
    "email": "manager@supplier.com",
    "password": "SecurePass123",
    "role": "supplier_manager"
  }'
```

## 📦 Postman Collection

A Postman collection is available at `docs/postman_collection.json`. Import it into Postman or Insomnia.

### Import Instructions

1. **Postman**:
   - File → Import
   - Select `docs/postman_collection.json`
   - Collection will include all endpoints with examples

2. **Insomnia**:
   - Create → Import From → File
   - Select `docs/postman_collection.json`

### Environment Variables

Set these variables in Postman/Insomnia:

- `base_url`: `http://localhost:8000`
- `access_token`: (auto-set after login)
- `refresh_token`: (auto-set after login)
- `consumer_token`: Token for consumer user
- `supplier_owner_token`: Token for supplier owner
- `supplier_manager_token`: Token for supplier manager
- `supplier_sales_token`: Token for supplier sales rep

## 🎯 Common Patterns

### Pagination

Most list endpoints support pagination:

```http
GET /api/v1/orders?page=1&size=20
```

**Response:**
```json
{
  "items": [...],
  "page": 1,
  "size": 20,
  "total": 100,
  "pages": 5
}
```

### Error Response Format

All errors follow this structure:

```json
{
  "detail": "Error message",
  "code": "ERROR_CODE",
  "meta": {
    "additional": "information"
  }
}
```

### Common Error Codes

- `VALIDATION_ERROR`: Invalid input data
- `UNAUTHORIZED`: Missing or invalid token
- `FORBIDDEN`: Insufficient permissions
- `NOT_FOUND`: Resource not found
- `DUPLICATE_RESOURCE`: Resource already exists
- `RATE_LIMIT_EXCEEDED`: Too many requests

## ⚠️ Error Handling

### HTTP Status Codes

- `200 OK`: Success
- `201 Created`: Resource created
- `400 Bad Request`: Invalid input
- `401 Unauthorized`: Authentication required
- `403 Forbidden`: Insufficient permissions
- `404 Not Found`: Resource not found
- `409 Conflict`: Resource conflict (e.g., duplicate)
- `422 Unprocessable Entity`: Validation error
- `429 Too Many Requests`: Rate limit exceeded
- `500 Internal Server Error`: Server error

### Example Error Response

```json
{
  "detail": "Validation error: Invalid input data",
  "code": "VALIDATION_ERROR",
  "meta": {
    "errors": [
      {
        "field": "email",
        "message": "value is not a valid email address",
        "type": "value_error.email"
      }
    ]
  }
}
```

## 🔗 Quick Links

- **API Documentation**: `http://localhost:8000/docs`
- **OpenAPI Schema**: `http://localhost:8000/openapi.json`
- **Health Check**: `http://localhost:8000/health`
- **Security Guide**: [docs/SECURITY.md](SECURITY.md)

## 📞 Support

For questions or issues:
1. Check the OpenAPI documentation at `/docs`
2. Review error messages (they include correlation IDs)
3. Contact the backend team with the correlation ID from response headers
