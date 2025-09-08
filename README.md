# Veloo-ai - Quotation Generator API

An AI-powered quotation generation service built with FastAPI and OpenAI.

## Features

- 🤖 AI-powered quotation generation using OpenAI GPT
- 📄 RESTful API with comprehensive endpoints
- 💾 MongoDB database for quotation storage
- 🔍 Search and filter quotations
- 📋 Customer-based quotation retrieval
- 🚀 Fast and scalable with FastAPI

## Setup

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

Copy the example environment file and configure your settings:

```bash
copy .env.example .env
```

Edit `.env` and add your configuration:

```env
OPENAI_API_KEY=your_actual_openai_api_key_here
MONGODB_URI=mongodb://localhost:27017/
DATABASE_NAME=quotation_db
```

### 4. Run the Application

```bash
python main.py
```

Or using uvicorn directly:

```bash
uvicorn main:app --host 0.0.0.0 --port 8000 --reload
```

The API will be available at: `http://localhost:8000`

## API Endpoints

### Base URL: `http://localhost:8000`

### 📄 Documentation
- **GET** `/` - API information and endpoints
- **GET** `/docs` - Interactive API documentation (Swagger UI)
- **GET** `/redoc` - Alternative API documentation

### 🏥 Health Check
- **GET** `/health` - Health check endpoint

### 💼 Quotation Management

#### Generate Quotation
- **POST** `/quotations/generate`
- Creates a new AI-generated quotation

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
  "task_description": "Kitchen Renovation",
  "bill_of_materials": "AI-generated detailed materials list...",
  "time": "2024-01-15",
  "price": "AI-estimated pricing...",
  "timestamp": "2024-01-01T12:00:00"
}
```

#### Get All Quotations
- **GET** `/quotations?limit=100&offset=0`
- Retrieves all quotations with pagination

#### Get Specific Quotation
- **GET** `/quotations/{quotation_id}`
- Retrieves a quotation by ID

#### Get Quotations by Customer
- **GET** `/quotations/customer/{customer_name}`
- Retrieves all quotations for a specific customer

#### Search Quotations
- **GET** `/quotations/search/{search_term}?limit=100`
- Search quotations by text across multiple fields

#### Get Quotations Count
- **GET** `/quotations/count`
- Get total count of quotations

#### Update Quotation
- **PUT** `/quotations/{quotation_id}`
- Update an existing quotation with new AI-generated content

#### Delete Quotation
- **DELETE** `/quotations/{quotation_id}`
- Deletes a quotation by ID

## Data Models

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

### GeneratedQuotation
```python
{
  "customer_name": str,
  "phone_number": str,
  "address": str,
  "task_description": str,
  "bill_of_materials": str,
  "time": str,
  "price": str,
  "timestamp": Optional[datetime]
}
```

## Database

The application uses MongoDB for data persistence. MongoDB provides better scalability, flexibility, and performance compared to traditional relational databases.

### Database Configuration

Configure your MongoDB connection in the `.env` file:

```env
MONGODB_URI=mongodb://localhost:27017/  # For local MongoDB
# or
MONGODB_URI=mongodb+srv://username:password@cluster.mongodb.net/  # For MongoDB Atlas
DATABASE_NAME=quotation_db
```

### Collection Structure

**quotations collection**
- `_id` (ObjectId) - MongoDB's unique identifier
- `customer_name` (String)
- `phone_number` (String)
- `address` (String)
- `task_description` (String)
- `bill_of_materials` (String)
- `time` (String)
- `price` (String)
- `timestamp` (Date)
- `created_at` (Date)
- `updated_at` (Date) - Added when quotation is updated

### MongoDB Features Used

- **Flexible Schema**: Easy to add new fields without migrations
- **Indexes**: Optimized queries on customer_name, phone_number, created_at, and timestamp
- **Text Search**: Full-text search across multiple fields
- **Aggregation**: Efficient counting and data analysis

## Development

### Project Structure

```
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