import pymongo
from pymongo import MongoClient
from typing import List, Optional, Dict
from datetime import datetime
from bson import ObjectId
import os
from dotenv import load_dotenv
from schema import FinalQuotation

# Load environment variables
load_dotenv()

class Database:
    def __init__(self):
        # Get MongoDB connection string from environment variable
        self.connection_string = os.getenv("MONGODB_URI", "mongodb://localhost:27017/")
        self.database_name = os.getenv("DATABASE_NAME", "quotation_db")
        self.collection_name = "quotations"
        
        # Initialize MongoDB client
        self.client = None
        self.db = None
        self.collection = None
        
    def connect(self):
        """Establish connection to MongoDB"""
        try:
            self.client = MongoClient(self.connection_string)
            self.db = self.client[self.database_name]
            self.collection = self.db[self.collection_name]
            
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
            
            # Create indexes for better performance
            self.collection.create_index([("customer_name", 1)])
            self.collection.create_index([("phone_number", 1)])
            self.collection.create_index([("created_at", -1)])
            self.collection.create_index([("timestamp", -1)])
            
            print("Database initialized successfully with indexes")
            
        except Exception as e:
            print(f"Error initializing database: {e}")
            raise
    
    def save_quotation(self, quotation: FinalQuotation) -> str:
        """Save a quotation to the database"""
        try:
            if self.collection is None:
                self.connect()
            
            # Convert Pydantic model to dict
            quotation_dict = quotation.dict()
            
            # Add timestamps
            quotation_dict["created_at"] = datetime.now()
            if not quotation_dict.get("timestamp"):
                quotation_dict["timestamp"] = datetime.now()
            
            # Insert into MongoDB
            result = self.collection.insert_one(quotation_dict)
            return str(result.inserted_id)
            
        except Exception as e:
            raise Exception(f"Error saving quotation: {e}")
    
    def get_quotation_by_id(self, quotation_id: str) -> Optional[Dict]:
        """Get a quotation by its ID"""
        try:
            if self.collection is None:
                self.connect()
            
            # Convert string ID to ObjectId
            object_id = ObjectId(quotation_id)
            
            quotation = self.collection.find_one({"_id": object_id})
            
            if quotation:
                # Convert ObjectId to string for JSON serialization
                quotation["id"] = str(quotation["_id"])
                del quotation["_id"]
                return quotation
            return None
            
        except Exception as e:
            raise Exception(f"Error fetching quotation: {e}")
    
    def get_all_quotations(self, limit: int = 100, offset: int = 0) -> List[Dict]:
        """Get all quotations with pagination"""
        try:
            if self.collection is None:
                self.connect()
            
            # Use MongoDB's skip and limit for pagination
            cursor = self.collection.find().sort("created_at", -1).skip(offset).limit(limit)
            
            quotations = []
            for doc in cursor:
                # Convert ObjectId to string
                doc["id"] = str(doc["_id"])
                del doc["_id"]
                quotations.append(doc)
            
            return quotations
            
        except Exception as e:
            raise Exception(f"Error fetching quotations: {e}")
    
    def get_quotations_by_customer(self, customer_name: str) -> List[Dict]:
        """Get all quotations for a specific customer"""
        try:
            if self.collection is None:
                self.connect()
            
            # Use regex for case-insensitive partial matching
            query = {"customer_name": {"$regex": customer_name, "$options": "i"}}
            cursor = self.collection.find(query).sort("created_at", -1)
            
            quotations = []
            for doc in cursor:
                # Convert ObjectId to string
                doc["id"] = str(doc["_id"])
                del doc["_id"]
                quotations.append(doc)
            
            return quotations
            
        except Exception as e:
            raise Exception(f"Error fetching customer quotations: {e}")
    
    def delete_quotation(self, quotation_id: str) -> bool:
        """Delete a quotation by ID"""
        try:
            if self.collection is None:
                self.connect()
            
            # Convert string ID to ObjectId
            object_id = ObjectId(quotation_id)
            
            result = self.collection.delete_one({"_id": object_id})
            return result.deleted_count > 0
                
        except Exception as e:
            raise Exception(f"Error deleting quotation: {e}")
    
    def update_quotation(self, quotation_id: str, quotation: FinalQuotation) -> bool:
        """Update an existing quotation"""
        try:
            if self.collection is None:
                self.connect()
            
            # Convert string ID to ObjectId
            object_id = ObjectId(quotation_id)
            
            # Convert Pydantic model to dict
            update_data = quotation.dict()
            
            # Update timestamp
            update_data["timestamp"] = quotation.timestamp or datetime.now()
            update_data["updated_at"] = datetime.now()
            
            result = self.collection.update_one(
                {"_id": object_id},
                {"$set": update_data}
            )
            
            return result.modified_count > 0
                
        except Exception as e:
            raise Exception(f"Error updating quotation: {e}")
    
    def get_quotations_count(self) -> int:
        """Get total count of quotations"""
        try:
            if self.collection is None:
                self.connect()
            
            return self.collection.count_documents({})
            
        except Exception as e:
            raise Exception(f"Error counting quotations: {e}")
    
    def search_quotations(self, search_term: str, limit: int = 100) -> List[Dict]:
        """Search quotations by text across multiple fields"""
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
            
            quotations = []
            for doc in cursor:
                # Convert ObjectId to string
                doc["id"] = str(doc["_id"])
                del doc["_id"]
                quotations.append(doc)
            
            return quotations
            
        except Exception as e:
            raise Exception(f"Error searching quotations: {e}")
