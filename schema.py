from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import datetime

class PriceDetail(BaseModel):
    Materials: float
    Labor: float
    Total: float
    
class QuotationRequest(BaseModel):
    customer_name: str
    phone_number: str
    address: str
    project_start: str
    select_task: str
    explaination: str
    timestamp: Optional[datetime] = None

class FinalQuotation(BaseModel):
    customer_name: str
    phone_number: str
    address: str
    task_description: str 
    bill_of_materials: List[str]
    time: str 
    price: PriceDetail
    timestamp: Optional[datetime] = None

class UpdateQuotationRequest(BaseModel):
    quotation_id: str
    user_message: str

# Inventory/Materials Schemas
class InventoryItem(BaseModel):
    name: str = Field(..., description="Name of the material/item")
    category: str = Field(..., description="Category (e.g., lumber, cement, tools, etc.)")
    description: Optional[str] = Field(None, description="Detailed description of the item")
    unit: str = Field(..., description="Unit of measurement (e.g., kg, m, pieces, etc.)")
    unit_price: float = Field(..., description="Price per unit")
    quantity_available: float = Field(default=0, description="Current quantity in stock")
    minimum_quantity: Optional[float] = Field(None, description="Minimum stock level for reorder")
    supplier: Optional[str] = Field(None, description="Supplier name")
    supplier_contact: Optional[str] = Field(None, description="Supplier contact information")
    sku: Optional[str] = Field(None, description="Stock Keeping Unit code")
    is_active: bool = Field(default=True, description="Whether item is actively available")
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

class InventoryItemUpdate(BaseModel):
    name: Optional[str] = None
    category: Optional[str] = None
    description: Optional[str] = None
    unit: Optional[str] = None
    unit_price: Optional[float] = None
    quantity_available: Optional[float] = None
    minimum_quantity: Optional[float] = None
    supplier: Optional[str] = None
    supplier_contact: Optional[str] = None
    sku: Optional[str] = None
    is_active: Optional[bool] = None

class InventorySearchQuery(BaseModel):
    query: str = Field(..., description="Search query for inventory items")
    category: Optional[str] = Field(None, description="Filter by category")
    is_active: Optional[bool] = Field(True, description="Filter by active status")
