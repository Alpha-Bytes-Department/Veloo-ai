import psycopg2
from psycopg2.extras import RealDictCursor, Json
from typing import List, Optional, Dict
from datetime import datetime, date
import os
from dotenv import load_dotenv
from app.schema import Finaloffer, InventoryItem
import json

# Load environment variables
load_dotenv()

class Database:
    def __init__(self):
        # Get PostgreSQL connection string from environment variable
        self.connection_string = os.getenv("DATABASE_URL")
        self.conn = None
        
    def connect(self):
        """Establish connection to PostgreSQL"""
        try:
            if self.conn is None or self.conn.closed:
                self.conn = psycopg2.connect(self.connection_string)
                self.conn.autocommit = True
                print("Successfully connected to PostgreSQL")
            
        except Exception as e:
            print(f"Error connecting to PostgreSQL: {e}")
            raise
    
    def disconnect(self):
        """Close PostgreSQL connection"""
        if self.conn and not self.conn.closed:
            self.conn.close()
    
    def get_cursor(self):
        """Get a new cursor with proper connection checking"""
        if self.conn is None or self.conn.closed:
            self.connect()
        return self.conn.cursor(cursor_factory=RealDictCursor)
    
    def init_db(self):
        """Initialize the database with required tables"""
        cursor = None
        try:
            self.connect()
            cursor = self.get_cursor()
            
            # Enable UUID extension
            cursor.execute("""
                CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
            """)
            
            # Create offers table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS offers (
                    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
                    customer_name TEXT NOT NULL,
                    phone_number TEXT NOT NULL,
                    address TEXT NOT NULL,
                    customer_email TEXT,
                    task_description TEXT,
                    bill_of_materials JSONB,
                    time TEXT,
                    resource TEXT,
                    status TEXT DEFAULT 'Pending',
                    price JSONB,
                    user_id TEXT NOT NULL,
                    project_start DATE,
                    materials_ordered BOOLEAN DEFAULT FALSE,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # Create indexes for offers
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_offers_customer_name ON offers(customer_name);
            """)
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_offers_phone_number ON offers(phone_number);
            """)
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_offers_user_id ON offers(user_id);
            """)
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_offers_created_at ON offers(created_at DESC);
            """)
            
            # Create inventory table
            cursor.execute("""
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
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_inventory_name ON inventory(name);
            """)
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_inventory_category ON inventory(category);
            """)
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_inventory_brand ON inventory(brand);
            """)
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_inventory_active ON inventory(active);
            """)
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_inventory_created_at ON inventory(created_at DESC);
            """)
            
            self.conn.commit()
            print("Database initialized successfully with tables and indexes")
            
        except Exception as e:
            if self.conn:
                self.conn.rollback()
            print(f"Error initializing database: {e}")
            raise
        finally:
            if cursor:
                cursor.close()
    
    def save_offer(self, offer: Finaloffer, user_id: str) -> str:
        """Save an offer to the database"""
        cursor = None
        try:
            self.connect()
            cursor = self.get_cursor()
            
            # Convert Pydantic model to dict
            offer_dict = offer.dict()
            
            # Add timestamps
            created_at = datetime.now()
            project_start = offer_dict.get("project_start")
            
            cursor.execute("""
                INSERT INTO offers (
                    customer_name, phone_number, address, customer_email, task_description,
                    bill_of_materials, time, resource, status, price, user_id, project_start, materials_ordered, created_at
                )
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                RETURNING id
            """, (
                offer_dict["customer_name"],
                offer_dict["phone_number"],
                offer_dict["address"],
                offer_dict.get("customer_email", ""),
                offer_dict["task_description"],
                Json(offer_dict["bill_of_materials"]),
                offer_dict["time"],
                offer_dict.get("resource", ""),
                offer_dict.get("status", "Pending"),
                Json(offer_dict["price"]),
                user_id,
                project_start,
                offer_dict.get("materials_ordered", False),
                created_at
            ))
            
            offer_id = cursor.fetchone()["id"]
            self.conn.commit()
            return str(offer_id)
            
        except Exception as e:
            if self.conn:
                self.conn.rollback()
            raise Exception(f"Error saving offer: {e}")
        finally:
            if cursor:
                cursor.close()
    
    def get_offer_by_id(self, offer_id: str) -> Optional[Dict]:
        """Get an offer by its ID"""
        cursor = None
        try:
            self.connect()
            cursor = self.get_cursor()
            
            cursor.execute("""
                SELECT * FROM offers WHERE id = %s
            """, (offer_id,))
            
            offer = cursor.fetchone()
            
            if offer:
                return dict(offer)
            return None
            
        except Exception as e:
            raise Exception(f"Error fetching offer: {e}")
        finally:
            if cursor:
                cursor.close()
    
    def get_all_offers(self, limit: int = 100, offset: int = 0) -> List[Dict]:
        """Get all offers with pagination"""
        cursor = None
        try:
            self.connect()
            cursor = self.get_cursor()
            
            cursor.execute("""
                SELECT * FROM offers 
                ORDER BY created_at DESC 
                LIMIT %s OFFSET %s
            """, (limit, offset))
            
            offers = cursor.fetchall()
            return [dict(offer) for offer in offers]
            
        except Exception as e:
            raise Exception(f"Error fetching offers: {e}")
        finally:
            if cursor:
                cursor.close()
    
    def get_offers_by_customer(self, customer_name: str) -> List[Dict]:
        """Get all offers for a specific customer"""
        cursor = None
        try:
            self.connect()
            cursor = self.get_cursor()
            
            cursor.execute("""
                SELECT * FROM offers 
                WHERE customer_name ILIKE %s 
                ORDER BY created_at DESC
            """, (f"%{customer_name}%",))
            
            offers = cursor.fetchall()
            return [dict(offer) for offer in offers]
            
        except Exception as e:
            raise Exception(f"Error fetching customer offers: {e}")
        finally:
            if cursor:
                cursor.close()
    
    def get_offers_by_user(self, user_id: str, month: int = None, year: int = None) -> List[Dict]:
        """Get all offers for a specific user, optionally filtered by month and year"""
        cursor = None
        try:
            self.connect()
            cursor = self.get_cursor()
            
            # Build query with optional month/year filters
            query = "SELECT * FROM offers WHERE user_id = %s"
            params = [user_id]
            
            if year is not None:
                query += " AND EXTRACT(YEAR FROM created_at) = %s"
                params.append(year)
            
            if month is not None:
                query += " AND EXTRACT(MONTH FROM created_at) = %s"
                params.append(month)
            
            query += " ORDER BY created_at DESC"
            
            cursor.execute(query, tuple(params))
            
            offers = cursor.fetchall()
            return [dict(offer) for offer in offers]
            
        except Exception as e:
            raise Exception(f"Error fetching user offers: {e}")
        finally:
            if cursor:
                cursor.close()
    
    def get_offers_by_date(self, user_id: str, start_date: date, end_date: date) -> List[Dict]:
        """Get all offers for a specific user within a date range based on project_start"""
        cursor = None
        try:
            self.connect()
            cursor = self.get_cursor()
            
            cursor.execute("""
                SELECT * FROM offers 
                WHERE user_id = %s 
                AND project_start BETWEEN %s AND %s
                ORDER BY project_start DESC
            """, (user_id, start_date, end_date))
            
            offers = cursor.fetchall()
            return [dict(offer) for offer in offers]
            
        except Exception as e:
            raise Exception(f"Error fetching offers by date: {e}")
        finally:
            if cursor:
                cursor.close()
    
    def delete_offer(self, offer_id: str) -> bool:
        """Delete an offer by ID"""
        cursor = None
        try:
            self.connect()
            cursor = self.get_cursor()
            
            cursor.execute("""
                DELETE FROM offers WHERE id = %s
            """, (offer_id,))
            
            deleted = cursor.rowcount > 0
            self.conn.commit()
            return deleted
                
        except Exception as e:
            if self.conn:
                self.conn.rollback()
            raise Exception(f"Error deleting offer: {e}")
        finally:
            if cursor:
                cursor.close()
    
    def update_offer(self, offer_id: str, offer: Finaloffer, user_id: str) -> bool:
        """Update an existing offer"""
        cursor = None
        try:
            self.connect()
            cursor = self.get_cursor()
            
            # Convert Pydantic model to dict
            update_data = offer.dict()
            
            project_start = update_data.get("project_start")
            updated_at = datetime.now()
            
            cursor.execute("""
                UPDATE offers SET
                    customer_name = %s,
                    phone_number = %s,
                    address = %s,
                    customer_email = %s,
                    task_description = %s,
                    bill_of_materials = %s,
                    time = %s,
                    resource = %s,
                    status = %s,
                    price = %s,
                    user_id = %s,
                    project_start = %s,
                    materials_ordered = %s,
                    updated_at = %s
                WHERE id = %s
            """, (
                update_data["customer_name"],
                update_data["phone_number"],
                update_data["address"],
                update_data.get("customer_email", ""),
                update_data["task_description"],
                Json(update_data["bill_of_materials"]),
                update_data["time"],
                update_data.get("resource", ""),
                update_data.get("status", "Pending"),
                Json(update_data["price"]),
                user_id,
                project_start,
                update_data.get("materials_ordered", False),
                updated_at,
                offer_id
            ))
            
            modified = cursor.rowcount > 0
            self.conn.commit()
            return modified
                
        except Exception as e:
            if self.conn:
                self.conn.rollback()
            raise Exception(f"Error updating offer: {e}")
        finally:
            if cursor:
                cursor.close()
    
    def get_offers_count(self) -> int:
        """Get total count of offers"""
        cursor = None
        try:
            self.connect()
            cursor = self.get_cursor()
            
            cursor.execute("SELECT COUNT(*) as count FROM offers")
            result = cursor.fetchone()
            return result["count"]
            
        except Exception as e:
            raise Exception(f"Error counting offers: {e}")
        finally:
            if cursor:
                cursor.close()
    
    def search_offers(self, search_term: str, user_id: str, limit: int = 100) -> List[Dict]:
        """Search offers by text across multiple fields for a specific user"""
        cursor = None
        try:
            self.connect()
            cursor = self.get_cursor()
            
            search_pattern = f"%{search_term}%"
            
            cursor.execute("""
                SELECT * FROM offers 
                WHERE user_id = %s
                  AND (customer_name ILIKE %s 
                   OR phone_number ILIKE %s 
                   OR address ILIKE %s 
                   OR task_description ILIKE %s)
                ORDER BY created_at DESC 
                LIMIT %s
            """, (user_id, search_pattern, search_pattern, search_pattern, search_pattern, limit))
            
            offers = cursor.fetchall()
            return [dict(offer) for offer in offers]
            
        except Exception as e:
            raise Exception(f"Error searching offers: {e}")
        finally:
            if cursor:
                cursor.close()
    
    def toggle_order_status(self, offer_id: str, status: str) -> Dict:
        """Update the status of an offer (Pending, Accepted, Done)"""
        cursor = None
        try:
            self.connect()
            cursor = self.get_cursor()
            
            # Validate status value
            valid_statuses = ["Pending", "Accepted", "Done"]
            if status not in valid_statuses:
                raise Exception(f"Invalid status. Must be one of: {', '.join(valid_statuses)}")
            
            # Check if offer exists
            cursor.execute("""
                SELECT id FROM offers WHERE id = %s
            """, (offer_id,))
            
            offer = cursor.fetchone()
            if not offer:
                raise Exception("offer not found")
            
            # Update the offer status
            cursor.execute("""
                UPDATE offers SET 
                    status = %s,
                    updated_at = %s
                WHERE id = %s
            """, (status, datetime.now(), offer_id))
            
            self.conn.commit()
            
            return {
                "success": True,
                "offer_id": offer_id,
                "status": status
            }
        
        except Exception as e:
            if self.conn:
                self.conn.rollback()
            raise Exception(f"Error updating offer status: {e}")
        finally:
            if cursor:
                cursor.close()
    
    def toggle_materials_ordered(self, offer_id: str) -> Dict:
        """Toggle the materials_ordered status of an offer"""
        cursor = None
        try:
            self.connect()
            cursor = self.get_cursor()
            
            # Get current offer
            cursor.execute("""
                SELECT materials_ordered FROM offers WHERE id = %s
            """, (offer_id,))
            
            offer = cursor.fetchone()
            if not offer:
                raise Exception("offer not found")
            
            # Toggle the materials_ordered status
            current_status = offer["materials_ordered"]
            new_status = not current_status
            
            # Update the offer
            cursor.execute("""
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
        finally:
            if cursor:
                cursor.close()

    # ==================== INVENTORY MANAGEMENT METHODS ====================
    
    def create_inventory_item(self, item: InventoryItem) -> str:
        """Create a new inventory item"""
        cursor = None
        try:
            self.connect()
            cursor = self.get_cursor()
            
            # Convert Pydantic model to dict
            item_dict = item.dict(exclude={'id'})
            
            cursor.execute("""
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
            
            item_id = cursor.fetchone()["id"]
            self.conn.commit()
            return str(item_id)
            
        except Exception as e:
            if self.conn:
                self.conn.rollback()
            raise Exception(f"Error creating inventory item: {e}")
        finally:
            if cursor:
                cursor.close()
    
    def get_inventory_item_by_id(self, item_id: str) -> Optional[Dict]:
        """Get an inventory item by its ID"""
        cursor = None
        try:
            self.connect()
            cursor = self.get_cursor()
            
            cursor.execute("""
                SELECT * FROM inventory WHERE id = %s
            """, (item_id,))
            
            item = cursor.fetchone()
            
            if item:
                return dict(item)
            return None
            
        except Exception as e:
            raise Exception(f"Error fetching inventory item: {e}")
        finally:
            if cursor:
                cursor.close()
    
    def get_all_inventory_items(self, 
                                 limit: int = 100, 
                                 offset: int = 0,
                                 active: Optional[bool] = None,
                                 category: Optional[str] = None) -> List[Dict]:
        """Get all inventory items with optional filters and pagination"""
        cursor = None
        try:
            self.connect()
            cursor = self.get_cursor()
            
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
            
            cursor.execute(f"""
                SELECT * FROM inventory 
                {where_clause}
                ORDER BY created_at DESC 
                LIMIT %s OFFSET %s
            """, params)
            
            items = cursor.fetchall()
            return [dict(item) for item in items]
            
        except Exception as e:
            raise Exception(f"Error fetching inventory items: {e}")
        finally:
            if cursor:
                cursor.close()
    
    def update_inventory_item(self, item_id: str, update_data: Dict) -> bool:
        """Update an existing inventory item"""
        cursor = None
        try:
            self.connect()
            cursor = self.get_cursor()
            
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
            
            cursor.execute(query, params)
            
            modified = cursor.rowcount > 0
            self.conn.commit()
            return modified
                
        except Exception as e:
            if self.conn:
                self.conn.rollback()
            raise Exception(f"Error updating inventory item: {e}")
        finally:
            if cursor:
                cursor.close()
    
    def delete_inventory_item(self, item_id: str) -> bool:
        """Delete an inventory item by ID"""
        cursor = None
        try:
            self.connect()
            cursor = self.get_cursor()
            
            cursor.execute("""
                DELETE FROM inventory WHERE id = %s
            """, (item_id,))
            
            deleted = cursor.rowcount > 0
            self.conn.commit()
            return deleted
                
        except Exception as e:
            if self.conn:
                self.conn.rollback()
            raise Exception(f"Error deleting inventory item: {e}")
        finally:
            if cursor:
                cursor.close()
    
    def search_inventory_items(self, 
                               search_term: str, 
                               category: Optional[str] = None,
                               active: bool = True,
                               limit: int = 100) -> List[Dict]:
        """Search inventory items by text across multiple fields"""
        cursor = None
        try:
            self.connect()
            cursor = self.get_cursor()
            
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
            
            cursor.execute(f"""
                SELECT * FROM inventory 
                WHERE {where_clause}
                ORDER BY created_at DESC 
                LIMIT %s
            """, params)
            
            items = cursor.fetchall()
            return [dict(item) for item in items]
            
        except Exception as e:
            raise Exception(f"Error searching inventory items: {e}")
        finally:
            if cursor:
                cursor.close()
    
    def get_inventory_count(self, active: Optional[bool] = None) -> int:
        """Get total count of inventory items"""
        cursor = None
        try:
            self.connect()
            cursor = self.get_cursor()
            
            if active is not None:
                cursor.execute("""
                    SELECT COUNT(*) as count FROM inventory WHERE active = %s
                """, (active,))
            else:
                cursor.execute("SELECT COUNT(*) as count FROM inventory")
            
            result = cursor.fetchone()
            return result["count"]
            
        except Exception as e:
            raise Exception(f"Error counting inventory items: {e}")
        finally:
            if cursor:
                cursor.close()
    
    def get_inventory_by_category(self, category: str) -> List[Dict]:
        """Get all inventory items in a specific category"""
        cursor = None
        try:
            self.connect()
            cursor = self.get_cursor()
            
            cursor.execute("""
                SELECT * FROM inventory 
                WHERE category ILIKE %s AND active = TRUE
                ORDER BY name ASC
            """, (f"%{category}%",))
            
            items = cursor.fetchall()
            return [dict(item) for item in items]
            
        except Exception as e:
            raise Exception(f"Error fetching inventory by category: {e}")
        finally:
            if cursor:
                cursor.close()
    
    def search_available_resources(self, user_id: str) -> List[Dict]:
        """
        Search for available manpower resources for a specific supervisor/user.
        Queries the supplychain_resource table filtered by supervisor_id.
        """
        cursor = None
        try:
            self.connect()
            cursor = self.get_cursor()
            
            cursor.execute("""
                SELECT name
                FROM supplychain_resource
                WHERE supervisor_id = %s
                ORDER BY name ASC
            """, (user_id,))
            
            resources = cursor.fetchall()
            return [dict(resource) for resource in resources]
            
        except Exception as e:
            raise Exception(f"Error fetching available resources: {e}")
        finally:
            if cursor:
                cursor.close()
    
    # ==================== SUPPLIER MANAGEMENT METHODS ====================
    
    def get_suppliers(self, user_id: str) -> List[Dict]:
        """Get suppliers from the supplychain_supplier table filtered by supervisor_id"""
        cursor = None
        try:
            self.connect()
            cursor = self.get_cursor()
            
            cursor.execute("""
                SELECT id, supplier_name, supplier_email 
                FROM supplychain_supplier 
                WHERE supervisor_id = %s
                ORDER BY supplier_name ASC
            """, (user_id,))
            
            suppliers = cursor.fetchall()
            return [dict(supplier) for supplier in suppliers]
            
        except Exception as e:
            raise Exception(f"Error fetching suppliers: {e}")
        finally:
            if cursor:
                cursor.close()


    def get_supplier_by_id(self, supplier_id: str) -> Optional[Dict]:
        """Get supplier from the supplychain_supplier table filtered by supplier_id"""
        cursor = None
        try:
            self.connect()
            cursor = self.get_cursor()
            
            cursor.execute("""
                SELECT id, supplier_name, supplier_email 
                FROM supplychain_supplier 
                WHERE id = %s
            """, (supplier_id,))
            
            supplier = cursor.fetchone()
            if supplier:
                return dict(supplier)
            return None
            
        except Exception as e:
            raise Exception(f"Error fetching supplier: {e}")
        finally:
            if cursor:
                cursor.close()


