from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from typing import List, Optional
from datetime import datetime
import json

from schema import QuotationRequest, GeneratedQuotation
from quotation import Generator
from database import Database

# Initialize FastAPI app
app = FastAPI(
    title="Quotation Generator API",
    description="AI-powered quotation generation service",
    version="1.0.0"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure this properly for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize components
generator = Generator()
database = Database()

@app.on_event("startup")
async def startup_event():
    """Initialize database on startup"""
    database.init_db()

@app.get("/")
async def root():
    """Root endpoint with API information"""
    return {
        "message": "Quotation Generator API",
        "version": "1.0.0",
        "database": "MongoDB",
        "endpoints": {
            "generate_quotation": "/quotations/generate",
            "get_quotations": "/quotations",
            "get_quotation": "/quotations/{quotation_id}",
            "update_quotation": "/quotations/{quotation_id}",
            "delete_quotation": "/quotations/{quotation_id}",
            "get_customer_quotations": "/quotations/customer/{customer_name}",
            "search_quotations": "/quotations/search/{search_term}",
            "quotations_count": "/quotations/count",
            "health": "/health"
        }
    }

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "timestamp": datetime.now()}

@app.post("/quotations/generate", response_model=GeneratedQuotation)
async def generate_quotation(request: QuotationRequest):
    """Generate a new quotation using AI"""
    try:
        # Generate quotation using AI
        quotation = generator.generate_quotation(request)
        
        # Save to database
        quotation_id = database.save_quotation(quotation)
        
        # Add the ID to the response
        quotation_dict = quotation.dict()
        quotation_dict["id"] = quotation_id
        
        return quotation_dict
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/quotations", response_model=List[dict])
async def get_all_quotations(
    limit: Optional[int] = 100,
    offset: Optional[int] = 0
):
    """Get all quotations with pagination"""
    try:
        quotations = database.get_all_quotations(limit=limit, offset=offset)
        return quotations
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/quotations/{quotation_id}")
async def get_quotation(quotation_id: str):
    """Get a specific quotation by ID"""
    try:
        quotation = database.get_quotation_by_id(quotation_id)
        if not quotation:
            raise HTTPException(status_code=404, detail="Quotation not found")
        return quotation
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.delete("/quotations/{quotation_id}")
async def delete_quotation(quotation_id: str):
    """Delete a specific quotation"""
    try:
        success = database.delete_quotation(quotation_id)
        if not success:
            raise HTTPException(status_code=404, detail="Quotation not found")
        return {"message": "Quotation deleted successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/quotations/customer/{customer_name}")
async def get_quotations_by_customer(customer_name: str):
    """Get all quotations for a specific customer"""
    try:
        quotations = database.get_quotations_by_customer(customer_name)
        return quotations
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/quotations/search/{search_term}")
async def search_quotations(search_term: str, limit: Optional[int] = 100):
    """Search quotations by text across multiple fields"""
    try:
        quotations = database.search_quotations(search_term, limit)
        return quotations
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/quotations/count")
async def get_quotations_count():
    """Get total count of quotations"""
    try:
        count = database.get_quotations_count()
        return {"total_quotations": count}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.put("/quotations/{quotation_id}")
async def update_quotation(quotation_id: str, request: QuotationRequest):
    """Update an existing quotation"""
    try:
        # Generate new quotation data from request
        quotation = generator.generate_quotation(request)
        
        # Update the quotation in database
        success = database.update_quotation(quotation_id, quotation)
        if not success:
            raise HTTPException(status_code=404, detail="Quotation not found")
        
        # Return updated quotation
        updated_quotation = database.get_quotation_by_id(quotation_id)
        return updated_quotation
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="127.0.0.1", port=8000, reload=True)
