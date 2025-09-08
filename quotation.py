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
        self.system_prompt = """You are a professional quotation generator assistant. 
        Generate detailed construction/service quotations based on customer requirements.
        Provide comprehensive bill of materials, time estimates, and accurate pricing.
        Format your response as a structured quotation with all required fields."""

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
            
            Please provide:
            1. Detailed task description
            2. Complete bill of materials with quantities and costs
            3. Time estimate for completion
            4. Total price breakdown
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