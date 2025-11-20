import pymongo
from pymongo import MongoClient
from typing import List, Optional, Dict
from datetime import datetime
from bson import ObjectId
import os
from dotenv import load_dotenv
from schema import Finaloffer, InventoryItem

# Load environment variables
load_dotenv()

class Database:
    def __init__(self):
        # Get MongoDB connection string from environment variable
        self.connection_string = os.getenv("MONGODB_URI", "mongodb://localhost:27017/")
        self.database_name = os.getenv("DATABASE_NAME", "offer_db")
        self.collection_name = "offers"
        self.inventory_collection_name = "inventory"
        
        # Initialize MongoDB client
        self.client = None
        self.db = None
        self.collection = None
        self.inventory_collection = None
        
    def connect(self):
        """Establish connection to MongoDB"""
        try:
            self.client = MongoClient(self.connection_string)
            self.db = self.client[self.database_name]
            self.collection = self.db[self.collection_name]
            self.inventory_collection = self.db[self.inventory_collection_name]
            
            # Test the connection
            self.client.admin.command('ping')
            print("Successfully connected to MongoDB")
            
        except Exception as e:
            print(f"Error connecting to MongoDB: {e}")
            raise
    
    def disconnect(self):
        """Close MongoDB connection"""
        if self.client:
            self.client.close()
    
    def init_db(self):
        """Initialize the database with required indexes"""
        try:
            self.connect()
            
            # Create indexes for offers collection
            self.collection.create_index([("customer_name", 1)])
            self.collection.create_index([("phone_number", 1)])
            self.collection.create_index([("created_at", -1)])
            self.collection.create_index([("timestamp", -1)])
            
            # Create indexes for inventory collection
            self.inventory_collection.create_index([("name", 1)])
            self.inventory_collection.create_index([("category", 1)])
            self.inventory_collection.create_index([("sku", 1)], unique=True, sparse=True)
            self.inventory_collection.create_index([("is_active", 1)])
            self.inventory_collection.create_index([("created_at", -1)])
            
            print("Database initialized successfully with indexes")
            
        except Exception as e:
            print(f"Error initializing database: {e}")
            raise
    
    def save_offer(self, offer: Finaloffer) -> str:
        """Save a offer to the database"""
        try:
            if self.collection is None:
                self.connect()
            
            # Convert Pydantic model to dict
            offer_dict = offer.dict()
            
            # Add timestamps
            offer_dict["created_at"] = datetime.now()
            if not offer_dict.get("timestamp"):
                offer_dict["timestamp"] = datetime.now()
            
            # Insert into MongoDB
            result = self.collection.insert_one(offer_dict)
            return str(result.inserted_id)
            
        except Exception as e:
            raise Exception(f"Error saving offer: {e}")
    
    def get_offer_by_id(self, offer_id: str) -> Optional[Dict]:
        """Get a offer by its ID"""
        try:
            if self.collection is None:
                self.connect()
            
            # Convert string ID to ObjectId
            object_id = ObjectId(offer_id)
            
            offer = self.collection.find_one({"_id": object_id})
            
            if offer:
                # Convert ObjectId to string for JSON serialization
                offer["id"] = str(offer["_id"])
                del offer["_id"]
                return offer
            return None
            
        except Exception as e:
            raise Exception(f"Error fetching offer: {e}")
    
    def get_all_offers(self, limit: int = 100, offset: int = 0) -> List[Dict]:
        """Get all offers with pagination"""
        try:
            if self.collection is None:
                self.connect()
            
            # Use MongoDB's skip and limit for pagination
            cursor = self.collection.find().sort("created_at", -1).skip(offset).limit(limit)
            
            offers = []
            for doc in cursor:
                # Convert ObjectId to string
                doc["id"] = str(doc["_id"])
                del doc["_id"]
                offers.append(doc)
            
            return offers
            
        except Exception as e:
            raise Exception(f"Error fetching offers: {e}")
    
    def get_offers_by_customer(self, customer_name: str) -> List[Dict]:
        """Get all offers for a specific customer"""
        try:
            if self.collection is None:
                self.connect()
            
            # Use regex for case-insensitive partial matching
            query = {"customer_name": {"$regex": customer_name, "$options": "i"}}
            cursor = self.collection.find(query).sort("created_at", -1)
            
            offers = []
            for doc in cursor:
                # Convert ObjectId to string
                doc["id"] = str(doc["_id"])
                del doc["_id"]
                offers.append(doc)
            
            return offers
            
        except Exception as e:
            raise Exception(f"Error fetching customer offers: {e}")
    
    def delete_offer(self, offer_id: str) -> bool:
        """Delete a offer by ID"""
        try:
            if self.collection is None:
                self.connect()
            
            # Convert string ID to ObjectId
            object_id = ObjectId(offer_id)
            
            result = self.collection.delete_one({"_id": object_id})
            return result.deleted_count > 0
                
        except Exception as e:
            raise Exception(f"Error deleting offer: {e}")
    
    def update_offer(self, offer_id: str, offer: Finaloffer) -> bool:
        """Update an existing offer"""
        try:
            if self.collection is None:
                self.connect()
            
            # Convert string ID to ObjectId
            object_id = ObjectId(offer_id)
            
            # Convert Pydantic model to dict
            update_data = offer.dict()
            
            # Update timestamp
            update_data["timestamp"] = offer.timestamp or datetime.now()
            update_data["updated_at"] = datetime.now()
            
            result = self.collection.update_one(
                {"_id": object_id},
                {"$set": update_data}
            )
            
            return result.modified_count > 0
                
        except Exception as e:
            raise Exception(f"Error updating offer: {e}")
    
    def get_offers_count(self) -> int:
        """Get total count of offers"""
        try:
            if self.collection is None:
                self.connect()
            
            return self.collection.count_documents({})
            
        except Exception as e:
            raise Exception(f"Error counting offers: {e}")
    
    def search_offers(self, search_term: str, limit: int = 100) -> List[Dict]:
        """Search offers by text across multiple fields"""
        try:
            if self.collection is None:
                self.connect()
            
            # Create text search query
            query = {
                "$or": [
                    {"customer_name": {"$regex": search_term, "$options": "i"}},
                    {"phone_number": {"$regex": search_term, "$options": "i"}},
                    {"address": {"$regex": search_term, "$options": "i"}},
                    {"task_description": {"$regex": search_term, "$options": "i"}},
                    {"bill_of_materials": {"$regex": search_term, "$options": "i"}}
                ]
            }
            
            cursor = self.collection.find(query).sort("created_at", -1).limit(limit)
            
            offers = []
            for doc in cursor:
                # Convert ObjectId to string
                doc["id"] = str(doc["_id"])
                del doc["_id"]
                offers.append(doc)
            
            return offers
            
        except Exception as e:
            raise Exception(f"Error searching offers: {e}")
    
    def toggle_materials_ordered(self, offer_id: str) -> Dict:
        """Toggle the materials_ordered status of a offer"""
        try:
            if self.collection is None:
                self.connect()
            
            # Convert string ID to ObjectId
            object_id = ObjectId(offer_id)
            
            # Get current offer
            offer = self.collection.find_one({"_id": object_id})
            if not offer:
                raise Exception("offer not found")
            
            # Toggle the materials_ordered status
            current_status = offer.get("materials_ordered", False)
            new_status = not current_status
            
            # Update the offer
            result = self.collection.update_one(
                {"_id": object_id},
                {
                    "$set": {
                        "materials_ordered": new_status,
                        "updated_at": datetime.now()
                    }
                }
            )
            
            if result.modified_count > 0:
                return {
                    "success": True,
                    "offer_id": offer_id,
                    "materials_ordered": new_status
                }
            else:
                raise Exception("Failed to update offer")
                
        except Exception as e:
            raise Exception(f"Error toggling materials_ordered status: {e}")

    # ==================== INVENTORY MANAGEMENT METHODS ====================
    
    def create_inventory_item(self, item: InventoryItem) -> str:
        """Create a new inventory item"""
        try:
            if self.inventory_collection is None:
                self.connect()
            
            # Convert Pydantic model to dict
            item_dict = item.dict()
            
            # Add timestamps
            item_dict["created_at"] = datetime.now()
            item_dict["updated_at"] = datetime.now()
            
            # Insert into MongoDB
            result = self.inventory_collection.insert_one(item_dict)
            return str(result.inserted_id)
            
        except Exception as e:
            raise Exception(f"Error creating inventory item: {e}")
    
    def get_inventory_item_by_id(self, item_id: str) -> Optional[Dict]:
        """Get an inventory item by its ID"""
        try:
            if self.inventory_collection is None:
                self.connect()
            
            # Convert string ID to ObjectId
            object_id = ObjectId(item_id)
            
            item = self.inventory_collection.find_one({"_id": object_id})
            
            if item:
                # Convert ObjectId to string for JSON serialization
                item["id"] = str(item["_id"])
                del item["_id"]
                return item
            return None
            
        except Exception as e:
            raise Exception(f"Error fetching inventory item: {e}")
    
    def get_all_inventory_items(self, 
                                 limit: int = 100, 
                                 offset: int = 0,
                                 is_active: Optional[bool] = None,
                                 category: Optional[str] = None) -> List[Dict]:
        """Get all inventory items with optional filters and pagination"""
        try:
            if self.inventory_collection is None:
                self.connect()
            
            # Build query filter
            query = {}
            if is_active is not None:
                query["is_active"] = is_active
            if category:
                query["category"] = {"$regex": category, "$options": "i"}
            
            # Use MongoDB's skip and limit for pagination
            cursor = self.inventory_collection.find(query).sort("created_at", -1).skip(offset).limit(limit)
            
            items = []
            for doc in cursor:
                # Convert ObjectId to string
                doc["id"] = str(doc["_id"])
                del doc["_id"]
                items.append(doc)
            
            return items
            
        except Exception as e:
            raise Exception(f"Error fetching inventory items: {e}")
    
    def update_inventory_item(self, item_id: str, update_data: Dict) -> bool:
        """Update an existing inventory item"""
        try:
            if self.inventory_collection is None:
                self.connect()
            
            # Convert string ID to ObjectId
            object_id = ObjectId(item_id)
            
            # Remove None values from update data
            update_data = {k: v for k, v in update_data.items() if v is not None}
            
            # Update timestamp
            update_data["updated_at"] = datetime.now()
            
            result = self.inventory_collection.update_one(
                {"_id": object_id},
                {"$set": update_data}
            )
            
            return result.modified_count > 0
                
        except Exception as e:
            raise Exception(f"Error updating inventory item: {e}")
    
    def delete_inventory_item(self, item_id: str) -> bool:
        """Delete an inventory item by ID"""
        try:
            if self.inventory_collection is None:
                self.connect()
            
            # Convert string ID to ObjectId
            object_id = ObjectId(item_id)
            
            result = self.inventory_collection.delete_one({"_id": object_id})
            return result.deleted_count > 0
                
        except Exception as e:
            raise Exception(f"Error deleting inventory item: {e}")
    
    def search_inventory_items(self, 
                               search_term: str, 
                               category: Optional[str] = None,
                               is_active: bool = True,
                               limit: int = 100) -> List[Dict]:
        """Search inventory items by text across multiple fields"""
        try:
            if self.inventory_collection is None:
                self.connect()
            
            # Create search query
            search_conditions = [
                {"name": {"$regex": search_term, "$options": "i"}},
                {"description": {"$regex": search_term, "$options": "i"}},
                {"category": {"$regex": search_term, "$options": "i"}},
                {"supplier": {"$regex": search_term, "$options": "i"}},
                {"sku": {"$regex": search_term, "$options": "i"}}
            ]
            
            # Build query with filters
            query = {
                "$and": [
                    {"$or": search_conditions},
                    {"is_active": is_active}
                ]
            }
            
            if category:
                query["$and"].append({"category": {"$regex": category, "$options": "i"}})
            
            cursor = self.inventory_collection.find(query).sort("created_at", -1).limit(limit)
            
            items = []
            for doc in cursor:
                # Convert ObjectId to string
                doc["id"] = str(doc["_id"])
                del doc["_id"]
                items.append(doc)
            
            return items
            
        except Exception as e:
            raise Exception(f"Error searching inventory items: {e}")
    
    def get_inventory_count(self, is_active: Optional[bool] = None) -> int:
        """Get total count of inventory items"""
        try:
            if self.inventory_collection is None:
                self.connect()
            
            query = {}
            if is_active is not None:
                query["is_active"] = is_active
            
            return self.inventory_collection.count_documents(query)
            
        except Exception as e:
            raise Exception(f"Error counting inventory items: {e}")
    
    def get_inventory_by_category(self, category: str) -> List[Dict]:
        """Get all inventory items in a specific category"""
        try:
            if self.inventory_collection is None:
                self.connect()
            
            query = {
                "category": {"$regex": category, "$options": "i"},
                "is_active": True
            }
            
            cursor = self.inventory_collection.find(query).sort("name", 1)
            
            items = []
            for doc in cursor:
                # Convert ObjectId to string
                doc["id"] = str(doc["_id"])
                del doc["_id"]
                items.append(doc)
            
            return items
            
        except Exception as e:
            raise Exception(f"Error fetching inventory by category: {e}")
    
    
