# Veloo-ai - AI-Powered Quotation & Inventory Management System

An intelligent quotation generation service with integrated inventory management, built with FastAPI, OpenAI, and MongoDB.

## 🌟 Features

### Quotation Management
- 🤖 AI-powered quotation generation using OpenAI GPT
- 🔧 **Tool Calling Integration** - AI automatically queries inventory for real-time pricing
- 📄 Complete CRUD operations for quotations
- 🔍 Search and filter quotations
- 📋 Customer-based quotation retrieval
- ✏️ Update existing quotations with AI assistance

### Inventory Management (NEW!)
- 📦 Complete inventory/materials management system
- 💰 Real-time pricing and availability tracking
- 🏷️ Category-based organization
- 🔎 Advanced search across multiple fields
- 📊 Low stock alerts and statistics
- 🔗 **Seamless integration with quotation generator**

### Technical Features
- 🚀 Fast and scalable with FastAPI
- 💾 MongoDB database with proper indexing
- 🎯 Type-safe with Pydantic models
- 📚 Auto-generated API documentation
- 🧪 Comprehensive test suite

## 🏗️ Architecture

The system integrates inventory data with AI-powered quotation generation using OpenAI's tool calling feature:

```
User Request → FastAPI → AI Generator → Tool Call → MongoDB Inventory
                                    ↓
                            Inventory Data Retrieved
                                    ↓
                            AI Generates Quotation with Real Pricing
```

**Key Innovation**: When generating quotations, the AI automatically queries the inventory database to get current prices and availability, ensuring accurate cost estimates.

## 📦 Quick Start

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

### 2. MongoDB Setup

Install and start MongoDB:

#### Option 1: Local MongoDB Installation
- Download and install MongoDB from https://www.mongodb.com/try/download/community
- Start MongoDB service
- MongoDB will run on default port 27017

#### Option 2: MongoDB Atlas (Cloud)
- Create a free account at https://www.mongodb.com/atlas
- Create a cluster and get your connection string
- Update the `MONGODB_URI` in your `.env` file

### 3. Environment Configuration

Create a `.env` file in the project root:

```env
OPENAI_API_KEY=your_actual_openai_api_key_here
MONGODB_URI=mongodb://localhost:27017/
DATABASE_NAME=quotation_db

# Email Configuration (for sending quotations via email)
SENDER_EMAIL=your_gmail@gmail.com
SENDER_EMAIL_PASSWORD=your_app_password
```

#### Email Setup (Gmail)

The application uses Gmail SMTP to send emails. To configure:

