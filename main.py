from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from typing import List, Optional
from datetime import datetime
from contextlib import asynccontextmanager
import json

from schema import (
    QuotationRequest, 
    FinalQuotation, 
    UpdateQuotationRequest,
    InventoryItem,
    InventoryItemUpdate,
    InventorySearchQuery
)
from quotation import Generator
from database import Database

# Initialize components
database = Database()
generator = Generator(database=database)  # Pass database instance to generator

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan handler"""
    # Startup
    database.init_db()
    yield
    # Shutdown (if needed)
    database.disconnect()

# Initialize FastAPI app
app = FastAPI(
    title="Quotation Generator API",
    description="AI-powered quotation generation service",
    version="1.0.0",
    lifespan=lifespan
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure this properly for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "timestamp": datetime.now()}

@app.post("/quotations/generate", response_model=FinalQuotation)
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

@app.post("/quotations/save", response_model=dict)
async def save_quotation(quotation: FinalQuotation):
    """Save a final quotation directly to the database"""
    try:
        # Save the quotation to database
        quotation_id = database.save_quotation(quotation)
        
        # Return the saved quotation with its ID
        quotation_dict = quotation.dict()
        quotation_dict["id"] = quotation_id
        
        return {
            "message": "Quotation saved successfully",
            "quotation_id": quotation_id,
            "quotation": quotation_dict
        }
    
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

@app.put("/quotations/update", response_model=dict)
async def update_quotation(request: UpdateQuotationRequest):
    """Update an existing quotation by ID using AI and save to database"""
    try:
        # First check if quotation exists
        existing_quotation = database.get_quotation_by_id(request.quotation_id)
        if not existing_quotation:
            raise HTTPException(status_code=404, detail="Quotation not found")
        
        # Convert the database result to FinalQuotation object
        existing_final_quotation = FinalQuotation(
            customer_name=existing_quotation.get("customer_name", ""),
            phone_number=existing_quotation.get("phone_number", ""),
            address=existing_quotation.get("address", ""),
            task_description=existing_quotation.get("task_description", ""),
            bill_of_materials=existing_quotation.get("bill_of_materials", ""),
            time=existing_quotation.get("time", ""),
            price=existing_quotation.get("price", ""),
            timestamp=existing_quotation.get("timestamp")
        )
        
        # Use the generator's update_quotation method
        updated_quotation = generator.update_quotation(
            user_message=request.user_message,
            update_request=existing_final_quotation
        )
        
        # Save the updated quotation to database
        success = database.update_quotation(request.quotation_id, updated_quotation)
        if not success:
            raise HTTPException(status_code=500, detail="Failed to update quotation in database")
        
        # Return the updated quotation with ID
        result = updated_quotation.dict()
        result["id"] = request.quotation_id
        
        return result
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ==================== INVENTORY/MATERIALS ENDPOINTS ====================

@app.post("/inventory", response_model=dict)
async def create_inventory_item(item: InventoryItem):
    """Create a new inventory/material item"""
    try:
        item_id = database.create_inventory_item(item)
        
        item_dict = item.dict()
        item_dict["id"] = item_id
        
        return {
            "message": "Inventory item created successfully",
            "item_id": item_id,
            "item": item_dict
        }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/inventory", response_model=List[dict])
async def get_all_inventory(
    limit: Optional[int] = 100,
    offset: Optional[int] = 0,
    is_active: Optional[bool] = None,
    category: Optional[str] = None
):
    """Get all inventory items with optional filters and pagination"""
    try:
        items = database.get_all_inventory_items(
            limit=limit, 
            offset=offset, 
            is_active=is_active,
            category=category
        )
        return items
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/inventory/{item_id}")
async def get_inventory_item(item_id: str):
    """Get a specific inventory item by ID"""
    try:
        item = database.get_inventory_item_by_id(item_id)
        if not item:
            raise HTTPException(status_code=404, detail="Inventory item not found")
        return item
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.put("/inventory/{item_id}", response_model=dict)
async def update_inventory_item(item_id: str, update_data: InventoryItemUpdate):
    """Update an existing inventory item"""
    try:
        # Check if item exists
        existing_item = database.get_inventory_item_by_id(item_id)
        if not existing_item:
            raise HTTPException(status_code=404, detail="Inventory item not found")
        
        # Update the item
        success = database.update_inventory_item(item_id, update_data.dict(exclude_none=True))
        
        if not success:
            raise HTTPException(status_code=500, detail="Failed to update inventory item")
        
        # Get updated item
        updated_item = database.get_inventory_item_by_id(item_id)
        
        return {
            "message": "Inventory item updated successfully",
            "item": updated_item
        }
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.delete("/inventory/{item_id}")
async def delete_inventory_item(item_id: str):
    """Delete a specific inventory item"""
    try:
        success = database.delete_inventory_item(item_id)
        if not success:
            raise HTTPException(status_code=404, detail="Inventory item not found")
        return {"message": "Inventory item deleted successfully"}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/inventory/search", response_model=List[dict])
async def search_inventory(search_query: InventorySearchQuery):
    """Search inventory items by text across multiple fields"""
    try:
        items = database.search_inventory_items(
            search_term=search_query.query,
            category=search_query.category,
            is_active=search_query.is_active,
            limit=100
        )
        return items
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/inventory/category/{category}")
async def get_inventory_by_category(category: str):
    """Get all inventory items in a specific category"""
    try:
        items = database.get_inventory_by_category(category)
        return items
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/inventory/stats/count")
async def get_inventory_count(is_active: Optional[bool] = None):
    """Get total count of inventory items"""
    try:
        count = database.get_inventory_count(is_active=is_active)
        return {"total_items": count}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/inventory/stats/low-stock")
async def get_low_stock_items():
    """Get items that are below minimum quantity threshold"""
    try:
        items = database.get_low_stock_items()
        return items
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
