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
            },
            {
                "type": "function",
                "function": {
                    "name": "search_available_resources",
                    "description": "Search for available workers (manpower resources) for a specific user. Returns the names of workers who are available to be assigned to tasks.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "user_id": {
                                "type": "string",
                                "description": "The user ID to search available workers for.",
                            },
                        },
                        "required": ["user_id"],
                    },
                }
            }
        ]

        self.system_prompt = """You are a professional offer generator assistant. 
        Generate detailed construction/service offers based on customer requirements.
        
        Your response MUST include ALL of these fields:
        - customer_name: Use the exact customer name provided
        - phone_number: Use the exact phone number provided
        - address: Use the exact address provided
        - task_description: Detailed description of the work to be done
        - bill_of_materials: Array of materials needed (each with category, material, price, description, unit, quantity)
        - time: Estimated completion time.
        - resource: Name of the assigned worker (use search_available_resources tool to get available workers)
        - status: Default to "Pending"
        - price: Object with Materials (float), Labor (float), and Total (float)
        - project_start: Use the exact project start date provided
        - materials_ordered: Default to false
        
        Provide comprehensive bill of materials, accurate time estimates, and realistic pricing.
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
                active=True,
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
                    "id": item.get("id"),
                    "name": item.get("name"),
                    "category": item.get("category"),
                    "description": item.get("description", ""),
                    "brand": item.get("brand", ""),
                    "default_price": float(item.get("default_price", 0)),
                    "active": item.get("active", True)
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
    
    def search_available_resources(self, user_id: str) -> Dict:
        """
        Search for available workers (manpower resources) for a specific user.
        Returns the names of workers who are available to be assigned to tasks.
        """
        try:
            if not self.database:
                return {
                    "error": "Database connection not available",
                    "resources": []
                }
            
            # Call database method to get available resources
            resources = self.database.search_available_resources(user_id)
            
            return {
                "user_id": user_id,
                "resources_found": len(resources),
                "resources": resources
            }
            
        except Exception as e:
            return {
                "error": f"Error fetching available resources: {str(e)}",
                "resources": []
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
            User ID: {offer_request.user_id}
            Project_start: {offer_request.project_start} (MUST use this exact date)
            Status: "Pending"
            Materials_ordered: false
            
            Please provide:
            1. Detailed task_description based on the task selected and explanation
            2. Complete bill_of_materials with category, material name, price, description, unit, and quantity
            3. Time estimate for completion.
            4. Available worker name in the 'resource' field (use search_available_resources tool to find and assign a worker)
            5. Total price breakdown with Materials, Labor, and Total in the 'price' field
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
                    
                    elif tool_call.function.name == "search_available_resources":
                        # Execute the function logic
                        arguments = json.loads(tool_call.function.arguments)
                        resources_data = self.search_available_resources(arguments.get("user_id", ""))
                        
                        # 4. Provide function call results to the model
                        messages.append({
                            "role": "tool",
                            "tool_call_id": tool_call.id,
                            "content": json.dumps(resources_data)
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
            Update the following professional offer based on the user's request:
            
            Current Offer Details:
            - Customer Name: {update_request.customer_name}
            - Phone: {update_request.phone_number}
            - Address: {update_request.address}
            - Task Description: {update_request.task_description}
            - Bill of Materials: {update_request.bill_of_materials}
            - Time: {update_request.time}
            - Resource: {update_request.resource}
            - Status: {update_request.status}
            - Project Start Date: {update_request.project_start}
            - Price: {update_request.price}
            - Materials Ordered: {update_request.materials_ordered}
            
            User's Update Request:
            {user_message}
            
            IMPORTANT: 
            - Keep all fields that are not mentioned in the update request unchanged
            - Maintain the exact project_start date unless explicitly asked to change it
            - Ensure all required fields are present in the updated offer
            - Return a complete Finaloffer object with all fields
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
        