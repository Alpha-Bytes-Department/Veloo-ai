# Veloo-ai - Quotation Generator API

An AI-powered quotation generation service built with FastAPI and OpenAI.

## Features

- 🤖 AI-powered quotation generation using OpenAI GPT
- 📄 RESTful API with comprehensive endpoints
- 💾 SQLite database for quotation storage
- 🔍 Search and filter quotations
- 📋 Customer-based quotation retrieval
- 🚀 Fast and scalable with FastAPI

## Setup

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

### 2. Environment Configuration

Copy the example environment file and configure your settings:

```bash
copy .env.example .env
```

Edit `.env` and add your OpenAI API key:

```env
OPENAI_API_KEY=your_actual_openai_api_key_here
```

### 3. Run the Application

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
  "id": 1,
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

The application uses SQLite for data persistence. The database file (`quotations.db`) will be created automatically when you first run the application.

### Table Structure

**quotations**
- `id` (INTEGER PRIMARY KEY)
- `customer_name` (TEXT)
- `phone_number` (TEXT)
- `address` (TEXT)
- `task_description` (TEXT)
- `bill_of_materials` (TEXT)
- `time` (TEXT)
- `price` (TEXT)
- `timestamp` (DATETIME)
- `created_at` (DATETIME)

## Development

### Project Structure

```
Veloo-ai/
├── main.py              # FastAPI application
├── quotation.py         # AI quotation generator
├── database.py          # Database operations
├── schema.py           # Pydantic models
├── requirements.txt    # Dependencies
├── .env.example       # Environment template
├── README.md          # Documentation
└── quotations.db      # SQLite database (created automatically)
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

1. Set `API_RELOAD=False` in your `.env` file
2. Configure proper CORS origins
3. Use a production WSGI server like Gunicorn
4. Consider using PostgreSQL instead of SQLite
5. Implement proper authentication and authorization
6. Add logging and monitoring

## License

This project is licensed under the terms specified in the LICENSE file.