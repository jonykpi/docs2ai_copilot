# Docs2AI Copilot API Documentation

## Base URL
All API endpoints are relative to your Odoo instance base URL (e.g., `http://localhost:8069`)

## Authentication
All endpoints require Bearer token authentication. Include the token in the Authorization header:
```
Authorization: Bearer YOUR_API_TOKEN
```

## Response Format
All responses are in JSON format with the following structure:

**Success Response:**
```json
{
  "status": "success",
  "message": "Optional message",
  "data": { ... },
  "count": 10,
  "total": 100
}
```

**Error Response:**
```json
{
  "status": "error",
  "message": "Error description"
}
```

---

## Table of Contents
1. [Expense APIs](#expense-apis)
2. [Tax APIs](#tax-apis)
3. [Vendor APIs](#vendor-apis)
4. [Manager APIs](#manager-apis)
5. [Category APIs](#category-apis)
6. [Customer APIs](#customer-apis)
7. [Bill APIs](#bill-apis)

---

## Expense APIs

### List Expenses
**GET** `/api/expenses`

Get a list of all expenses with pagination.

**Query Parameters:**
- `limit` (optional, default: 100) - Maximum number of records to return
- `offset` (optional, default: 0) - Number of records to skip

**Example Request:**
```bash
GET /api/expenses?limit=50&offset=0
Authorization: Bearer YOUR_TOKEN
```

**Example Response:**
```json
{
  "status": "success",
  "count": 10,
  "total": 150,
  "data": [
    {
      "id": 1,
      "name": "Business Lunch",
      "employee_id": 5,
      "employee_name": "John Doe",
      "date": "2024-01-15",
      "product_id": 10,
      "product_name": "Meal",
      "quantity": 1.0,
      "price_unit": 50.0,
      "total_amount": 50.0,
      "total_amount_currency": 50.0,
      "currency_id": "USD",
      "payment_mode": "own_account",
      "payment_mode_label": "Employee (to reimburse)",
      "vendor_id": 3,
      "vendor_name": "Restaurant ABC",
      "manager_id": 2,
      "manager_name": "Jane Manager",
      "department_id": 1,
      "department_name": "Sales",
      "state": "draft",
      "tax_ids": [1, 2],
      "tax_names": ["Tax 10%", "Tax 5%"],
      "account_id": 20,
      "account_name": "Travel Expenses",
      "company_id": 1,
      "company_name": "My Company"
    }
  ]
}
```

### Create Expense
**POST** `/api/expenses`

Create a new expense with all available options.

**Request Body:**
```json
{
  "name": "Business Lunch",
  "employee_id": 5,
  "date": "2024-01-15",
  "category_id": 10,
  "quantity": 1.0,
  "price_unit": 50.0,
  "total_amount": 50.0,
  "total_amount_currency": 50.0,
  "currency": "USD",
  "payment_mode": "own_account",
  "vendor_id": 3,
  "manager_id": 2,
  "tax_ids": [1, 2],
  "account_id": 20,
  "description": "Client meeting lunch",
  "analytic_distribution": {},
  "attachment": {
    "name": "receipt.pdf",
    "data": "base64_encoded_file_data",
    "mimetype": "application/pdf"
  }
}
```

**Field Descriptions:**
- `name` (required) - Expense description
- `employee_id` (required) - ID of the employee (if not provided, uses current user's employee)
- `date` (optional) - Expense date (YYYY-MM-DD format)
- `category_id` (optional) - Category/Product ID (alias for `product_id`)
- `product_id` (optional) - Product ID (same as `category_id`, use either one)
- `quantity` (optional) - Quantity, default: 1.0
- `price_unit` (optional) - Unit price
- `total_amount` (optional) - Total amount in company currency
- `total_amount_currency` (optional) - Total amount in expense currency
- `currency` (optional) - Currency code (e.g., "USD", "EUR", "GTQ") or currency ID (alias for `currency_id`)
- `currency_id` (optional) - Currency code or currency ID (same as `currency`, use either one)
- `payment_mode` (optional) - Payment mode:
  - `"own_account"` - Employee (to reimburse)
  - `"company_account"` - Company
- `vendor_id` (optional) - Vendor/Supplier ID
- `manager_id` (optional) - Manager/Approver user ID
- `tax_ids` (optional) - Array of tax IDs
- `account_id` (optional) - Account ID
- `description` (optional) - Internal notes
- `analytic_distribution` (optional) - Analytic distribution object
- `attachment` (optional) - Receipt/document attachment object:
  - `name` - File name (e.g., "receipt.pdf")
  - `data` - Base64 encoded file data
  - `mimetype` - MIME type (e.g., "application/pdf", "image/jpeg", "image/png")

**Example Request:**
```bash
POST /api/expenses
Authorization: Bearer YOUR_TOKEN
Content-Type: application/json

{
  "name": "Business Lunch",
  "employee_id": 5,
  "date": "2024-01-15",
  "payment_mode": "own_account",
  "total_amount": 50.0,
  "currency_id": "USD"
}
```

**Example Response:**
```json
{
  "status": "success",
  "message": "Expense created successfully",
  "data": {
    "id": 1,
    "name": "Business Lunch",
    "employee_id": 5,
    "employee_name": "John Doe",
    "date": "2024-01-15",
    "product_id": null,
    "product_name": "",
    "quantity": 1.0,
    "price_unit": 50.0,
    "total_amount": 50.0,
    "total_amount_currency": 50.0,
    "currency_id": "USD",
    "payment_mode": "own_account",
    "payment_mode_label": "Employee (to reimburse)",
    "vendor_id": null,
    "vendor_name": "",
    "manager_id": null,
    "manager_name": "",
    "state": "draft",
    "tax_ids": [],
    "attachment_id": 123
  }
}
```

**Example Request with Attachment:**
```bash
POST /api/expenses
Authorization: Bearer YOUR_TOKEN
Content-Type: application/json

{
  "name": "Business Lunch",
  "employee_id": 5,
  "date": "2024-01-15",
  "category_id": 10,
  "payment_mode": "own_account",
  "total_amount": 50.0,
  "currency": "USD",
  "attachment": {
    "name": "receipt.jpg",
    "data": "/9j/4AAQSkZJRgABAQEAYABgAAD...",
    "mimetype": "image/jpeg"
  }
}
```

**Note:** The attachment `data` field should contain base64-encoded file content. Supported file types include:
- PDF: `application/pdf`
- Images: `image/jpeg`, `image/png`, `image/gif`, `image/bmp`, `image/webp`

---

## Tax APIs

### List Taxes
**GET** `/api/taxes`

Get a list of all taxes with optional filtering.

**Query Parameters:**
- `limit` (optional, default: 100) - Maximum number of records to return
- `offset` (optional, default: 0) - Number of records to skip
- `type_tax_use` (optional) - Filter by tax type:
  - `"sale"` - Sales taxes
  - `"purchase"` - Purchase taxes
  - `"none"` - Other taxes

**Example Request:**
```bash
GET /api/taxes?type_tax_use=purchase&limit=50
Authorization: Bearer YOUR_TOKEN
```

**Example Response:**
```json
{
  "status": "success",
  "count": 5,
  "total": 15,
  "data": [
    {
      "id": 1,
      "name": "Tax 10%",
      "amount": 10.0,
      "amount_type": "percent",
      "type_tax_use": "purchase",
      "type_tax_use_label": "Purchase",
      "company_id": 1,
      "company_name": "My Company",
      "active": true
    }
  ]
}
```

### Create Tax
**POST** `/api/taxes`

Create a new tax.

**Request Body:**
```json
{
  "name": "Tax 10%",
  "amount": 10.0,
  "amount_type": "percent",
  "type_tax_use": "purchase",
  "company_id": 1
}
```

**Field Descriptions:**
- `name` (required) - Tax name
- `amount` (required) - Tax amount/percentage
- `amount_type` (optional, default: "percent") - Amount type (usually "percent")
- `type_tax_use` (optional, default: "none") - Tax type:
  - `"sale"` - Sales tax
  - `"purchase"` - Purchase tax
  - `"none"` - Other
- `company_id` (optional) - Company ID

**Example Request:**
```bash
POST /api/taxes
Authorization: Bearer YOUR_TOKEN
Content-Type: application/json

{
  "name": "VAT 15%",
  "amount": 15.0,
  "type_tax_use": "purchase"
}
```

**Example Response:**
```json
{
  "status": "success",
  "message": "Tax created successfully",
  "data": {
    "id": 5,
    "name": "VAT 15%",
    "amount": 15.0,
    "amount_type": "percent",
    "type_tax_use": "purchase",
    "type_tax_use_label": "Purchase",
    "company_id": 1,
    "company_name": "My Company",
    "active": true
  }
}
```

---

## Vendor APIs

### List Vendors
**GET** `/api/vendors`

Get a list of all vendors (suppliers).

**Query Parameters:**
- `limit` (optional, default: 100) - Maximum number of records to return
- `offset` (optional, default: 0) - Number of records to skip

**Example Request:**
```bash
GET /api/vendors?limit=50&offset=0
Authorization: Bearer YOUR_TOKEN
```

**Example Response:**
```json
{
  "status": "success",
  "count": 10,
  "total": 200,
  "data": [
    {
      "id": 1,
      "name": "Supplier ABC",
      "email": "contact@supplier.com",
      "phone": "+1234567890",
      "mobile": "",
      "street": "123 Main St",
      "street2": "",
      "city": "New York",
      "state_id": "NY",
      "zip": "10001",
      "country_id": "United States",
      "vat": "US123456789",
      "is_company": true,
      "supplier_rank": 1
    }
  ]
}
```

### Create Vendor
**POST** `/api/vendors`

Create a new vendor (supplier).

**Request Body:**
```json
{
  "name": "Supplier ABC",
  "email": "contact@supplier.com",
  "phone": "+1234567890",
  "mobile": "+0987654321",
  "street": "123 Main St",
  "street2": "Suite 100",
  "city": "New York",
  "state_id": "NY",
  "zip": "10001",
  "country_id": "United States",
  "vat": "US123456789",
  "is_company": true
}
```

**Field Descriptions:**
- `name` (required) - Vendor name
- `email` (optional) - Email address
- `phone` (optional) - Phone number
- `mobile` (optional) - Mobile number
- `street` (optional) - Street address
- `street2` (optional) - Street address line 2
- `city` (optional) - City
- `state_id` (optional) - State name
- `zip` (optional) - ZIP/Postal code
- `country_id` (optional) - Country name or code
- `vat` (optional) - VAT/Tax ID
- `is_company` (optional) - Whether it's a company (true/false)

**Example Request:**
```bash
POST /api/vendors
Authorization: Bearer YOUR_TOKEN
Content-Type: application/json

{
  "name": "New Supplier",
  "email": "info@newsupplier.com",
  "is_company": true
}
```

**Example Response:**
```json
{
  "status": "success",
  "message": "Vendor created successfully",
  "data": {
    "id": 10,
    "name": "New Supplier",
    "email": "info@newsupplier.com",
    "phone": "",
    "mobile": "",
    "street": "",
    "street2": "",
    "city": "",
    "state_id": "",
    "zip": "",
    "country_id": "",
    "vat": "",
    "is_company": true,
    "supplier_rank": 1
  }
}
```

### Delete Vendor
**DELETE** `/api/vendors/<vendor_id>`

Delete a vendor by ID.

**Example Request:**
```bash
DELETE /api/vendors/10
Authorization: Bearer YOUR_TOKEN
```

**Example Response:**
```json
{
  "status": "success",
  "message": "Vendor \"New Supplier\" deleted successfully"
}
```

**Error Response (404):**
```json
{
  "status": "error",
  "message": "Vendor with ID 10 not found"
}
```

---

## Manager APIs

### List Managers
**GET** `/api/managers`

Get a list of all managers (users with expense approval rights).

**Query Parameters:**
- `limit` (optional, default: 100) - Maximum number of records to return
- `offset` (optional, default: 0) - Number of records to skip

**Example Request:**
```bash
GET /api/managers?limit=50
Authorization: Bearer YOUR_TOKEN
```

**Example Response:**
```json
{
  "status": "success",
  "count": 5,
  "total": 10,
  "data": [
    {
      "id": 2,
      "name": "Jane Manager",
      "login": "jane.manager",
      "email": "jane@company.com",
      "employee_id": 3,
      "employee_name": "Jane Doe",
      "active": true
    }
  ]
}
```

### Create Manager
**POST** `/api/managers`

Create a new manager (user with expense approval rights).

**Request Body:**
```json
{
  "name": "John Manager",
  "login": "john.manager",
  "email": "john@company.com",
  "password": "secure_password123",
  "employee_id": 5
}
```

**Field Descriptions:**
- `name` (required) - Manager full name
- `login` (required) - Login username (must be unique)
- `password` (required) - Password for the user
- `email` (optional) - Email address
- `employee_id` (optional) - Link to employee record

**Example Request:**
```bash
POST /api/managers
Authorization: Bearer YOUR_TOKEN
Content-Type: application/json

{
  "name": "New Manager",
  "login": "new.manager",
  "password": "password123",
  "email": "newmanager@company.com"
}
```

**Example Response:**
```json
{
  "status": "success",
  "message": "Manager created successfully",
  "data": {
    "id": 15,
    "name": "New Manager",
    "login": "new.manager",
    "email": "newmanager@company.com",
    "employee_id": null,
    "employee_name": "",
    "active": true
  }
}
```

---

## Customer APIs

### List Customers
**GET** `/api/customers`

Get a list of all customers.

**Query Parameters:**
- `limit` (optional, default: 100) - Maximum number of records to return
- `offset` (optional, default: 0) - Number of records to skip

**Example Request:**
```bash
GET /api/customers?limit=50
Authorization: Bearer YOUR_TOKEN
```

**Example Response:**
```json
{
  "status": "success",
  "count": 10,
  "total": 500,
  "data": [
    {
      "id": 1,
      "name": "Customer ABC",
      "email": "customer@example.com",
      "phone": "+1234567890",
      "customer_rank": 1,
      "is_company": true
    }
  ]
}
```

### Create Customer
**POST** `/api/customers`

Create a new customer. Same structure as vendor creation, but sets `customer_rank` instead of `supplier_rank`.

---

## Category APIs

### List Categories
**GET** `/api/categories`

Get a list of expense categories (products that can be expensed).

**Query Parameters:**
- `limit` (optional, default: 100) - Maximum number of records to return
- `offset` (optional, default: 0) - Number of records to skip

**Example Request:**
```bash
GET /api/categories?limit=50&offset=0
Authorization: Bearer YOUR_TOKEN
```

**Example Response:**
```json
{
  "status": "success",
  "count": 10,
  "total": 25,
  "data": [
    {
      "id": 1,
      "name": "Meals",
      "description": "Restaurants, business lunches, etc.",
      "default_code": "FOOD",
      "type": "service",
      "categ_id": 1,
      "categ_name": "Expenses",
      "standard_price": 0.0,
      "uom_id": 1,
      "uom_name": "Units",
      "company_id": 1,
      "company_name": "My Company",
      "active": true
    }
  ]
}
```

### Create Category
**POST** `/api/categories`

Create a new expense category (product that can be expensed).

**Request Body:**
```json
{
  "name": "Meals",
  "description": "Restaurants, business lunches, etc.",
  "default_code": "FOOD",
  "type": "service",
  "categ_id": 1,
  "standard_price": 0.0,
  "uom_id": 1,
  "company_id": 1
}
```

**Field Descriptions:**
- `name` (required) - Category name
- `description` (optional) - Category description
- `default_code` (optional) - Internal reference code
- `type` (optional, default: "service") - Product type: `"service"` or `"consu"`
- `categ_id` (optional) - Product category ID
- `standard_price` (optional, default: 0.0) - Standard price
- `uom_id` (optional) - Unit of Measure ID (defaults to "Units" if not provided)
- `company_id` (optional) - Company ID

**Example Request:**
```bash
POST /api/categories
Authorization: Bearer YOUR_TOKEN
Content-Type: application/json

{
  "name": "Travel & Accommodation",
  "description": "Hotel, plane ticket, taxi, etc.",
  "default_code": "TRAVEL",
  "type": "service"
}
```

**Example Response:**
```json
{
  "status": "success",
  "message": "Category created successfully",
  "data": {
    "id": 5,
    "name": "Travel & Accommodation",
    "description": "Hotel, plane ticket, taxi, etc.",
    "default_code": "TRAVEL",
    "type": "service",
    "categ_id": null,
    "categ_name": "",
    "standard_price": 0.0,
    "uom_id": 1,
    "uom_name": "Units",
    "can_be_expensed": true,
    "company_id": 1,
    "company_name": "My Company",
    "active": true
  }
}
```

**Note:** Categories are automatically set with `can_be_expensed=True` and `purchase_ok=True` when created through this API.

---

## Bill APIs

### List Bills
**GET** `/api/bills`

Get a list of vendor bills and purchase receipts.

**Query Parameters:**
- `limit` (optional, default: 100) - Maximum number of records to return
- `offset` (optional, default: 0) - Number of records to skip

**Example Request:**
```bash
GET /api/bills?limit=50
Authorization: Bearer YOUR_TOKEN
```

### Create Bill
**POST** `/api/bills`

Create a new vendor bill or purchase receipt.

**Request Body:**
```json
{
  "type": "bill",
  "partner_id": 1,
  "invoice_date": "2024-01-15",
  "invoice_date_due": "2024-02-15",
  "currency": "USD",
  "invoice_line_ids": [
    {
      "product_id": 1,
      "name": "Product Description",
      "quantity": 1.0,
      "price_unit": 100.0,
      "tax": 10,
      "account_id": 1
    }
  ],
  "attachment": {
    "name": "bill.pdf",
    "data": "base64_encoded_data",
    "mimetype": "application/pdf"
  }
}
```

**Field Descriptions:**
- `type` (optional, default: "bill") - Type: `"bill"` or `"receipt"`
- `partner_id` (required) - Vendor/Partner ID
- `invoice_date` (optional) - Invoice date (YYYY-MM-DD)
- `invoice_date_due` (optional) - Due date (YYYY-MM-DD)
- `currency` (optional) - Currency code (e.g., "USD", "EUR")
- `invoice_line_ids` (optional) - Array of invoice lines
- `attachment` (optional) - Attachment object with `name`, `data` (base64), and `mimetype`

---

## Payment Mode Options

When creating expenses, use these values for `payment_mode`:

- **`"own_account"`** - Employee (to reimburse)
- **`"company_account"`** - Company

---

## Error Codes

- **200** - Success
- **201** - Created successfully
- **400** - Bad Request (validation error, missing required fields)
- **404** - Not Found (resource doesn't exist)
- **500** - Internal Server Error

---

## Notes

1. All dates should be in ISO format: `YYYY-MM-DD`
2. All monetary values are decimal numbers
3. Currency codes should be ISO 4217 codes (e.g., "USD", "EUR", "GBP")
4. Tax IDs and other IDs should be integers
5. When creating expenses, if `employee_id` is not provided, the system will try to use the current user's employee ID
6. Managers are automatically assigned the expense team approver group
7. Taxes are automatically configured with repartition lines based on the tax type

---

## Example: Complete Expense Creation Flow

```bash
# 1. Create a vendor
POST /api/vendors
{
  "name": "Restaurant XYZ",
  "email": "info@restaurant.com",
  "is_company": true
}

# 2. Create a tax
POST /api/taxes
{
  "name": "Sales Tax 10%",
  "amount": 10.0,
  "type_tax_use": "purchase"
}

# 3. Create a manager (if needed)
POST /api/managers
{
  "name": "Approval Manager",
  "login": "approval.manager",
  "password": "secure123",
  "email": "approval@company.com"
}

# 4. Create an expense
POST /api/expenses
{
  "name": "Team Lunch",
  "employee_id": 5,
  "date": "2024-01-15",
  "total_amount": 150.0,
  "total_amount_currency": 150.0,
  "currency_id": "USD",
  "payment_mode": "own_account",
  "vendor_id": 1,
  "manager_id": 2,
  "tax_ids": [1],
  "description": "Monthly team lunch"
}
```

---

## Support

For issues or questions, please contact your system administrator or refer to the Odoo documentation.

