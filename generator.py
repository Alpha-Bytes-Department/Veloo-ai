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
        

    def generate_offer_email(self, offer: Dict) -> EmailResponse:
        """
        Generate professional email content for a customer based on their offer.
        
        Args:
            offer: Dictionary containing the offer details from the database
            
        Returns:
            EmailResponse with customer_name, email_subject, and email_body
        """
        try:
            # Extract offer details
            customer_name = offer.get("customer_name", "Valued Customer")
            phone_number = offer.get("phone_number", "N/A")
            address = offer.get("address", "N/A")
            task_description = offer.get("task_description", "N/A")
            bill_of_materials = offer.get("bill_of_materials", [])
            time_estimate = offer.get("time", "N/A")
            price_details = offer.get("price", {})
            
            # Format bill of materials for better readability
            materials_text = ""
            if bill_of_materials:
                for idx, material in enumerate(bill_of_materials, 1):
                    materials_text += f"\n{idx}. {material.get('material', 'N/A')} - {material.get('category', 'N/A')}"
                    materials_text += f"\n   Quantity: {material.get('quantity', 'N/A')} {material.get('unit', '')}"
                    materials_text += f"\n   Price: ${material.get('price', 'N/A')}"
                    if material.get('description'):
                        materials_text += f"\n   Description: {material.get('description')}"
                    materials_text += "\n"
            
            # Format price breakdown
            price_text = f"""
                Materials Cost: ${price_details.get('Materials', 0):,.2f}
                Labor Cost: ${price_details.get('Labor', 0):,.2f}
                Total Cost: ${price_details.get('Total', 0):,.2f}
                """
                            
            # Create prompt for AI to generate email
            email_prompt = f"""
                Generate a professional, warm, and engaging email to send to a customer regarding their construction/service offer.

                Customer Details:
                - Name: {customer_name}
                - Phone: {phone_number}
                - Address: {address}

                Offer Details:
                - Task Description: {task_description}
                - Estimated Time: {time_estimate}
                - Bill of Materials: {materials_text}
                - Price Breakdown: {price_text}

                The email should:
                1. Be professional yet friendly and approachable
                2. Thank the customer for their interest
                3. Provide a clear overview of the project
                4. Include all materials and pricing details in a well-formatted manner
                5. Highlight the time estimate for completion
                6. Include a call-to-action (e.g., contact for questions, approval, next steps)
                7. End with a professional closing

                Generate both an email subject line and the complete email body.
                The email should be formatted in a clean, readable way with proper sections and spacing.
                """
            
            messages = [
                {
                    "role": "system", 
                    "content": "You are a professional business communication specialist. Generate clear, engaging, and customer-friendly email content for construction/service offers. Use proper formatting with line breaks and sections for readability."
                },
                {"role": "user", "content": email_prompt}
            ]
            
            # Call OpenAI API to generate email content
            response = self.client.beta.chat.completions.parse(
                model="gpt-4o-mini",
                messages=messages,
                response_format=EmailResponse,
            )
            
            email_response = response.choices[0].message.parsed
            
            return email_response
        
        except Exception as e:
            raise Exception(f"Error generating email content: {str(e)}")
        

    def generate_acceptance_email(self, offer: Dict) -> EmailResponse:
        """
        Generate professional thank you email content for a customer who accepted the offer.
        
        Args:
            offer: Dictionary containing the offer details from the database
            
        Returns:
            EmailResponse with customer_name, email_subject, and email_body
        """
        try:
            # Extract offer details
            customer_name = offer.get("customer_name", "Valued Customer")
            phone_number = offer.get("phone_number", "N/A")
            address = offer.get("address", "N/A")
            task_description = offer.get("task_description", "N/A")
            time_estimate = offer.get("time", "N/A")
            price_details = offer.get("price", {})
            project_start = offer.get("project_start", "To be confirmed")
            
            # Format price total
            total_price = price_details.get('Total', 0)
            
            # Create prompt for AI to generate acceptance email
            email_prompt = f"""
            Generate a professional, warm, and appreciative email to thank a customer for accepting our construction/service offer.

            Customer Details:
            - Name: {customer_name}
            - Phone: {phone_number}
            - Address: {address}

            Project Details:
            - Task Description: {task_description}
            - Estimated Time: {time_estimate}
            - Project Start Date: {project_start}
            - Total Project Cost: ${total_price:,.2f}

            The email should:
            1. Express sincere gratitude and appreciation for accepting the offer
            2. Confirm the project details briefly
            3. Outline the next steps (e.g., scheduling, materials ordering, preparation)
            4. Reassure the customer of quality service and commitment
            5. Provide contact information for any questions or concerns
            6. Express excitement about working together
            7. End with a professional and warm closing

            Generate both an email subject line and the complete email body.
            The tone should be professional yet warm, showing genuine appreciation for their trust and business.
            The email should be formatted in a clean, readable way with proper sections and spacing.
            """
            
            messages = [
                {
                    "role": "system", 
                    "content": "You are a professional business communication specialist. Generate warm, appreciative, and customer-friendly email content thanking clients for accepting construction/service offers. Show genuine gratitude and build confidence in the upcoming project. Use proper formatting with line breaks and sections for readability."
                },
                {"role": "user", "content": email_prompt}
            ]
            
            # Call OpenAI API to generate email content
            response = self.client.beta.chat.completions.parse(
                model="gpt-4o-mini",
                messages=messages,
                response_format=EmailResponse,
            )
            
            email_response = response.choices[0].message.parsed
            
            return email_response
        
        except Exception as e:
            raise Exception(f"Error generating acceptance email content: {str(e)}")