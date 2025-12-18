from fastapi import FastAPI, HTTPException, Depends, Request
from fastapi.middleware.cors import CORSMiddleware
from typing import List, Optional
from datetime import datetime, date
from contextlib import asynccontextmanager
import json

from schema import (
    offerRequest, 
    Finaloffer, 
    UpdateofferRequest,
    SaveUpdatedOffer,
    UpdateStatus,
    OfferByDate,
    InventoryItem,
    InventoryItemUpdate,
    InventorySearchQuery,
    EmailRequest,
    EmailResponse,
    Email
)
from generator import Generator
from database import Database
from email_manager import EmailManager

# Initialize components
database = Database()
generator = Generator(database=database)  # Pass database instance to generator
emailManager = EmailManager(database=database)  # Pass database instance to email manager

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
    title="Offer Generator API",
    description="AI-powered offer generation service",
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

@app.post("/offers/generate")
async def generate_offer(request: offerRequest):
    """Generate a new offer using AI"""
    try:
        # Generate offer using AI
        offer = generator.generate_offer(request)
        
        # Save to database with user_id
        offer_id = database.save_offer(offer, request.user_id)
        
        # Add the ID to the response
        offer_dict = offer.dict()
        offer_dict["id"] = offer_id
        
        # Parse bill of materials into a formatted string
        bill_of_materials_string = ""
        for idx, material in enumerate(offer.bill_of_materials, 1):
            bill_of_materials_string += f"{idx}. {material.material}\n"
            bill_of_materials_string += f"   Category: {material.category}\n"
            bill_of_materials_string += f"   Quantity: {material.quantity} {material.unit}\n"
            bill_of_materials_string += f"   Price: {material.price}\n"
            bill_of_materials_string += f"   Description: {material.description}\n\n"
        
        offer_dict["bill_of_materials_string"] = bill_of_materials_string.strip()

        return offer_dict
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.put("/offers/save")
async def save_offer(request: SaveUpdatedOffer):
    """Save or update a final offer directly to the database"""
    try:
        # Extract offer_id from request
        offer_id = request.offer_id
        user_id = request.user_id
        # Validate that offer_id is not empty or placeholder
        if not offer_id or offer_id.lower() in ['string', 'null', 'undefined', '']:
            raise HTTPException(status_code=400, detail="Invalid or missing offer_id")
        
        # Create Finaloffer object from request (excluding offer_id)
        offer_data = request.dict(exclude={'offer_id'})
        offer = Finaloffer(**offer_data)
        
        # Check if offer exists
        existing_offer = database.get_offer_by_id(offer_id)
        
        if existing_offer:
            # Update existing offer
            success = database.update_offer(offer_id, offer, user_id)
            if not success:
                raise HTTPException(status_code=500, detail="Failed to update offer in database")
            message = "Offer updated successfully"
        else:
            # Save new offer with specified offer_id
            database.save_offer(offer, user_id)
            message = "Offer saved successfully"
        
        # Return the saved/updated offer with its ID
        offer_dict = offer.dict()
        offer_dict["id"] = offer_id
        
        return {
            "message": message,
            "offer_id": offer_id,
            "offer": offer_dict
        }
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# @app.get("/offers", response_model=List[dict])
# async def get_all_offers(
#     limit: Optional[int] = 100,
#     offset: Optional[int] = 0
# ):
#     """Get all offers with pagination"""
#     try:
#         offers = database.get_all_offers(limit=limit, offset=offset)
#         return offers
#     except Exception as e:
#         raise HTTPException(status_code=500, detail=str(e))