1. **SENDER_EMAIL**: Your Gmail address (e.g., `yourname@gmail.com`)
2. **SENDER_EMAIL_PASSWORD**: Create an **App Password** (regular password won't work):
   - Go to [Google Account Security](https://myaccount.google.com/security)
   - Enable **2-Step Verification** if not already enabled
   - Navigate to [App Passwords](https://myaccount.google.com/apppasswords)
   - Select **"Mail"** and your device, then click **Generate**
   - Copy the 16-character password (spaces are optional)

> ⚠️ **Important**: Do NOT use your regular Gmail password. Google requires App Passwords for third-party applications.

### 4. Run the Application

```bash
python main.py
```

Or using uvicorn directly:

```bash
uvicorn main:app --host 0.0.0.0 --port 8000 --reload
```

The API will be available at: `http://localhost:8000`

### 5. Create Sample Inventory Data (Optional)

```bash
python test_inventory_api.py
```

This will create sample inventory items and test all API endpoints.

## 📚 API Endpoints

### Base URL: `http://localhost:8000`

### 📄 Documentation
- **GET** `/docs` - Interactive API documentation (Swagger UI)
- **GET** `/redoc` - Alternative API documentation
- **GET** `/health` - Health check endpoint

---

## 💼 Quotation Management Endpoints

### Generate Quotation (with AI & Inventory Integration)
**POST** `/quotations/generate`

The AI automatically queries inventory for real-time pricing!

**Request Body:**
```json
{
  "customer_name": "John Doe",
  "phone_number": "+1234567890",
  "address": "123 Main St, City, State",
  "project_start": "2024-01-15",
  "select_task": "Kitchen Renovation",
  "explaination": "Complete kitchen remodel with new cabinets and appliances"
}
```

**Response:**
```json
{
  "id": "507f1f77bcf86cd799439011",
  "customer_name": "John Doe",
  "phone_number": "+1234567890",
  "address": "123 Main St, City, State",
  "task_description": "Kitchen Renovation with modern appliances",
  "bill_of_materials": [
    "Kitchen Cabinets - 15 units @ $200/unit = $3000",
    "Granite Countertop - 20 sqft @ $50/sqft = $1000",
    "Labor - 5 days @ $300/day = $1500"
  ],
  "time": "5-7 days",
  "price": {
    "Materials": 4000.00,
    "Labor": 1500.00,
    "Total": 5500.00
  },
  "timestamp": "2024-01-01T12:00:00"
}
```

### Other Quotation Endpoints
- **POST** `/quotations/save` - Save a quotation directly
- **GET** `/quotations?limit=100&offset=0` - Get all quotations
- **GET** `/quotations/{quotation_id}` - Get specific quotation
- **PUT** `/quotations/update` - Update quotation with AI
- **DELETE** `/quotations/{quotation_id}` - Delete quotation
- **GET** `/quotations/customer/{customer_name}` - Get by customer
- **GET** `/quotations/search/{search_term}` - Search quotations
- **GET** `/quotations/count` - Get total count

---

## 📦 Inventory Management Endpoints (NEW!)

### Create Inventory Item
**POST** `/inventory`

**Request Body:**
```json
{
  "name": "Portland Cement",
  "category": "Construction Materials",
  "description": "High-quality Portland cement",
  "unit": "bag (50kg)",
  "unit_price": 15.50,
  "quantity_available": 100,
  "minimum_quantity": 20,
  "supplier": "BuildMart Suppliers",
  "supplier_contact": "+1234567890",
  "sku": "CEM-PORT-001",
  "is_active": true
}
```

### Get All Inventory Items
**GET** `/inventory?limit=100&offset=0&is_active=true&category=Construction`

### Get Inventory Item by ID
**GET** `/inventory/{item_id}`

### Update Inventory Item
**PUT** `/inventory/{item_id}`

**Request Body (partial update):**
```json
{
  "unit_price": 16.00,
  "quantity_available": 85
}
```

### Delete Inventory Item
**DELETE** `/inventory/{item_id}`

### Search Inventory
**POST** `/inventory/search`

**Request Body:**
```json
{
  "query": "cement",
  "category": "Construction Materials",
  "is_active": true
}
```

### Other Inventory Endpoints
- **GET** `/inventory/category/{category}` - Get items by category
- **GET** `/inventory/stats/count` - Get total item count
- **GET** `/inventory/stats/low-stock` - Get low stock items

---

## 🔧 Tool Calling Integration

### How It Works

When generating a quotation, the AI can automatically query your inventory database:

1. **User submits quotation request** for a construction project
2. **AI analyzes the request** and determines it needs inventory data
3. **AI calls `get_inventory_data()`** with relevant search terms
4. **System queries MongoDB** inventory collection
5. **Real inventory data returned** to AI with prices and availability
6. **AI generates quotation** using actual inventory pricing
7. **User receives accurate quotation** with real costs

### Example Flow

```python
# User Request
"Generate quotation for building a concrete foundation"

# AI automatically calls
get_inventory_data(query="concrete foundation cement rebar")

# Database returns
[
  {name: "Portland Cement", unit_price: 15.50, quantity: 100},
  {name: "Steel Rebar 12mm", unit_price: 8.75, quantity: 150}
]

# AI generates quotation with real pricing
"Portland Cement - 40 bags @ $15.50/bag = $620.00"
"Steel Rebar - 25 pieces @ $8.75/piece = $218.75"
Total Materials: $838.75
```

See `example_tool_calling_flow.py` for a detailed demonstration!

---

## 📊 Data Models

### QuotationRequest
```python
{
  "customer_name": str,
  "phone_number": str,
  "address": str,
  "project_start": str,
  "select_task": str,
  "explaination": str,
  "timestamp": Optional[datetime]
}
```

### FinalQuotation
```python
{
  "customer_name": str,
  "phone_number": str,
  "address": str,
  "task_description": str,
  "bill_of_materials": List[str],
  "time": str,
  "price": {
    "Materials": float,
    "Labor": float,
    "Total": float
  },
  "timestamp": Optional[datetime]
}
```

### InventoryItem
```python
{
  "name": str,                    # Required
  "category": str,                # Required
  "description": str,             # Optional
  "unit": str,                    # Required (kg, m, pieces, etc.)
  "unit_price": float,            # Required
  "quantity_available": float,    # Default: 0
  "minimum_quantity": float,      # Optional (for low stock alerts)
  "supplier": str,                # Optional
  "supplier_contact": str,        # Optional
  "sku": str,                     # Optional (unique)
  "is_active": bool,              # Default: true
  "created_at": datetime,         # Auto-generated
  "updated_at": datetime          # Auto-updated
}
```

---

## 💾 Database

The application uses MongoDB for data persistence with two main collections:

### MongoDB Configuration

```env
MONGODB_URI=mongodb://localhost:27017/  # Local MongoDB
# or
MONGODB_URI=mongodb+srv://username:password@cluster.mongodb.net/  # MongoDB Atlas
DATABASE_NAME=quotation_db
```

### Collections

**1. quotations collection**
- `_id` (ObjectId) - Unique identifier
- `customer_name` (String)
- `phone_number` (String)
- `address` (String)
- `task_description` (String)
- `bill_of_materials` (List[String])
- `time` (String)
- `price` (Object: Materials, Labor, Total)
- `timestamp` (Date)
- `created_at` (Date)
- `updated_at` (Date)

**2. inventory collection** (NEW!)
- `_id` (ObjectId) - Unique identifier
- `name` (String) - Material name
- `category` (String) - Classification
- `description` (String) - Details
- `unit` (String) - Measurement unit
- `unit_price` (Float) - Price per unit
- `quantity_available` (Float) - Current stock
- `minimum_quantity` (Float) - Reorder threshold
- `supplier` (String) - Supplier name
- `supplier_contact` (String) - Contact info
- `sku` (String, Unique) - Stock Keeping Unit
- `is_active` (Boolean) - Active status
- `created_at` (Date)
- `updated_at` (Date)

### Database Indexes

**Quotations:**
- `customer_name` (ascending)
- `phone_number` (ascending)
- `created_at` (descending)
- `timestamp` (descending)

**Inventory:**
- `name` (ascending)
- `category` (ascending)
- `sku` (unique, sparse)
- `is_active` (ascending)
- `created_at` (descending)

### MongoDB Features Used

- **Flexible Schema**: Easy to add new fields without migrations
- **Indexes**: Optimized queries for fast retrieval
- **Text Search**: Full-text search across multiple fields
- **Aggregation**: Efficient counting and analytics
- **Atomic Operations**: Safe concurrent updates

---

## 🧪 Testing

### Run Test Suite
```bash
# Test all inventory endpoints
python test_inventory_api.py
```

### View Tool Calling Demo
```bash
# Interactive demonstration of AI-inventory integration
python example_tool_calling_flow.py
```

### Manual Testing with cURL

**Create Inventory Item:**
```bash
curl -X POST "http://127.0.0.1:8000/inventory" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Portland Cement",
    "category": "Construction Materials",
    "unit": "bag (50kg)",
    "unit_price": 15.50,
    "quantity_available": 100
  }'
```

**Generate Quotation:**
```bash
curl -X POST "http://127.0.0.1:8000/quotations/generate" \
  -H "Content-Type: application/json" \
  -d '{
    "customer_name": "John Smith",
    "phone_number": "+1234567890",
    "address": "123 Main St",
    "project_start": "2024-12-01",
    "select_task": "Foundation Construction",
    "explaination": "Build concrete foundation for garage"
  }'
```

---

## 📖 Documentation

### Comprehensive Guides
- **`INVENTORY_API.md`** - Complete API reference with examples
- **`INVENTORY_QUICKSTART.md`** - Quick start guide and best practices
- **`IMPLEMENTATION_SUMMARY.md`** - Implementation details and features
- **`SYSTEM_ARCHITECTURE.md`** - System architecture and data flows
- **`example_tool_calling_flow.py`** - Interactive tool calling demonstration

### Interactive Documentation
Once the server is running, visit:
- **Swagger UI**: http://127.0.0.1:8000/docs
- **ReDoc**: http://127.0.0.1:8000/redoc

---

## 🛠️ Development

### Project Structure

```
Veloo-ai/
├── main.py                          # FastAPI app & API endpoints
├── quotation.py                     # AI quotation generator with tool calling
├── database.py                      # MongoDB operations (quotations + inventory)
├── schema.py                        # Pydantic data models
├── requirements.txt                 # Python dependencies
├── .env                            # Environment variables (create this)
│
├── test_inventory_api.py           # Test suite for inventory API
├── example_tool_calling_flow.py    # Tool calling demonstration
│
├── README.md                        # This file
├── INVENTORY_API.md                # Complete API reference
├── INVENTORY_QUICKSTART.md         # Quick start guide
├── IMPLEMENTATION_SUMMARY.md       # Implementation details
└── SYSTEM_ARCHITECTURE.md          # Architecture diagrams
```

### Key Files

**`main.py`**
- FastAPI application setup
- 17 API endpoints (8 quotation + 9 inventory)
- CORS middleware configuration
- Lifespan event handlers

**`quotation.py`**
- `Generator` class with OpenAI integration
- Tool calling implementation
- `get_inventory_data()` function
- AI-powered quotation generation

**`database.py`**
- `Database` class for MongoDB operations
- Quotations CRUD (9 methods)
- Inventory CRUD (10 methods)
- Search, filter, and statistics functions

**`schema.py`**
- Pydantic models for data validation
- `QuotationRequest`, `FinalQuotation`
- `InventoryItem`, `InventoryItemUpdate`
- Type-safe data structures

---

## 🚀 Deployment

### Production Considerations

1. **Environment Variables**
   - Use strong, unique values for production
   - Store secrets securely (e.g., AWS Secrets Manager)
   - Never commit `.env` to version control

2. **MongoDB**
   - Use MongoDB Atlas for production
   - Enable authentication
   - Configure IP whitelist
   - Set up backups

3. **API Security**
   - Implement authentication (JWT tokens)
   - Add rate limiting
   - Configure CORS properly
   - Use HTTPS

4. **Server**
   ```bash
   # Production server with Gunicorn
   gunicorn main:app -w 4 -k uvicorn.workers.UvicornWorker --bind 0.0.0.0:8000
   ```

---

## 🎯 Use Cases

### 1. Construction Companies
- Generate accurate quotations with real material costs
- Track inventory and material availability
- Manage multiple customer quotations
- Monitor low stock items for reordering

### 2. Service Providers
- Quickly create professional quotations
- Maintain up-to-date service pricing
- Search past quotations by customer
- Update existing quotations as needed

### 3. Retail & Wholesale
- Manage product catalog with pricing
- Generate quotes for bulk orders
- Track inventory levels
- Filter products by category

---

## 🔮 Future Enhancements

### Planned Features
- [ ] Bulk inventory import/export (CSV, Excel)
- [ ] Price history tracking and analytics
- [ ] Multi-warehouse inventory support
- [ ] Automated reorder notifications
- [ ] Customer portal for quotation viewing
- [ ] PDF quotation generation
- [ ] Email integration for quotation delivery
- [ ] Invoice generation from quotations
- [ ] User authentication and roles
- [ ] Barcode/QR code support

---

## 🤝 Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

---

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

---

## 🆘 Support & Troubleshooting

### Common Issues

**Issue: MongoDB connection failed**
```
Solution: Ensure MongoDB is running
- Check service status
- Verify connection string in .env
- Check firewall settings
```

**Issue: OpenAI API errors**
```
Solution: Verify API key
- Check .env file has valid OPENAI_API_KEY
- Ensure API key has sufficient credits
- Check API key permissions
```

**Issue: ModuleNotFoundError**
```
Solution: Install dependencies
pip install -r requirements.txt
```

**Issue: Port already in use**
```
Solution: Use different port
uvicorn main:app --port 8001
```

### Getting Help

1. Check the documentation files in the repository
2. Review error messages in terminal
3. Verify environment variables are set correctly
4. Test with the provided test scripts
5. Check MongoDB connection with mongo shell

---

## 📞 Contact

For questions, issues, or suggestions:
- Open an issue on GitHub
- Check documentation files
- Review API docs at `/docs` endpoint

---

## 🎓 Additional Resources

- [FastAPI Documentation](https://fastapi.tiangolo.com/)
- [MongoDB Documentation](https://docs.mongodb.com/)
- [OpenAI API Reference](https://platform.openai.com/docs)
- [Pydantic Documentation](https://docs.pydantic.dev/)

---

**Version**: 1.0.0  
**Last Updated**: November 19, 2025  
**Status**: ✅ Production Ready

---

## ⭐ Features Summary

✅ AI-powered quotation generation  
✅ Real-time inventory integration  
✅ Tool calling with OpenAI  
✅ Complete CRUD operations  
✅ Advanced search & filtering  
✅ Low stock monitoring  
✅ MongoDB with proper indexing  
✅ Type-safe with Pydantic  
✅ Auto-generated API docs  
✅ Comprehensive test suite  
✅ Production-ready architecture  

**Built with ❤️ using FastAPI, OpenAI, and MongoDB**```
Veloo-ai/
├── main.py              # FastAPI application
├── quotation.py         # AI quotation generator
├── database.py          # MongoDB operations
├── schema.py           # Pydantic models
├── requirements.txt    # Dependencies
├── .env.example       # Environment template
└── README.md          # Documentation
```

### Testing

You can test the API using:

1. **Swagger UI**: Visit `http://localhost:8000/docs`
2. **curl**: Command line testing
3. **Postman**: API testing tool
4. **Python requests**: Programmatic testing

Example curl command:
```bash
curl -X POST "http://localhost:8000/quotations/generate" \
  -H "Content-Type: application/json" \
  -d '{
    "customer_name": "Test Customer",
    "phone_number": "123-456-7890",
    "address": "123 Test St",
    "project_start": "2024-01-15",
    "select_task": "Bathroom Renovation",
    "explaination": "Full bathroom remodel"
  }'
```

## Production Deployment

For production deployment:

1. Use MongoDB Atlas or a properly configured MongoDB cluster
2. Set `API_RELOAD=False` in your `.env` file
3. Configure proper CORS origins
4. Use a production WSGI server like Gunicorn
5. Implement proper authentication and authorization
6. Add logging and monitoring
7. Use MongoDB connection pooling and replica sets for high availability

## License

This project is licensed under the terms specified in the LICENSE file.