import requests
from config import Config

class HubSpotCRMService:
    def __init__(self):
        self.api_key = Config.HUBSPOT_API_KEY
        self.base_url = "https://api.hubapi.com"
    
    def create_contact(self, contact_data):
        """Create contact in HubSpot CRM"""
        try:
            url = f"{self.base_url}/crm/v3/objects/contacts"
            headers = {
                'Authorization': f'Bearer {self.api_key}',
                'Content-Type': 'application/json'
            }
            
            # Map our data to HubSpot properties
            hubspot_data = {
                "properties": {}
            }
            
            if 'email' in contact_data:
                hubspot_data['properties']['email'] = contact_data['email']
            if 'name' in contact_data:
                # Split name into first and last
                name_parts = contact_data['name'].split()
                hubspot_data['properties']['firstname'] = name_parts[0]
                if len(name_parts) > 1:
                    hubspot_data['properties']['lastname'] = ' '.join(name_parts[1:])
            if 'phone' in contact_data:
                hubspot_data['properties']['phone'] = contact_data['phone']
            if 'company' in contact_data:
                hubspot_data['properties']['company'] = contact_data['company']
            
            response = requests.post(url, json=hubspot_data, headers=headers)
            
            if response.status_code == 201:
                return response.json()['id']
            else:
                print(f"CRM Error: {response.status_code} - {response.text}")
                return None
        
        except Exception as e:
            print(f"CRM Service error: {e}")
            return None