from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime

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
    bill_of_materials: str
    time: str 
    price: str
    timestamp: Optional[datetime] = None

class UpdateQuotationRequest(BaseModel):
    quotation_id: str
    user_message: str
