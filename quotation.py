from openai import OpenAI
from typing import List, Dict
import os
import json
from schema import QuotationRequest, FinalQuotation
from dotenv import load_dotenv
from datetime import datetime

load_dotenv()

class Generator:
    def __init__(self):
        self.client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

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

        self.system_prompt = """You are a professional quotation generator assistant. 
        Generate detailed construction/service quotations based on customer requirements.
        Provide comprehensive bill of materials, time estimates, and accurate pricing.
        Format your response as a structured quotation with all required fields."""

    def get_inventory_data(self, query: str) -> Dict:
        """
        Get inventory data from database based on query.
        This function should retrieve relevant inventory, pricing, and availability data.
        """
        # TODO: Implement database query logic here
        # This is a placeholder - implement your actual database query
        pass 
    
    
    def generate_quotation(self, quotation_request: QuotationRequest) -> FinalQuotation:
        try:
            # Create a detailed prompt from the request data
            user_input = f"""
            Generate a professional quotation for the following customer:
            
            Customer Name: {quotation_request.customer_name}
            Phone: {quotation_request.phone_number}
            Address: {quotation_request.address}
            Project Start Date: {quotation_request.project_start}
            Task Selected: {quotation_request.select_task}
            Additional Details: {quotation_request.explaination}
            Time: {datetime.now().isoformat()}
            
            Please provide:
            1. Detailed task description
            2. Complete bill of materials with quantities and costs
            3. Time estimate for completion
            4. Total price breakdown
            """
            
            # Create a running input list for tool calling
            input_list = [
                {"role": "system", "content": self.system_prompt},
                {"role": "user", "content": user_input}
            ]
            
            # 1. Prompt the model with tools defined
            response = self.client.responses.create(
                model="gpt-4.1-mini",
                tools=self.tools,
                input=input_list,
            )
            
            # Save function call outputs for subsequent requests
            input_list += response.output
            
            # 2. Check if model made any function calls
            for item in response.output:
                if item.type == "function_call":
                    if item.name == "get_inventory_data":
                        # 3. Execute the function logic for get_inventory_data
                        arguments = json.loads(item.arguments)
                        inventory_data = self.get_inventory_data(arguments.get("query", ""))
                        
                        # 4. Provide function call results to the model
                        input_list.append({
                            "type": "function_call_output",
                            "call_id": item.call_id,
                            "output": json.dumps({
                                "inventory_data": inventory_data
                            })
                        })
            
            # 5. Get final response with structured output after tool calling
            final_response = self.client.responses.parse(
                model="gpt-4.1-mini",
                instructions="Generate a complete quotation using the inventory data provided by the tool.",
                tools=self.tools,
                input=input_list,
                text_format=FinalQuotation,
            )
            
            quotation = final_response.output_parsed
            
            return quotation
        
        except Exception as e:
            raise Exception(f"Error generating quotation: {str(e)}")
    

    def update_quotation(self, user_message: str, update_request: FinalQuotation) -> FinalQuotation:
        try:
            # Create a detailed prompt from the request data
            user_input = f"""
            Generate a professional quotation for the following customer:
            
            Customer Name: {update_request.customer_name}
            Phone: {update_request.phone_number}
            Address: {update_request.address}
            Task Description: {update_request.task_description}
            Bill of Materials: {update_request.bill_of_materials}
            Time: {update_request.time}
            Price: {update_request.price}
            
            Please update the quotation as per user request:
            {user_message}
            """
            
            messages = [
                {"role": "system", "content": self.system_prompt},
                {"role": "user", "content": user_input}
            ]
            
            response = self.client.responses.parse(
                model="gpt-4.1-mini",
                input=messages,
                text_format=FinalQuotation,
            )
            
            quotation = response.output_parsed
            
            return quotation
        
        except Exception as e:
            raise Exception(f"Error generating quotation: {str(e)}")