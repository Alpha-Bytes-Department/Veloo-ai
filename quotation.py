from openai import OpenAI
from typing import List, Dict
import os
import json
from schema import QuotationRequest, GeneratedQuotation
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

    def generate_quotation(self, quotation_request: QuotationRequest) -> GeneratedQuotation:
        try:
            # Create a detailed prompt from the request data
            user_message = f"""
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
                {"role": "user", "content": user_message}
            ]
            
            response = self.client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=messages,
                temperature=0.7,
                max_tokens=1500
            )
            
            # Parse the response and create a structured quotation
            ai_response = response.choices[0].message.content
            
            # Create the quotation object
            quotation = GeneratedQuotation(
                customer_name=quotation_request.customer_name,
                phone_number=quotation_request.phone_number,
                address=quotation_request.address,
                task_description=quotation_request.select_task,
                bill_of_materials=ai_response,  # You might want to parse this better
                time=quotation_request.project_start,
                price="To be calculated",  # Extract from AI response
                timestamp=datetime.now()
            )
            
            return quotation
        
        except Exception as e:
            raise Exception(f"Error generating quotation: {str(e)}")
    