import sqlite3
import json
from typing import List, Optional, Dict
from datetime import datetime
from schema import GeneratedQuotation

class Database:
    def __init__(self, db_name: str = "quotations.db"):
        self.db_name = db_name
    
    def get_connection(self):
        """Get database connection"""
        conn = sqlite3.connect(self.db_name)
        conn.row_factory = sqlite3.Row  # Enable dict-like access to rows
        return conn
    
    def init_db(self):
        """Initialize the database with required tables"""
        conn = self.get_connection()
        try:
            cursor = conn.cursor()
            
            # Create quotations table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS quotations (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    customer_name TEXT NOT NULL,
                    phone_number TEXT NOT NULL,
                    address TEXT NOT NULL,
                    task_description TEXT NOT NULL,
                    bill_of_materials TEXT NOT NULL,
                    time TEXT NOT NULL,
                    price TEXT NOT NULL,
                    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            conn.commit()
            print("Database initialized successfully")
            
        except Exception as e:
            print(f"Error initializing database: {e}")
            conn.rollback()
        finally:
            conn.close()
    
    def save_quotation(self, quotation: GeneratedQuotation) -> int:
        """Save a quotation to the database"""
        conn = self.get_connection()
        try:
            cursor = conn.cursor()
            
            cursor.execute('''
                INSERT INTO quotations (
                    customer_name, phone_number, address, task_description,
                    bill_of_materials, time, price, timestamp
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                quotation.customer_name,
                quotation.phone_number,
                quotation.address,
                quotation.task_description,
                quotation.bill_of_materials,
                quotation.time,
                quotation.price,
                quotation.timestamp or datetime.now()
            ))
            
            quotation_id = cursor.lastrowid
            conn.commit()
            return quotation_id
            
        except Exception as e:
            conn.rollback()
            raise Exception(f"Error saving quotation: {e}")
        finally:
            conn.close()
    
    def get_quotation_by_id(self, quotation_id: int) -> Optional[Dict]:
        """Get a quotation by its ID"""
        conn = self.get_connection()
        try:
            cursor = conn.cursor()
            cursor.execute('SELECT * FROM quotations WHERE id = ?', (quotation_id,))
            row = cursor.fetchone()
            
            if row:
                return dict(row)
            return None
            
        except Exception as e:
            raise Exception(f"Error fetching quotation: {e}")
        finally:
            conn.close()
    
    def get_all_quotations(self, limit: int = 100, offset: int = 0) -> List[Dict]:
        """Get all quotations with pagination"""
        conn = self.get_connection()
        try:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT * FROM quotations 
                ORDER BY created_at DESC 
                LIMIT ? OFFSET ?
            ''', (limit, offset))
            
            rows = cursor.fetchall()
            return [dict(row) for row in rows]
            
        except Exception as e:
            raise Exception(f"Error fetching quotations: {e}")
        finally:
            conn.close()
    
    def get_quotations_by_customer(self, customer_name: str) -> List[Dict]:
        """Get all quotations for a specific customer"""
        conn = self.get_connection()
        try:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT * FROM quotations 
                WHERE customer_name LIKE ? 
                ORDER BY created_at DESC
            ''', (f"%{customer_name}%",))
            
            rows = cursor.fetchall()
            return [dict(row) for row in rows]
            
        except Exception as e:
            raise Exception(f"Error fetching customer quotations: {e}")
        finally:
            conn.close()
    
    def delete_quotation(self, quotation_id: int) -> bool:
        """Delete a quotation by ID"""
        conn = self.get_connection()
        try:
            cursor = conn.cursor()
            cursor.execute('DELETE FROM quotations WHERE id = ?', (quotation_id,))
            
            if cursor.rowcount > 0:
                conn.commit()
                return True
            else:
                return False
                
        except Exception as e:
            conn.rollback()
            raise Exception(f"Error deleting quotation: {e}")
        finally:
            conn.close()
    
    def update_quotation(self, quotation_id: int, quotation: GeneratedQuotation) -> bool:
        """Update an existing quotation"""
        conn = self.get_connection()
        try:
            cursor = conn.cursor()
            
            cursor.execute('''
                UPDATE quotations SET
                    customer_name = ?, phone_number = ?, address = ?,
                    task_description = ?, bill_of_materials = ?,
                    time = ?, price = ?, timestamp = ?
                WHERE id = ?
            ''', (
                quotation.customer_name,
                quotation.phone_number,
                quotation.address,
                quotation.task_description,
                quotation.bill_of_materials,
                quotation.time,
                quotation.price,
                quotation.timestamp or datetime.now(),
                quotation_id
            ))
            
            if cursor.rowcount > 0:
                conn.commit()
                return True
            else:
                return False
                
        except Exception as e:
            conn.rollback()
            raise Exception(f"Error updating quotation: {e}")
        finally:
            conn.close()