@app.get("/offers/{offer_id}")
async def get_offer(offer_id: str):
    """Get a specific offer by ID"""
    try:
        offer = database.get_offer_by_id(offer_id)
        
        if not offer:
            raise HTTPException(status_code=404, detail="offer not found")
        
        # Parse bill of materials into a formatted string
        bill_of_materials_string = ""
        for idx, material in enumerate(offer["bill_of_materials"], 1):
            bill_of_materials_string += f"{idx}. {material['material']}\n"
            bill_of_materials_string += f"   Category: {material['category']}\n"
            bill_of_materials_string += f"   Quantity: {material['quantity']} {material['unit']}\n"
            bill_of_materials_string += f"   Price: {material['price']}\n"
            bill_of_materials_string += f"   Description: {material['description']}\n\n"
        
        offer["bill_of_materials_string"] = bill_of_materials_string.strip()
        return offer
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.delete("/offers/{offer_id}")
async def delete_offer(offer_id: str): 
    """Delete a specific offer"""
    try:
        success = database.delete_offer(offer_id)
        if not success:
            raise HTTPException(status_code=404, detail="offer not found")
        return {"message": "offer deleted successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# @app.get("/offers/customer/{customer_name}")
# async def get_offers_by_customer(customer_name: str):
#     """Get all offers for a specific customer"""
#     try:
#         offers = database.get_offers_by_customer(customer_name)
#         return offers
#     except Exception as e:
#         raise HTTPException(status_code=500, detail=str(e))

@app.get("/offers/user/{user_id}")
async def get_offers_by_user(user_id: str):
    """Get all offers for a specific user"""
    try:
        offers = database.get_offers_by_user(user_id)
        return offers
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/offers-date")
async def get_offers_by_date(user_id: str, start_date: date, end_date: date):
    """Get all offers for a specific date"""
    try:
        offers = database.get_offers_by_date(user_id, start_date, end_date)
        return offers
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/offers/search/{search_term}")
async def search_offers(search_term: str, user_id: str, limit: Optional[int] = 100):
    """Search offers by text across multiple fields for a specific user"""
    try:
        offers = database.search_offers(search_term, user_id, limit)
        return offers
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# @app.get("/offers/count")
# async def get_offers_count():
#     """Get total count of offers"""
#     try:
#         count = database.get_offers_count()
#         return {"total_offers": count}
#     except Exception as e:
#         raise HTTPException(status_code=500, detail=str(e))

@app.put("/offers/update", response_model=dict)
async def update_offer(request: UpdateofferRequest):
    """Update an existing offer by ID using AI and save to database"""
    try:
        # First check if offer exists
        existing_offer = database.get_offer_by_id(request.offer_id)
        if not existing_offer:
            raise HTTPException(status_code=404, detail="offer not found")
        
        # Get user_id from existing offer
        user_id = existing_offer.get("user_id", "")
        
        # Convert the database result to Finaloffer object
        existing_final_offer = Finaloffer(
            customer_name=existing_offer.get("customer_name", ""),
            phone_number=existing_offer.get("phone_number", ""),
            address=existing_offer.get("address", ""),
            task_description=existing_offer.get("task_description", ""),
            bill_of_materials=existing_offer.get("bill_of_materials", ""),
            time=existing_offer.get("time", ""),
            resource=existing_offer.get("resource", ""),
            status=existing_offer.get("status", "Pending"),
            price=existing_offer.get("price", ""),
            project_start=existing_offer.get("project_start"),
            materials_ordered=existing_offer.get("materials_ordered", False)
        )
        
        # Use the generator's update_offer method
        updated_offer = generator.update_offer(
            user_message=request.user_message,
            update_request=existing_final_offer
        )
        
        # Save the updated offer to database with user_id
        success = database.update_offer(request.offer_id, updated_offer, user_id)
        if not success:
            raise HTTPException(status_code=500, detail="Failed to update offer in database")
        
        # Return the updated offer with ID
        result = updated_offer.dict()
        result["id"] = request.offer_id
        
        return result
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.put("/offers/toggle-status")
async def toggle_offer_status(request: UpdateStatus):
    """Toggle the status of an offer (Pending, Accepted, Done)"""
    try:
        result = database.toggle_order_status(request.offer_id, request.status)
        return {
            "message": "Status updated successfully",
            "offer_id": result["offer_id"],
            "status": result["status"]
        }
    except Exception as e:
        if "not found" in str(e).lower():
            raise HTTPException(status_code=404, detail="offer not found")
        raise HTTPException(status_code=500, detail=str(e))

@app.put("/offers/materials-ordered")
async def toggle_materials_ordered(offer_id: str):
    """Toggle the materials_ordered status of a offer"""
    try:
        result = database.toggle_materials_ordered(offer_id)
        return {
            "message": "Materials ordered status toggled successfully",
            "offer_id": result["offer_id"],
            "materials_ordered": result["materials_ordered"]
        }
    except Exception as e:
        if "not found" in str(e).lower():
            raise HTTPException(status_code=404, detail="offer not found")
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
    active: Optional[bool] = None,
    category: Optional[str] = None
):
    """Get all inventory items with optional filters and pagination"""
    try:
        items = database.get_all_inventory_items(
            limit=limit, 
            offset=offset, 
            active=active,
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
            active=search_query.active,
            limit=100
        )
        return items
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# @app.get("/inventory/category/{category}")
# async def get_inventory_by_category(category: str):
#     """Get all inventory items in a specific category"""
#     try:
#         items = database.get_inventory_by_category(category)
#         return items
#     except Exception as e:
#         raise HTTPException(status_code=500, detail=str(e))

# @app.get("/inventory/stats/count")
# async def get_inventory_count(active: Optional[bool] = None):
#     """Get total count of inventory items"""
#     try:
#         count = database.get_inventory_count(active=active)
#         return {"total_items": count}
#     except Exception as e:
#         raise HTTPException(status_code=500, detail=str(e))


# ==================== EMAIL GENERATION ENDPOINT ====================

@app.post("/email-offer", response_model=EmailResponse)
async def generate_email_for_offer(request: EmailRequest):
    """Generate email content for a customer based on offer ID"""
    try:
        # First, fetch the offer from the database
        offer = database.get_offer_by_id(request.offer_id)
        if not offer:
            raise HTTPException(status_code=404, detail="Offer not found")
        
        # Generate email content using AI
        email_response = emailManager.generate_offer_email(offer)
        
        return email_response
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    
@app.post("/email-acceptance", response_model=EmailResponse)
async def generate_email_for_acceptance(request: EmailRequest):
    """Generate email content for a customer based on offer ID"""
    try:
        # First, fetch the offer from the database
        offer = database.get_offer_by_id(request.offer_id)
        if not offer:
            raise HTTPException(status_code=404, detail="Offer not found")
        
        # Generate email content using AI
        email_response = emailManager.generate_acceptance_email(offer)
        
        return email_response
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    
@app.post("/email-custom", response_model=EmailResponse)
async def generate_email_for_acceptance(request: EmailRequest):
    """Generate email content for a customer based on offer ID"""
    try:
        # First, fetch the offer from the database
        offer = database.get_offer_by_id(request.offer_id)
        if not offer:
            raise HTTPException(status_code=404, detail="Offer not found")
        
        # Generate email content using AI
        email_response = emailManager.generate_custom_email(offer)
        
        return email_response
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/send-email", response_model=dict)
async def send_email(request: Email):
    """Send an email to the specified recipient"""
    try:
        emailManager.send_email(request)
        return {"message": "Email sent successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)   