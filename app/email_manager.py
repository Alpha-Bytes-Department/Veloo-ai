from openai import OpenAI
from typing import List, Dict
import os
import json
from schema import EmailResponse, Email
from dotenv import load_dotenv
from datetime import datetime
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

load_dotenv()

class EmailManager:
    def __init__(self, database=None):
        self.client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
        self.database = database  # Store database reference for inventory queries


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
        

    def generate_custom_email(self, offer: Dict) -> EmailResponse:
        try:
            Customer_name = offer.get("customer_name", "Valued Customer")
            Subject = ""
            Body = ""
            return EmailResponse(
                customer_name=Customer_name,
                email_subject=Subject,
                email_body=Body
            )
        except Exception as e:
            raise Exception(f"Error generating custom mail: {str(e)}")

    def send_email(self, email_request: Email):
        sender_email = os.getenv("SENDER_EMAIL")
        sender_password = os.getenv("SENDER_EMAIL_PASSWORD")
        recipient_email = email_request.to
        subject = email_request.subject
        body = email_request.body

        # Validate credentials
        if not sender_email or not sender_password:
            raise Exception("Email credentials not configured. Please set SENDER_EMAIL and SENDER_EMAIL_PASSWORD in .env file")

        smtp_server = None
        try:
            # Set up the SMTP server
            smtp_server = smtplib.SMTP("smtp.gmail.com", 587)
            smtp_server.starttls()
            smtp_server.login(sender_email, sender_password)

            # Create the email
            msg = MIMEMultipart("alternative")
            msg["From"] = sender_email
            msg["To"] = recipient_email
            msg["Subject"] = subject

            # Add body as both plain text and HTML for better compatibility
            text_part = MIMEText(body, "plain")
            html_part = MIMEText(body.replace('\n', '<br>'), "html")
            msg.attach(text_part)
            msg.attach(html_part)

            # Send the email
            smtp_server.sendmail(sender_email, recipient_email, msg.as_string())
        
        except smtplib.SMTPAuthenticationError:
            raise Exception("Email authentication failed. Please check your email credentials and ensure 'App Passwords' is enabled for Gmail")
        except smtplib.SMTPException as e:
            raise Exception(f"SMTP error occurred: {str(e)}")
        except Exception as e:
            raise Exception(f"Error sending email: {str(e)}")
        finally:
            # Ensure SMTP connection is always closed
            if smtp_server:
                try:
                    smtp_server.quit()
                except:
                    pass