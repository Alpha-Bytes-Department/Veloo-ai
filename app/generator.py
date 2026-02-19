from openai import OpenAI
from typing import List, Dict
import os
import json
from app.schema import offerRequest, Finaloffer, GeneratedOfferContent, EmailRequest, EmailResponse
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
        Generate detailed construction/service offers based on project requirements.
        
        Your response MUST include ALL of these fields:
        - task_description: Detailed description of the work to be done
        - bill_of_materials: Array of materials needed (each with category, material, price, description, unit, quantity)
        - time: Estimated completion time.
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
    
    
    def generate_offer(self, offer_request: offerRequest) -> Finaloffer:
        try:
            # Create a detailed prompt from the request data
            # NOTE: Customer personal info (name, phone, address) is NOT sent to the AI
            user_input = f"""
            Generate a professional offer for the following project:
            
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
            4. Total price breakdown with Materials, Labor, and Total in the 'price' field
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
                    

                
                # 5. Get final response with tool results (using GeneratedOfferContent - no personal info)
                final_response = self.client.beta.chat.completions.parse(
                    model="gpt-4o-mini",
                    messages=messages,
                    response_format=GeneratedOfferContent,
                )
                
                generated_content = final_response.choices[0].message.parsed
            else:
                # No tool calls, parse the response directly (using GeneratedOfferContent - no personal info)
                final_response = self.client.beta.chat.completions.parse(
                    model="gpt-4o-mini",
                    messages=messages,
                    response_format=GeneratedOfferContent,
                )
                
                generated_content = final_response.choices[0].message.parsed
            
            # Merge AI-generated content with customer personal information locally
            offer = Finaloffer(
                customer_name=offer_request.customer_name,
                phone_number=offer_request.phone_number,
                address=offer_request.address,
                customer_email=offer_request.customer_email,
                task_description=generated_content.task_description,
                bill_of_materials=generated_content.bill_of_materials,
                time=generated_content.time,
                resource=offer_request.resource,
                status=generated_content.status,
                price=generated_content.price,
                project_start=generated_content.project_start,
                materials_ordered=generated_content.materials_ordered
            )
            
            return offer
        
        except Exception as e:
            raise Exception(f"Error generating offer: {str(e)}")
    

    def update_offer(self, user_message: str, update_request: Finaloffer) -> Finaloffer:
        try:
            # Create a detailed prompt from the request data
            # NOTE: Customer personal info (name, phone, address) is NOT sent to the AI
            user_input = f"""
            Update the following professional offer based on the user's request:
            
            Current Offer Details:
            - Task Description: {update_request.task_description}
            - Bill of Materials: {update_request.bill_of_materials}
            - Time: {update_request.time}
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
            - Return a complete offer object with all fields
            """
            
            messages = [
                {"role": "system", "content": self.system_prompt},
                {"role": "user", "content": user_input}
            ]
            
            # Use GeneratedOfferContent to avoid sending/receiving personal info
            response = self.client.beta.chat.completions.parse(
                model="gpt-4o-mini",
                messages=messages,
                response_format=GeneratedOfferContent,
            )
            
            generated_content = response.choices[0].message.parsed
            
            # Merge AI-generated content with customer personal information from original request
            offer = Finaloffer(
                customer_name=update_request.customer_name,
                phone_number=update_request.phone_number,
                address=update_request.address,
                customer_email=update_request.customer_email,
                task_description=generated_content.task_description,
                bill_of_materials=generated_content.bill_of_materials,
                time=generated_content.time,
                resource=update_request.resource,
                status=generated_content.status,
                price=generated_content.price,
                project_start=generated_content.project_start,
                materials_ordered=generated_content.materials_ordered
            )
            
            return offer
        
        except Exception as e:
            raise Exception(f"Error generating offer: {str(e)}")
    
    # ==================== CHAT-BASED OFFER GENERATION ====================
    
    # In-memory session storage: {session_id: {"messages": [...], "customer_info": {...}, "project_start": ...}}
    _chat_sessions: Dict[str, Dict] = {}
    
    # Tools for chat-based offer generation
    chat_tools = [
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
                "name": "generate_final_offer",
                "description": "Generate the final offer when you have gathered enough information from the user. Only call this when you have sufficient details about the project requirements, scope, and preferences.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "task_description": {
                            "type": "string",
                            "description": "Detailed description of the work to be done",
                        },
                        "bill_of_materials": {
                            "type": "array",
                            "description": "Array of materials needed",
                            "items": {
                                "type": "object",
                                "properties": {
                                    "category": {"type": "string"},
                                    "material": {"type": "string"},
                                    "price": {"type": "string"},
                                    "description": {"type": "string"},
                                    "unit": {"type": "string"},
                                    "quantity": {"type": "string"}
                                },
                                "required": ["category", "material", "price", "description", "unit", "quantity"]
                            }
                        },
                        "time": {
                            "type": "string",
                            "description": "Estimated completion time",
                        },
                        "materials_cost": {
                            "type": "number",
                            "description": "Total cost of materials",
                        },
                        "labor_cost": {
                            "type": "number",
                            "description": "Total cost of labor",
                        },
                        "total_cost": {
                            "type": "number",
                            "description": "Total project cost (materials + labor)",
                        },
                    },
                    "required": ["task_description", "bill_of_materials", "time", "materials_cost", "labor_cost", "total_cost"],
                },
            }
        }
    ]
    
    chat_system_prompt = """You are a professional offer generator assistant for construction and service projects.

