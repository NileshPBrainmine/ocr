from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
import os
import uuid
from werkzeug.utils import secure_filename

from config import Config
from services.database_service import DatabaseService
from services.ocr_service import OCRService
from services.crm_service import HubSpotCRMService

app = Flask(__name__)
app.config.from_object(Config)
CORS(app)  # Enable CORS for all routes and all origins

# Initialize services
db_service = DatabaseService()
ocr_service = OCRService()
crm_service = HubSpotCRMService()

# Ensure upload directory exists
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'pdf'}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@app.route('/')
def index():
    return send_from_directory('../frontend', 'index.html')

@app.route('/<path:path>')
def serve_static(path):
    return send_from_directory('../frontend', path)

@app.route('/api/upload', methods=['POST'])
def upload_file():
    try:
        if 'file' not in request.files:
            return jsonify({'error': 'No file provided'}), 400
        
        file = request.files['file']
        if file.filename == '':
            return jsonify({'error': 'No file selected'}), 400
        
        if file and allowed_file(file.filename):
            # Generate unique filename
            filename = secure_filename(file.filename)
            unique_filename = f"{uuid.uuid4()}_{filename}"
            file_path = os.path.join(app.config['UPLOAD_FOLDER'], unique_filename)
            
            # Save file
            file.save(file_path)
            
            # Save to database
            doc_id = db_service.save_document(filename, file_path)
            if not doc_id:
                return jsonify({'error': 'Database error'}), 500
            
            return jsonify({
                'message': 'File uploaded successfully',
                'document_id': doc_id
            }), 200
        
        return jsonify({'error': 'Invalid file type'}), 400
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/process/<doc_id>', methods=['POST'])
def process_document(doc_id):
    try:
        # Get document info from database
        doc_result = db_service.supabase.table('documents').select('*').eq('id', doc_id).execute()
        if not doc_result.data:
            return jsonify({'error': 'Document not found'}), 404
        
        doc = doc_result.data[0]
        file_path = doc['file_path']
        
        # Update status to processing
        db_service.update_document_status(doc_id, 'processing')
        
        # Extract text using OCR
        extracted_text = ocr_service.extract_text_from_image(file_path)
        if not extracted_text:
            db_service.update_document_status(doc_id, 'failed')
            return jsonify({'error': 'OCR processing failed'}), 500
        
        # Parse contact data
        contact_data = ocr_service.parse_contact_data(extracted_text)
        
        # Save extracted data to database
        db_service.save_extracted_data(doc_id, contact_data)
        
        # Create contact in CRM
        crm_contact_id = crm_service.create_contact(contact_data)
        
        if crm_contact_id:
            db_service.log_crm_sync(doc_id, crm_contact_id, 'success')
            db_service.update_document_status(doc_id, 'completed', extracted_text)
            
            return jsonify({
                'message': 'Document processed successfully',
                'extracted_data': contact_data,
                'crm_contact_id': crm_contact_id
            }), 200
        else:
            db_service.log_crm_sync(doc_id, None, 'failed', 'CRM API error')
            db_service.update_document_status(doc_id, 'completed', extracted_text)
            
            return jsonify({
                'message': 'OCR completed but CRM sync failed',
                'extracted_data': contact_data
            }), 200
    
    except Exception as e:
        db_service.update_document_status(doc_id, 'failed')
        return jsonify({'error': str(e)}), 500

@app.route('/api/documents', methods=['GET'])
def get_documents():
    try:
        result = db_service.supabase.table('documents').select('*').order('created_at', desc=True).execute()
        return jsonify(result.data), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True, port=5000)