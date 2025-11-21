#!/bin/bash
# Demo script for B2B Supplier-Wholesale Exchange Platform
# This script demonstrates the complete flow for both consumer and supplier

set -e

BASE_URL="${BASE_URL:-http://localhost:8000}"
API_URL="${BASE_URL}/api/v1"

# Colors for output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}B2B Supplier-Wholesale Exchange Demo${NC}"
echo -e "${BLUE}========================================${NC}"
echo ""

# Function to print section headers
section() {
    echo ""
    echo -e "${GREEN}>>> $1${NC}"
    echo ""
}

# Function to make API calls
api_call() {
    local method=$1
    local endpoint=$2
    local data=$3
    local token=$4

    if [ -n "$token" ]; then
        if [ -n "$data" ]; then
            curl -s -X "$method" \
                -H "Content-Type: application/json" \
                -H "Authorization: Bearer $token" \
                -d "$data" \
                "${API_URL}${endpoint}"
        else
            curl -s -X "$method" \
                -H "Authorization: Bearer $token" \
                "${API_URL}${endpoint}"
        fi
    else
        if [ -n "$data" ]; then
            curl -s -X "$method" \
                -H "Content-Type: application/json" \
                -d "$data" \
                "${API_URL}${endpoint}"
        else
            curl -s -X "$method" \
                "${API_URL}${endpoint}"
        fi
    fi
}

# Check API health
section "1. Health Check"
echo "Checking API health..."
health=$(api_call GET /health)
echo "$health" | jq '.'
echo ""

# ============================================================================
# CONSUMER FLOW
# ============================================================================
section "2. CONSUMER FLOW - Signup & Login"
echo "Consumer signing up..."
consumer_signup=$(api_call POST /auth/signup '{
    "email": "consumer@example.com",
    "password": "Password123",
    "role": "consumer"
}')
echo "$consumer_signup" | jq '.'
CONSUMER_TOKEN=$(echo "$consumer_signup" | jq -r '.access_token')
echo -e "${YELLOW}Consumer Token: ${CONSUMER_TOKEN:0:50}...${NC}"
echo ""

section "3. CONSUMER FLOW - Request Link"
echo "Consumer requesting link to supplier..."
link_request=$(api_call POST /links '{
    "supplier_id": 1
}' "$CONSUMER_TOKEN")
echo "$link_request" | jq '.'
LINK_ID=$(echo "$link_request" | jq -r '.id')
echo -e "${YELLOW}Link ID: $LINK_ID${NC}"
echo ""

# ============================================================================
# SUPPLIER FLOW
# ============================================================================
section "4. SUPPLIER FLOW - Login"
echo "Supplier owner logging in..."
supplier_login=$(api_call POST /auth/login '{
    "email": "supplier.owner@example.com",
    "password": "Password123"
}')
echo "$supplier_login" | jq '.'
SUPPLIER_TOKEN=$(echo "$supplier_login" | jq -r '.access_token')
echo -e "${YELLOW}Supplier Token: ${SUPPLIER_TOKEN:0:50}...${NC}"
echo ""

section "5. SUPPLIER FLOW - Approve Link"
echo "Supplier owner approving link request..."
link_approve=$(api_call PATCH "/links/${LINK_ID}/status" '{
    "status": "accepted"
}' "$SUPPLIER_TOKEN")
echo "$link_approve" | jq '.'
echo ""

section "6. SUPPLIER FLOW - Create Product"
echo "Supplier creating a product..."
product_create=$(api_call POST /products '{
    "name": "Demo Product",
    "description": "A product created during demo",
    "price_kzt": "20000.00",
    "currency": "KZT",
    "sku": "DEMO-001",
    "stock_qty": 50,
    "is_active": true
}' "$SUPPLIER_TOKEN")
echo "$product_create" | jq '.'
PRODUCT_ID=$(echo "$product_create" | jq -r '.id')
echo -e "${YELLOW}Product ID: $PRODUCT_ID${NC}"
echo ""

