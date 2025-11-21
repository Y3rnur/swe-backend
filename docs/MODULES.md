# Module Documentation

This document provides a comprehensive overview of each module in the B2B Supplier-Wholesale Exchange Platform.

## 📋 Table of Contents

1. [Authentication Module](#authentication-module)
2. [User Management Module](#user-management-module)
3. [Link Management Module](#link-management-module)
4. [Product Management Module](#product-management-module)
5. [Catalog Module](#catalog-module)
6. [Order Management Module](#order-management-module)
7. [Chat Module](#chat-module)
8. [Complaint Management Module](#complaint-management-module)
9. [Notification Module](#notification-module)

---

## 🔐 Authentication Module

### Purpose

The Authentication module handles user registration, login, and token management. It provides JWT-based authentication with access and refresh tokens, enabling secure API access for all other modules.

### Key Features

- User registration (signup) for consumers and supplier owners
- User authentication (login) with email and password
- JWT token generation (access token: 30min, refresh token: 7 days)
- Token refresh mechanism for seamless user experience
- Password hashing with bcrypt (12 rounds)
- Password policy enforcement (min 8 chars, uppercase, lowercase, digit)

### Endpoints

- `POST /api/v1/auth/signup` - Register a new user
- `POST /api/v1/auth/login` - Authenticate and get tokens
- `POST /api/v1/auth/refresh` - Refresh access token

### Data Models

- **User**: Stores user credentials, role, and active status
- **TokenResponse**: Contains access_token, refresh_token, and token_type

### Example Flow

1. Consumer signs up with email and password
2. System validates password policy and creates user
3. Returns JWT tokens (access + refresh)
4. Client stores tokens and uses access token for API calls
5. When access token expires, use refresh token to get new tokens

---

## 👤 User Management Module

### Purpose

The User Management module provides endpoints for managing user profiles and supplier staff. It enables supplier owners to add managers and sales representatives to their organization.

### Key Features

- Get current authenticated user information
- Add staff members (managers, sales reps) to supplier organization
- Role-based access control (only supplier owners can add staff)

### Endpoints

- `GET /api/v1/users/me` - Get current user information
- `POST /api/v1/users/staff` - Add staff member (supplier owner only)

### Data Models

- **User**: User account with email, role, and active status
- **SupplierStaff**: Links users to suppliers with staff roles (manager/sales)

### Example Flow

1. Supplier owner logs in
2. Owner adds a manager by providing email and password
3. System creates user with supplier_manager role
4. System links user to supplier via SupplierStaff
5. Manager can now log in and access supplier resources

---

## 🔗 Link Management Module

### Purpose

The Link Management module manages the relationship between consumers and suppliers. Consumers must establish an "accepted" link with a supplier before they can view products and place orders.

### Key Features

- Consumer-initiated link requests
- Supplier approval/denial workflow
- Link status state machine (pending → accepted/denied → blocked)
- Access control for catalog visibility (requires accepted link)

### Endpoints

- `POST /api/v1/links` - Request link to supplier (consumer only)
- `PATCH /api/v1/links/{link_id}/status` - Approve/deny link (supplier owner only)
- `GET /api/v1/links/{link_id}` - Get specific link
- `GET /api/v1/links` - List links (filtered by role)

### Data Models

- **Link**: Represents consumer-supplier relationship
  - Status: PENDING, ACCEPTED, DENIED, BLOCKED
  - Links Consumer to Supplier

### Example Flow

1. Consumer requests link to a supplier
2. Link created with PENDING status
3. Supplier owner reviews and approves link
4. Link status changes to ACCEPTED
5. Consumer can now view supplier catalog and place orders

---

## 📦 Product Management Module

### Purpose

The Product Management module enables suppliers to manage their product catalog. Suppliers can create, update, activate/deactivate, and delete products. Products are only visible to consumers with accepted links.

### Key Features

- Product CRUD operations (supplier owner/manager only)
- SKU uniqueness validation per supplier
- Product activation/deactivation
- Stock quantity management
- Price management in KZT

### Endpoints

- `POST /api/v1/products` - Create product (supplier owner/manager)
- `PUT /api/v1/products/{product_id}` - Update product (supplier owner/manager)
- `DELETE /api/v1/products/{product_id}` - Delete product (supplier owner only)
- `GET /api/v1/products` - List supplier's products

### Data Models

- **Product**: Product information
  - Fields: name, description, price_kzt, currency, sku, stock_qty, is_active
  - Linked to Supplier

### Example Flow

1. Supplier owner/manager creates a product with details
2. System validates SKU uniqueness for supplier
3. Product is created and set to active
4. Product appears in catalog for consumers with accepted links
5. Supplier can update price, stock, or deactivate product

---

## 🛍️ Catalog Module

### Purpose

The Catalog module provides read-only access to supplier catalogs for consumers. It enables consumers to browse suppliers and their products after establishing accepted links.

### Key Features

- List all suppliers (consumers with accepted links)
- Browse products from specific suppliers
- Pagination support
- Active product filtering

### Endpoints

- `GET /api/v1/catalog/suppliers` - List suppliers (consumer only)
- `GET /api/v1/catalog/suppliers/{supplier_id}/products` - Get supplier products (consumer only)

### Data Models

- Uses Product and Supplier models from other modules
- Returns paginated responses

### Example Flow

1. Consumer has accepted link with supplier
2. Consumer requests list of suppliers
3. System returns suppliers where consumer has accepted links
4. Consumer selects supplier and views products
5. Consumer can see active products with prices and stock

---

## 📋 Order Management Module

### Purpose

The Order Management module handles the complete order lifecycle from creation to completion. Consumers create orders, and suppliers manage order status through a state machine.

### Key Features

- Order creation with multiple items
- Automatic total calculation
- Order status state machine (pending → accepted/rejected → in_progress → completed)
- Quantity validation against product stock
- Access control by role (consumers create, suppliers manage)

### Endpoints

- `POST /api/v1/orders` - Create order (consumer only)
- `GET /api/v1/orders/{order_id}` - Get specific order
- `GET /api/v1/orders` - List orders (filtered by role)
- `PATCH /api/v1/orders/{order_id}/status` - Update order status (supplier owner/manager)

### Data Models

- **Order**: Order header
  - Status: PENDING, ACCEPTED, REJECTED, IN_PROGRESS, COMPLETED
  - Total amount in KZT
  - Links Consumer to Supplier
- **OrderItem**: Order line items
  - Product reference, quantity, unit price
  - Snapshot of price at time of order

### Example Flow

1. Consumer creates order with items from supplier catalog
2. System validates quantities against stock
3. System calculates total and creates order with PENDING status
4. Supplier owner/manager reviews and accepts order
5. Order status changes to ACCEPTED, then IN_PROGRESS, then COMPLETED

---

## 💬 Chat Module

### Purpose

The Chat module enables real-time communication between consumers and supplier sales representatives. It supports order-linked conversations for context.

### Key Features

- Consumer-initiated chat sessions
- Order-linked conversations
- Message exchange between participants
- Participant-only access control
- File URL support (no direct uploads)

### Endpoints

- `POST /api/v1/chats/sessions` - Create chat session (consumer only)
- `GET /api/v1/chats/sessions` - List chat sessions (filtered by role)
- `POST /api/v1/chats/sessions/{session_id}/messages` - Send message
- `GET /api/v1/chats/sessions/{session_id}/messages` - Get messages

### Data Models

- **ChatSession**: Chat conversation
  - Links Consumer to Sales Rep
  - Optional Order reference
- **ChatMessage**: Individual messages
  - Text content
  - Optional file URL
  - Sender and timestamp

### Example Flow

1. Consumer creates chat session with sales rep (optionally linked to order)
2. Consumer sends message asking about order status
3. Sales rep responds with information
4. Conversation continues with both participants able to send messages
5. Messages are paginated for efficient loading

---

## 🚨 Complaint Management Module

### Purpose

The Complaint Management module handles consumer complaints about orders. It provides a structured workflow for complaint resolution with escalation capabilities.

### Key Features

- Consumer complaint filing
- Sales rep and manager assignment
- Status escalation workflow (open → escalated → resolved)
- Resolution tracking
- Access control by role

### Endpoints

- `POST /api/v1/complaints` - Create complaint (consumer only)
- `GET /api/v1/complaints/{complaint_id}` - Get specific complaint
- `GET /api/v1/complaints` - List complaints (filtered by role)
- `PATCH /api/v1/complaints/{complaint_id}/status` - Update complaint status (sales rep/manager)

### Data Models

- **Complaint**: Complaint record
  - Status: OPEN, ESCALATED, RESOLVED
  - Links to Order, Consumer, Sales Rep, Manager
  - Description and optional resolution text

### Example Flow

1. Consumer files complaint about an order
2. Complaint created with OPEN status
3. Sales rep reviews and escalates if needed
4. Manager handles escalated complaints
5. Complaint resolved with resolution text
6. Status changes to RESOLVED (final state)

---

## 🔔 Notification Module

### Purpose

The Notification module provides a notification system for important events. Users receive notifications for order updates, link approvals, and other relevant events.

### Key Features

- Automatic notification generation
- Notification listing with pagination
- Mark as read functionality
- Role-based notification filtering

### Endpoints

- `GET /api/v1/notifications` - List notifications (current user)
- `PATCH /api/v1/notifications/{notification_id}/read` - Mark notification as read

### Data Models

- **Notification**: Notification record
  - Message content
  - Notification type
  - Read status
  - Links to User

### Example Flow

1. System event occurs (e.g., order status change)
2. Notification created for relevant users
3. User fetches notifications
4. User marks notification as read
5. Notification persists for history

---

## 🔄 Module Interactions

### Typical Workflow

1. **Authentication** → User logs in, gets tokens
2. **Link Management** → Consumer requests link, supplier approves
3. **Product Management** → Supplier creates products
4. **Catalog** → Consumer browses products
5. **Order Management** → Consumer places order, supplier manages status
6. **Chat** → Consumer and sales rep communicate about order
7. **Complaint Management** → If issues arise, complaint is filed and resolved
8. **Notifications** → Users receive updates throughout the process

### Data Flow

- All modules depend on **Authentication** for user identification
- **Link Management** gates access to **Catalog** and **Order Management**
- **Order Management** triggers **Notifications**
- **Chat** can reference **Orders** for context
- **Complaint Management** references **Orders** and **Users**

---

## 📊 Database Schema Overview

### Core Entities

- **User**: Base user accounts (all roles)
- **Supplier**: Supplier businesses
- **Consumer**: Consumer organizations
- **SupplierStaff**: Links users to suppliers (manager/sales roles)

### Business Entities

- **Product**: Supplier products
- **Link**: Consumer-Supplier relationships
- **Order**: Purchase orders
- **OrderItem**: Order line items
- **ChatSession**: Chat conversations
- **ChatMessage**: Chat messages
- **Complaint**: Consumer complaints
- **Notification**: User notifications

### Relationships

- User → Supplier (1:1 for owners)
- User → Consumer (1:1)
- User → SupplierStaff (1:many for managers/sales)
- Supplier → Product (1:many)
- Consumer ↔ Supplier (many:many via Link)
- Consumer → Order (1:many)
- Supplier → Order (1:many)
- Order → OrderItem (1:many)
- Order → ChatSession (1:1 optional)
- Order → Complaint (1:many)
