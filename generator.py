from openai import OpenAI
from typing import List, Dict
import os
import json
from schema import offerRequest, Finaloffer, EmailRequest, EmailResponse
from dotenv import load_dotenv
from datetime import datetime

load_dotenv()

class Generator:
    def __init__(self, database=None):
        self.client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
        self.database = database  # Store database reference for inventory queries

        # Define tool schema for function calling
        self.tools = [
            {
                "type": "function",
                "function": {
                    "name": "get_inventory_data",
                    "description": "Search the database for current information on inventory, pricing, and availability of materials and services.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "query": {
                                "type": "string",
                                "description": "The search query to find relevant information on the database.",
                            },
                        },
                        "required": ["query"],
                    },
                }
            }
        ]

        self.system_prompt = """You are a professional offer generator assistant. 
        Generate detailed construction/service offers based on customer requirements.
        Provide comprehensive bill of materials, time estimates, and accurate pricing.
        Format your response as a structured offer with all required fields."""

    def get_inventory_data(self, query: str) -> Dict:
        """
        Get inventory data from database based on query.
        This function should retrieve relevant inventory, pricing, and availability data.
        """
        try:
            if not self.database:
                return {
                    "error": "Database connection not available",
                    "items": []
                }
            
            # Search inventory items based on the query
            items = self.database.search_inventory_items(
                search_term=query,
                is_active=True,
                limit=50
            )
            
            if not items:
                return {
                    "message": f"No inventory items found for query: {query}",
                    "items": []
                }
            
            # Format the inventory data for the AI model
            formatted_items = []
            for item in items:
                formatted_items.append({
                    "name": item.get("name"),
                    "category": item.get("category"),
                    "description": item.get("description", ""),
                    "unit": item.get("unit"),
                    "unit_price": item.get("unit_price"),
                    "quantity_available": item.get("quantity_available"),
                    "supplier": item.get("supplier", ""),
                    "sku": item.get("sku", "")
                })
            
            return {
                "query": query,
                "items_found": len(formatted_items),
                "items": formatted_items
            }
            
        except Exception as e:
            return {
                "error": f"Error fetching inventory data: {str(e)}",
                "items": []
            } 
    
    
    def generate_offer(self, offer_request: offerRequest) -> Finaloffer:
        try:
            # Create a detailed prompt from the request data
            user_input = f"""
            Generate a professional offer for the following customer:
            
            Customer Name: {offer_request.customer_name}
            Phone: {offer_request.phone_number}
            Address: {offer_request.address}
            Project Start Date: {offer_request.project_start}
            Task Selected: {offer_request.select_task}
            Additional Details: {offer_request.explaination}
            Time: {datetime.now().isoformat()}
            Materials Ordered: False (Set by default)
            
            Please provide:
            1. Detailed task description
            2. Complete bill of materials with quantities and costs
            3. Time estimate for completion
            4. Total price breakdown
            """
            
            # Create messages for chat completion
            messages = [
                {"role": "system", "content": self.system_prompt},
                {"role": "user", "content": user_input}
            ]
            
            # 1. Prompt the model with tools defined
            response = self.client.chat.completions.create(
                model="gpt-4o-mini",
                tools=self.tools,
                messages=messages,
            )
            
            response_message = response.choices[0].message
            tool_calls = response_message.tool_calls
            
            # 2. Check if model made any function calls
            if tool_calls:
                # Add assistant's response to messages
                messages.append(response_message)
                
                # 3. Execute each tool call
                for tool_call in tool_calls:
                    if tool_call.function.name == "get_inventory_data":
                        # Execute the function logic
                        arguments = json.loads(tool_call.function.arguments)
                        inventory_data = self.get_inventory_data(arguments.get("query", ""))
                        
                        # 4. Provide function call results to the model
                        messages.append({
                            "role": "tool",
                            "tool_call_id": tool_call.id,
                            "content": json.dumps(inventory_data)
                        })
                
                # 5. Get final response with tool results
                final_response = self.client.beta.chat.completions.parse(
                    model="gpt-4o-mini",
                    messages=messages,
                    response_format=Finaloffer,
                )
                
                offer = final_response.choices[0].message.parsed
            else:
                # No tool calls, parse the response directly
                final_response = self.client.beta.chat.completions.parse(
                    model="gpt-4o-mini",
                    messages=messages,
                    response_format=Finaloffer,
                )
                
                offer = final_response.choices[0].message.parsed
            
            return offer
        
        except Exception as e:
            raise Exception(f"Error generating offer: {str(e)}")
    

    def update_offer(self, user_message: str, update_request: Finaloffer) -> Finaloffer:
        try:
            # Create a detailed prompt from the request data
            user_input = f"""
            Generate a professional offer for the following customer:
            
            Customer Name: {update_request.customer_name}
            Phone: {update_request.phone_number}
            Address: {update_request.address}
            Task Description: {update_request.task_description}
            Bill of Materials: {update_request.bill_of_materials}
            Time: {update_request.time}
            Price: {update_request.price}
            
            Please update the offer as per user request:
            {user_message}
            """
            
            messages = [
                {"role": "system", "content": self.system_prompt},
                {"role": "user", "content": user_input}
            ]
            
            response = self.client.beta.chat.completions.parse(
                model="gpt-4o-mini",
                messages=messages,
                response_format=Finaloffer,
            )
            
            offer = response.choices[0].message.parsed
            
            return offer
        
        except Exception as e:
            raise Exception(f"Error generating offer: {str(e)}")
        