# ============================================================================
# CONSUMER FLOW (continued)
# ============================================================================
section "7. CONSUMER FLOW - View Catalog"
echo "Consumer viewing supplier catalog..."
catalog=$(api_call GET "/catalog/suppliers/1/products" "$CONSUMER_TOKEN")
echo "$catalog" | jq '.items[0] | {id, name, price_kzt, stock_qty}'
echo ""

section "8. CONSUMER FLOW - Place Order"
echo "Consumer placing order..."
order_create=$(api_call POST /orders "{
    \"supplier_id\": 1,
    \"items\": [
        {\"product_id\": 1, \"qty\": 3},
        {\"product_id\": 2, \"qty\": 5}
    ]
}" "$CONSUMER_TOKEN")
echo "$order_create" | jq '.'
ORDER_ID=$(echo "$order_create" | jq -r '.id')
echo -e "${YELLOW}Order ID: $ORDER_ID${NC}"
echo ""

section "9. SUPPLIER FLOW - Manage Order"
echo "Supplier viewing order..."
order_view=$(api_call GET "/orders/${ORDER_ID}" "$SUPPLIER_TOKEN")
echo "$order_view" | jq '{id, status, total_kzt, items: .items | length}'
echo ""

echo "Supplier accepting order..."
order_accept=$(api_call PATCH "/orders/${ORDER_ID}/status" '{
    "status": "accepted"
}' "$SUPPLIER_TOKEN")
echo "$order_accept" | jq '{id, status}'
echo ""

# ============================================================================
# CHAT FLOW
# ============================================================================
section "10. CHAT FLOW - Create Session"
echo "Consumer creating chat session..."
chat_session=$(api_call POST /chats/sessions '{
    "sales_rep_id": 3,
    "order_id": '$ORDER_ID'
}' "$CONSUMER_TOKEN")
echo "$chat_session" | jq '.'
SESSION_ID=$(echo "$chat_session" | jq -r '.id')
echo -e "${YELLOW}Chat Session ID: $SESSION_ID${NC}"
echo ""

echo "Consumer sending message..."
message=$(api_call POST "/chats/sessions/${SESSION_ID}/messages" '{
    "text": "Hello, I have a question about my order #'$ORDER_ID'"
}' "$CONSUMER_TOKEN")
echo "$message" | jq '{id, text, sender_id}'
echo ""

# ============================================================================
# COMPLAINT FLOW
# ============================================================================
section "11. COMPLAINT FLOW - Create Complaint"
echo "Consumer creating complaint..."
complaint=$(api_call POST /complaints '{
    "order_id": '$ORDER_ID',
    "sales_rep_id": 3,
    "manager_id": 2,
    "description": "Order items do not match description. Need clarification."
}' "$CONSUMER_TOKEN")
echo "$complaint" | jq '.'
COMPLAINT_ID=$(echo "$complaint" | jq -r '.id')
echo -e "${YELLOW}Complaint ID: $COMPLAINT_ID${NC}"
echo ""

section "12. SUPPLIER FLOW - Resolve Complaint"
echo "Supplier resolving complaint..."
complaint_resolve=$(api_call PATCH "/complaints/${COMPLAINT_ID}/status" '{
    "status": "resolved",
    "resolution": "Issue clarified. Replacement items will be shipped."
}' "$SUPPLIER_TOKEN")
echo "$complaint_resolve" | jq '{id, status, resolution}'
echo ""

# ============================================================================
# SUMMARY
# ============================================================================
section "Demo Complete!"
echo -e "${GREEN}✅ All flows demonstrated successfully!${NC}"
echo ""
echo "Summary:"
echo "  - Consumer signed up and logged in"
echo "  - Consumer requested link to supplier"
echo "  - Supplier approved link"
echo "  - Supplier created product"
echo "  - Consumer viewed catalog"
echo "  - Consumer placed order"
echo "  - Supplier managed order status"
echo "  - Consumer created chat session"
echo "  - Consumer sent message"
echo "  - Consumer filed complaint"
echo "  - Supplier resolved complaint"
echo ""
echo -e "${BLUE}========================================${NC}"
