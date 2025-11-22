import psycopg2
from psycopg2.extras import RealDictCursor, Json
from typing import List, Optional, Dict
from datetime import datetime
import os
from dotenv import load_dotenv
from schema import Finaloffer, InventoryItem
import json

# Load environment variables
load_dotenv()

class Database:
    def __init__(self):
        # Get PostgreSQL connection string from environment variable
        self.connection_string = os.getenv("DATABASE_URL")
        self.conn = None
        self.cursor = None
        
    def connect(self):
        """Establish connection to PostgreSQL"""
        try:
            self.conn = psycopg2.connect(self.connection_string)
            self.cursor = self.conn.cursor(cursor_factory=RealDictCursor)
            print("Successfully connected to PostgreSQL")
            
        except Exception as e:
            print(f"Error connecting to PostgreSQL: {e}")
            raise
    
    def disconnect(self):
        """Close PostgreSQL connection"""
        if self.cursor:
            self.cursor.close()
        if self.conn:
            self.conn.close()
    
    def init_db(self):
        """Initialize the database with required tables"""
        try:
            self.connect()
            
            # Enable UUID extension
            self.cursor.execute("""
                CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
            """)
            
            # Create offers table
            self.cursor.execute("""
                CREATE TABLE IF NOT EXISTS offers (
                    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
                    customer_name TEXT NOT NULL,
                    phone_number TEXT NOT NULL,
                    address TEXT NOT NULL,
                    task_description TEXT,
                    bill_of_materials JSONB,
                    time TEXT,
                    price JSONB,
                    user_id TEXT NOT NULL,
                    timestamp TIMESTAMP,
                    materials_ordered BOOLEAN DEFAULT FALSE,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # Create indexes for offers
            self.cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_offers_customer_name ON offers(customer_name);
            """)
            self.cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_offers_phone_number ON offers(phone_number);
            """)
            self.cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_offers_user_id ON offers(user_id);
            """)
            self.cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_offers_created_at ON offers(created_at DESC);
            """)
            
            # Create inventory table
            self.cursor.execute("""
                CREATE TABLE IF NOT EXISTS inventory (
                    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
                    name TEXT NOT NULL,
                    category TEXT NOT NULL,
                    description TEXT,
                    brand TEXT,
                    default_price DECIMAL(10, 2) NOT NULL,
                    active BOOLEAN DEFAULT TRUE,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # Create indexes for inventory
            self.cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_inventory_name ON inventory(name);
            """)
            self.cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_inventory_category ON inventory(category);
            """)
            self.cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_inventory_brand ON inventory(brand);
            """)
            self.cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_inventory_active ON inventory(active);
            """)
            self.cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_inventory_created_at ON inventory(created_at DESC);
            """)
            
            self.conn.commit()
            print("Database initialized successfully with tables and indexes")
            
        except Exception as e:
            if self.conn:
                self.conn.rollback()
            print(f"Error initializing database: {e}")
            raise
    
    def save_offer(self, offer: Finaloffer) -> str:
        """Save an offer to the database"""
        try:
            if self.conn is None:
                self.connect()
            
            # Convert Pydantic model to dict
            offer_dict = offer.dict()
            
            # Add timestamps
            created_at = datetime.now()
            timestamp = offer_dict.get("timestamp") or datetime.now()
            
            self.cursor.execute("""
                INSERT INTO offers (
                    customer_name, phone_number, address, task_description,
                    bill_of_materials, time, price, user_id, timestamp, materials_ordered, created_at
                )
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                RETURNING id
            """, (
                offer_dict["customer_name"],
                offer_dict["phone_number"],
                offer_dict["address"],
                offer_dict["task_description"],
                Json(offer_dict["bill_of_materials"]),
                offer_dict["time"],
                Json(offer_dict["price"]),
                offer_dict["user_id"],
                timestamp,
                offer_dict.get("materials_ordered", False),
                created_at
            ))
            
            offer_id = self.cursor.fetchone()["id"]
            self.conn.commit()
            return str(offer_id)
            
        except Exception as e:
            if self.conn:
                self.conn.rollback()
            raise Exception(f"Error saving offer: {e}")
    
    def get_offer_by_id(self, offer_id: str) -> Optional[Dict]:
        """Get an offer by its ID"""
        try:
            if self.conn is None:
                self.connect()
            
            self.cursor.execute("""
                SELECT * FROM offers WHERE id = %s
            """, (offer_id,))
            
            offer = self.cursor.fetchone()
            
            if offer:
                return dict(offer)
            return None
            
        except Exception as e:
            raise Exception(f"Error fetching offer: {e}")
    
    def get_all_offers(self, limit: int = 100, offset: int = 0) -> List[Dict]:
        """Get all offers with pagination"""
        try:
            if self.conn is None:
                self.connect()
            
            self.cursor.execute("""
                SELECT * FROM offers 
                ORDER BY created_at DESC 
                LIMIT %s OFFSET %s
            """, (limit, offset))
            
            offers = self.cursor.fetchall()
            return [dict(offer) for offer in offers]
            
        except Exception as e:
            raise Exception(f"Error fetching offers: {e}")
    
    def get_offers_by_customer(self, customer_name: str) -> List[Dict]:
        """Get all offers for a specific customer"""
        try:
            if self.conn is None:
                self.connect()
            
            self.cursor.execute("""
                SELECT * FROM offers 
                WHERE customer_name ILIKE %s 
                ORDER BY created_at DESC
            """, (f"%{customer_name}%",))
            
            offers = self.cursor.fetchall()
            return [dict(offer) for offer in offers]
            
        except Exception as e:
            raise Exception(f"Error fetching customer offers: {e}")
    
    def get_offers_by_user(self, user_id: str) -> List[Dict]:
        """Get all offers for a specific user"""
        try:
            if self.conn is None:
                self.connect()
            
            self.cursor.execute("""
                SELECT * FROM offers 
                WHERE user_id = %s 
                ORDER BY created_at DESC
            """, (user_id,))
            
            offers = self.cursor.fetchall()
            return [dict(offer) for offer in offers]
            
        except Exception as e:
            raise Exception(f"Error fetching user offers: {e}")
    
    def delete_offer(self, offer_id: str) -> bool:
        """Delete an offer by ID"""
        try:
            if self.conn is None:
                self.connect()
            
            self.cursor.execute("""
                DELETE FROM offers WHERE id = %s
            """, (offer_id,))
            
            deleted = self.cursor.rowcount > 0
            self.conn.commit()
            return deleted
                
        except Exception as e:
            if self.conn:
                self.conn.rollback()
            raise Exception(f"Error deleting offer: {e}")
    
    def update_offer(self, offer_id: str, offer: Finaloffer) -> bool:
        """Update an existing offer"""
        try:
            if self.conn is None:
                self.connect()
            
            # Convert Pydantic model to dict
            update_data = offer.dict()
            
            timestamp = update_data.get("timestamp") or datetime.now()
            updated_at = datetime.now()
            
            self.cursor.execute("""
                UPDATE offers SET
                    customer_name = %s,
                    phone_number = %s,
                    address = %s,
                    task_description = %s,
                    bill_of_materials = %s,
                    time = %s,
                    price = %s,
                    user_id = %s,
                    timestamp = %s,
                    materials_ordered = %s,
                    updated_at = %s
                WHERE id = %s
            """, (
                update_data["customer_name"],
                update_data["phone_number"],
                update_data["address"],
                update_data["task_description"],
                Json(update_data["bill_of_materials"]),
                update_data["time"],
                Json(update_data["price"]),
                update_data["user_id"],
                timestamp,
                update_data.get("materials_ordered", False),
                updated_at,
                offer_id
            ))
            
            modified = self.cursor.rowcount > 0
            self.conn.commit()
            return modified
                
        except Exception as e:
            if self.conn:
                self.conn.rollback()
            raise Exception(f"Error updating offer: {e}")
    
    def get_offers_count(self) -> int:
        """Get total count of offers"""
        try:
            if self.conn is None:
                self.connect()
            
            self.cursor.execute("SELECT COUNT(*) as count FROM offers")
            result = self.cursor.fetchone()
            return result["count"]
            
        except Exception as e:
            raise Exception(f"Error counting offers: {e}")
    
    def search_offers(self, search_term: str, limit: int = 100) -> List[Dict]:
        """Search offers by text across multiple fields"""
        try:
            if self.conn is None:
                self.connect()
            
            search_pattern = f"%{search_term}%"
            
            self.cursor.execute("""
                SELECT * FROM offers 
                WHERE customer_name ILIKE %s 
                   OR phone_number ILIKE %s 
                   OR address ILIKE %s 
                   OR task_description ILIKE %s
                ORDER BY created_at DESC 
                LIMIT %s
            """, (search_pattern, search_pattern, search_pattern, search_pattern, limit))
            
            offers = self.cursor.fetchall()
            return [dict(offer) for offer in offers]
            
        except Exception as e:
            raise Exception(f"Error searching offers: {e}")
    
    def toggle_materials_ordered(self, offer_id: str) -> Dict:
        """Toggle the materials_ordered status of an offer"""
        try:
            if self.conn is None:
                self.connect()
            
            # Get current offer
            self.cursor.execute("""
                SELECT materials_ordered FROM offers WHERE id = %s
            """, (offer_id,))
            
            offer = self.cursor.fetchone()
            if not offer:
                raise Exception("offer not found")
            
            # Toggle the materials_ordered status
            current_status = offer["materials_ordered"]
            new_status = not current_status
            
            # Update the offer
            self.cursor.execute("""
                UPDATE offers SET 
                    materials_ordered = %s,
                    updated_at = %s
                WHERE id = %s
            """, (new_status, datetime.now(), offer_id))
            
            self.conn.commit()
            
            return {
                "success": True,
                "offer_id": offer_id,
                "materials_ordered": new_status
            }
                
        except Exception as e:
            if self.conn:
                self.conn.rollback()
            raise Exception(f"Error toggling materials_ordered status: {e}")

    # ==================== INVENTORY MANAGEMENT METHODS ====================
    
    def create_inventory_item(self, item: InventoryItem) -> str:
        """Create a new inventory item"""
        try:
            if self.conn is None:
                self.connect()
            
            # Convert Pydantic model to dict
            item_dict = item.dict(exclude={'id'})
            
            self.cursor.execute("""
                INSERT INTO inventory (
                    name, category, description, brand, default_price, active, created_at, updated_at
                )
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                RETURNING id
            """, (
                item_dict["name"],
                item_dict["category"],
                item_dict.get("description"),
                item_dict.get("brand"),
                item_dict["default_price"],
                item_dict.get("active", True),
                datetime.now(),
                datetime.now()
            ))
            
            item_id = self.cursor.fetchone()["id"]
            self.conn.commit()
            return str(item_id)
            
        except Exception as e:
            if self.conn:
                self.conn.rollback()
            raise Exception(f"Error creating inventory item: {e}")
    
    def get_inventory_item_by_id(self, item_id: str) -> Optional[Dict]:
        """Get an inventory item by its ID"""
        try:
            if self.conn is None:
                self.connect()
            
            self.cursor.execute("""
                SELECT * FROM inventory WHERE id = %s
            """, (item_id,))
            
            item = self.cursor.fetchone()
            
            if item:
                return dict(item)
            return None
            
        except Exception as e:
            raise Exception(f"Error fetching inventory item: {e}")
    
    def get_all_inventory_items(self, 
                                 limit: int = 100, 
                                 offset: int = 0,
                                 active: Optional[bool] = None,
                                 category: Optional[str] = None) -> List[Dict]:
        """Get all inventory items with optional filters and pagination"""
        try:
            if self.conn is None:
                self.connect()
            
            # Build query with filters
            conditions = []
            params = []
            
            if active is not None:
                conditions.append("active = %s")
                params.append(active)
            
            if category:
                conditions.append("category ILIKE %s")
                params.append(f"%{category}%")
            
            where_clause = "WHERE " + " AND ".join(conditions) if conditions else ""
            
            params.extend([limit, offset])
            
            self.cursor.execute(f"""
                SELECT * FROM inventory 
                {where_clause}
                ORDER BY created_at DESC 
                LIMIT %s OFFSET %s
            """, params)
            
            items = self.cursor.fetchall()
            return [dict(item) for item in items]
            
        except Exception as e:
            raise Exception(f"Error fetching inventory items: {e}")
    
    def update_inventory_item(self, item_id: str, update_data: Dict) -> bool:
        """Update an existing inventory item"""
        try:
            if self.conn is None:
                self.connect()
            
            # Remove None values from update data
            update_data = {k: v for k, v in update_data.items() if v is not None}
            
            if not update_data:
                return False
            
            # Build SET clause dynamically
            set_clauses = []
            params = []
            
            for key, value in update_data.items():
                set_clauses.append(f"{key} = %s")
                params.append(value)
            
            # Add updated_at
            set_clauses.append("updated_at = %s")
            params.append(datetime.now())
            
            # Add item_id as last parameter
            params.append(item_id)
            
            query = f"""
                UPDATE inventory SET {', '.join(set_clauses)}
                WHERE id = %s
            """
            
            self.cursor.execute(query, params)
            
            modified = self.cursor.rowcount > 0
            self.conn.commit()
            return modified
                
        except Exception as e:
            if self.conn:
                self.conn.rollback()
            raise Exception(f"Error updating inventory item: {e}")
    
    def delete_inventory_item(self, item_id: str) -> bool:
        """Delete an inventory item by ID"""
        try:
            if self.conn is None:
                self.connect()
            
            self.cursor.execute("""
                DELETE FROM inventory WHERE id = %s
            """, (item_id,))
            
            deleted = self.cursor.rowcount > 0
            self.conn.commit()
            return deleted
                
        except Exception as e:
            if self.conn:
                self.conn.rollback()
            raise Exception(f"Error deleting inventory item: {e}")
    
    def search_inventory_items(self, 
                               search_term: str, 
                               category: Optional[str] = None,
                               active: bool = True,
                               limit: int = 100) -> List[Dict]:
        """Search inventory items by text across multiple fields"""
        try:
            if self.conn is None:
                self.connect()
            
            search_pattern = f"%{search_term}%"
            
            # Build query with filters
            conditions = [
                "(name ILIKE %s OR description ILIKE %s OR category ILIKE %s OR brand ILIKE %s)"
            ]
            params = [search_pattern, search_pattern, search_pattern, search_pattern]
            
            conditions.append("active = %s")
            params.append(active)
            
            if category:
                conditions.append("category ILIKE %s")
                params.append(f"%{category}%")
            
            params.append(limit)
            
            where_clause = " AND ".join(conditions)
            
            self.cursor.execute(f"""
                SELECT * FROM inventory 
                WHERE {where_clause}
                ORDER BY created_at DESC 
                LIMIT %s
            """, params)
            
            items = self.cursor.fetchall()
            return [dict(item) for item in items]
            
        except Exception as e:
            raise Exception(f"Error searching inventory items: {e}")
    
    def get_inventory_count(self, active: Optional[bool] = None) -> int:
        """Get total count of inventory items"""
        try:
            if self.conn is None:
                self.connect()
            
            if active is not None:
                self.cursor.execute("""
                    SELECT COUNT(*) as count FROM inventory WHERE active = %s
                """, (active,))
            else:
                self.cursor.execute("SELECT COUNT(*) as count FROM inventory")
            
            result = self.cursor.fetchone()
            return result["count"]
            
        except Exception as e:
            raise Exception(f"Error counting inventory items: {e}")
    
    def get_inventory_by_category(self, category: str) -> List[Dict]:
        """Get all inventory items in a specific category"""
        try:
            if self.conn is None:
                self.connect()
            
            self.cursor.execute("""
                SELECT * FROM inventory 
                WHERE category ILIKE %s AND active = TRUE
                ORDER BY name ASC
            """, (f"%{category}%",))
            
            items = self.cursor.fetchall()
            return [dict(item) for item in items]
            
        except Exception as e:
            raise Exception(f"Error fetching inventory by category: {e}")


