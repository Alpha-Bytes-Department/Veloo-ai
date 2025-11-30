from pydantic import BaseModel, Field
from typing import List, Optional, Literal
from datetime import datetime, date

class PriceDetail(BaseModel):
    Materials: float
    Labor: float
    Total: float
    
class offerRequest(BaseModel):
    customer_name: str
    phone_number: str
    address: str
    project_start: date
    select_task: str
    explaination: str
    user_id: str

class Materials(BaseModel):
    category: str
    material: str 	
    price: str	
    description: str
    unit: str	
    quantity: str

class Finaloffer(BaseModel):
    customer_name: str
    phone_number: str
    address: str
    task_description: str 
    bill_of_materials: List[Materials]
    time: str
    resource: str  # Name of the available worker assigned to the task
    status: Literal["Pending", "Accepted", "Done"] = "Pending" 
    price: PriceDetail
    project_start: date
    materials_ordered: bool = False  # Default to False if not specified

class UpdateofferRequest(BaseModel):
    offer_id: str
    user_message: str

class UpdateStatus(BaseModel):
    offer_id: str
    status: Literal["Pending", "Accepted", "Done"]

class SaveUpdatedOffer(Finaloffer):
    offer_id: str
    user_id: str

class OfferByDate(BaseModel):
    user_id: str
    start_date: date
    end_date: date

# Inventory/Materials Schemas
class InventoryItem(BaseModel):
    id: Optional[str] = Field(None, description="Primary key (UUID or INT)")
    name: str = Field(..., description="Product name")
    category: str = Field(..., description="Category for filtering")
    description: Optional[str] = Field(None, description="Optional (useful if using vector DB)")
    brand: Optional[str] = Field(None, description="Product brand")
    default_price: float = Field(..., description="Base price before variant adjustment")
    active: bool = Field(default=True, description="Whether the item is available")
    created_at: Optional[datetime] = Field(None, description="Metadata - creation timestamp")
    updated_at: Optional[datetime] = Field(None, description="Metadata - last update timestamp")

class InventoryItemUpdate(BaseModel):
    name: Optional[str] = None
    category: Optional[str] = None
    description: Optional[str] = None
    brand: Optional[str] = None
    default_price: Optional[float] = None
    active: Optional[bool] = None

class InventorySearchQuery(BaseModel):
    query: str = Field(..., description="Search query for inventory items")
    category: Optional[str] = Field(None, description="Filter by category")
    active: Optional[bool] = Field(True, description="Filter by active status")

class EmailRequest(BaseModel):
    offer_id: str = Field(..., description="ID of the offer to generate email for")

class EmailResponse(BaseModel):
    customer_name: str = Field(..., description="Name of the customer")
    email_subject: str = Field(..., description="Email subject line")
    email_body: str = Field(..., description="Email body content")

class Email(BaseModel):
    to: str = Field(..., description="Recipient email address")
    subject: str = Field(..., description="Email subject line")
    body: str = Field(..., description="Email body content")


