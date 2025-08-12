from supabase import create_client, Client
from config import Config
import uuid
from datetime import datetime

class DatabaseService:
    def __init__(self):
        self.supabase: Client = create_client(Config.SUPABASE_URL, Config.SUPABASE_KEY)
    
    def save_document(self, filename, file_path):
        """Save document metadata to database"""
        try:
            result = self.supabase.table('documents').insert({
                'filename': filename,
                'file_path': file_path,
                'processing_status': 'pending'
            }).execute()
            return result.data[0]['id']
        except Exception as e:
            print(f"Database error: {e}")
            return None
    
    def update_document_status(self, doc_id, status, extracted_text=None):
        """Update document processing status"""
        update_data = {'processing_status': status}
        if extracted_text:
            update_data['extracted_text'] = extracted_text
        
        self.supabase.table('documents').update(update_data).eq('id', doc_id).execute()
    
    def save_extracted_data(self, doc_id, field_data):
        """Save extracted field data"""
        for field_name, field_value in field_data.items():
            self.supabase.table('extracted_data').insert({
                'document_id': doc_id,
                'field_name': field_name,
                'field_value': field_value,
                'confidence_score': 0.9  # You can implement actual confidence scoring
            }).execute()
    
    def log_crm_sync(self, doc_id, crm_contact_id, status, error_message=None):
        """Log CRM synchronization"""
        self.supabase.table('crm_sync_log').insert({
            'document_id': doc_id,
            'crm_contact_id': crm_contact_id,
            'sync_status': status,
            'error_message': error_message
        }).execute()