from google.cloud import vision
import re

class OCRService:
    def __init__(self):
        self.client = vision.ImageAnnotatorClient()
    
    def extract_text_from_image(self, image_path):
        """Extract text from image using Google Cloud Vision"""
        try:
            with open(image_path, 'rb') as image_file:
                content = image_file.read()
            
            image = vision.Image(content=content)
            response = self.client.text_detection(image=image)
            
            if response.error.message:
                raise Exception(f"OCR Error: {response.error.message}")
            
            texts = response.text_annotations
            if texts:
                return texts[0].description
            return ""
        
        except Exception as e:
            print(f"OCR Service error: {e}")
            return None
    
    def parse_contact_data(self, text):
        """Parse extracted text to find contact information"""
        contact_data = {}
        
        # Email regex
        email_pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
        emails = re.findall(email_pattern, text)
        if emails:
            contact_data['email'] = emails[0]
        
        # Phone regex
        # A more specific regex to capture common phone formats and avoid matching random numbers.
        phone_pattern = r'(?:\+?\d{1,3}[-.\s]?)?\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}'
        phones = re.findall(phone_pattern, text)
        if phones:
            # Clean up the found phone number by removing non-digit characters
            contact_data['phone'] = re.sub(r'\D', '', phones[0])
        
        # Name extraction (basic - you can improve this)
        lines = text.split('\n')
        for line in lines:
            if len(line.split()) >= 2 and not any(char.isdigit() for char in line):
                contact_data['name'] = line.strip()
                break
        
        # Company extraction (look for common indicators)
        company_indicators = ['inc', 'llc', 'corp', 'ltd', 'company', 'co.']
        for line in lines:
            if any(indicator in line.lower() for indicator in company_indicators):
                contact_data['company'] = line.strip()
                break
        
        return contact_data