Your role is to have a conversation with the user to understand their project requirements before generating an offer.

IMPORTANT GUIDELINES:
1. If the user's initial request is vague or missing important details, ask clarifying questions.
2. Ask about: project scope, area size, preferred materials, quality level, timeline preferences, etc.
3. Keep questions concise and focused - ask 1-2 questions at a time.
4. When you have enough information to create a comprehensive offer, call the generate_final_offer tool.
5. You can use get_inventory_data to check available materials and pricing.

DO NOT generate an offer until you have sufficient details. It's better to ask questions than to make assumptions.

When ready to generate the offer, call generate_final_offer with:
- task_description: Detailed description of the work
- bill_of_materials: Complete list of materials with prices
- time: Estimated completion time
- materials_cost, labor_cost, total_cost: Price breakdown"""

    def chat_for_offer(self, session_id: str, message: str, customer_info: dict = None, project_start = None) -> Dict:
        """
        Handle chat-based offer generation.
        Returns either a message (clarification) or a final offer.
        
        First message: customer_info and project_start are required and stored in session.
        Follow-up messages: customer_info and project_start are optional (uses stored values).
        """
        try:
            # Get or create session
            if session_id not in self._chat_sessions:
                # New session - customer info is required
                if not customer_info:
                    raise Exception("Session expired or not found. Please start a new conversation with customer info.")
                
                self._chat_sessions[session_id] = {
                    "messages": [{"role": "system", "content": self.chat_system_prompt}],
                    "customer_info": customer_info,
                    "project_start": project_start
                }
            
            session = self._chat_sessions[session_id]
            messages = session["messages"]
            stored_customer_info = session["customer_info"]
            stored_project_start = session["project_start"]
            
            messages.append({"role": "user", "content": message})
            
            # Call AI with tools
            response = self.client.chat.completions.create(
                model="gpt-4o-mini",
                messages=messages,
                tools=self.chat_tools,
            )
            
            response_message = response.choices[0].message
            tool_calls = response_message.tool_calls
            
            # Process tool calls
            if tool_calls:
                messages.append(response_message)
                
                for tool_call in tool_calls:
                    if tool_call.function.name == "get_inventory_data":
                        arguments = json.loads(tool_call.function.arguments)
                        inventory_data = self.get_inventory_data(arguments.get("query", ""))
                        messages.append({
                            "role": "tool",
                            "tool_call_id": tool_call.id,
                            "content": json.dumps(inventory_data)
                        })
                    
                    elif tool_call.function.name == "generate_final_offer":
                        # AI decided to generate the offer
                        arguments = json.loads(tool_call.function.arguments)
                        
                        # Build the final offer
                        from schema import Finaloffer, Materials, PriceDetail
                        
                        bill_of_materials = [
                            Materials(**mat) for mat in arguments.get("bill_of_materials", [])
                        ]
                        
                        price = PriceDetail(
                            Materials=arguments.get("materials_cost", 0),
                            Labor=arguments.get("labor_cost", 0),
                            Total=arguments.get("total_cost", 0)
                        )
                        
                        offer = Finaloffer(
                            customer_name=stored_customer_info.get("customer_name", ""),
                            phone_number=stored_customer_info.get("phone_number", ""),
                            address=stored_customer_info.get("address", ""),
                            customer_email=stored_customer_info.get("customer_email", ""),
                            task_description=arguments.get("task_description", ""),
                            bill_of_materials=bill_of_materials,
                            time=arguments.get("time", ""),
                            resource=stored_customer_info.get("resource", ""),
                            status="Pending",
                            price=price,
                            project_start=stored_project_start,
                            materials_ordered=False
                        )
                        
                        # Clear session after generating offer
                        del self._chat_sessions[session_id]
                        
                        return {
                            "type": "offer",
                            "offer": offer
                        }
                
                # If only inventory lookup, get follow-up response
                follow_up = self.client.chat.completions.create(
                    model="gpt-4o-mini",
                    messages=messages,
                )
                
                assistant_message = follow_up.choices[0].message.content
                messages.append({"role": "assistant", "content": assistant_message})
                
                return {
                    "type": "message",
                    "message": assistant_message
                }
            
            else:
                # No tool calls - AI is asking a question or responding
                assistant_message = response_message.content
                messages.append({"role": "assistant", "content": assistant_message})
                
                return {
                    "type": "message",
                    "message": assistant_message
                }
        
        except Exception as e:
            raise Exception(f"Error in chat for offer: {str(e)}")
        