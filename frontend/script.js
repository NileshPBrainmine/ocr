class DocumentProcessor {
    constructor() {
        this.baseURL = 'http://localhost:5000/api';
        this.initializeEventListeners();
        this.loadHistory();
    }

    initializeEventListeners() {
        const uploadArea = document.getElementById('uploadArea');
        const fileInput = document.getElementById('fileInput');

        // Drag and drop events
        uploadArea.addEventListener('dragover', this.handleDragOver.bind(this));
        uploadArea.addEventListener('dragleave', this.handleDragLeave.bind(this));
        uploadArea.addEventListener('drop', this.handleDrop.bind(this));
        
        // File input change
        fileInput.addEventListener('change', this.handleFileSelect.bind(this));
        
        // Click to upload
        uploadArea.addEventListener('click', () => fileInput.click());
    }

    handleDragOver(e) {
        e.preventDefault();
        document.getElementById('uploadArea').classList.add('dragover');
    }

    handleDragLeave(e) {
        e.preventDefault();
        document.getElementById('uploadArea').classList.remove('dragover');
    }

    handleDrop(e) {
        e.preventDefault();
        document.getElementById('uploadArea').classList.remove('dragover');
        const files = Array.from(e.dataTransfer.files);
        this.processFiles(files);
    }

    handleFileSelect(e) {
        const files = Array.from(e.target.files);
        this.processFiles(files);
    }

    async processFiles(files) {
        for (const file of files) {
            await this.processFile(file);
        }
    }

    async processFile(file) {
        try {
            // Show processing section
            this.showProcessingSection();
            this.updateProcessingStatus('Uploading file...');

            // Upload file
            const documentId = await this.uploadFile(file);
            if (!documentId) {
                throw new Error('File upload failed');
            }

            this.updateProcessingStatus('Extracting text from document...');

            // Process document
            const result = await this.processDocument(documentId);
            
            // Show results
            this.showResults(result);
            
            // Reload history
            this.loadHistory();

        } catch (error) {
            console.error('Processing error:', error);
            this.showError(error.message);
        } finally {
            // Hide processing section after a delay
            setTimeout(() => {
                document.getElementById('processingSection').style.display = 'none';
            }, 2000);
        }
    }

    async uploadFile(file) {
        const formData = new FormData();
        formData.append('file', file);

        const response = await fetch(`${this.baseURL}/upload`, {
            method: 'POST',
            body: formData
        });

        if (!response.ok) {
            throw new Error(`Upload failed: ${response.statusText}`);
        }

        const result = await response.json();
        return result.document_id;
    }

    async processDocument(documentId) {
        const response = await fetch(`${this.baseURL}/process/${documentId}`, {
            method: 'POST'
        });

        if (!response.ok) {
            throw new Error(`Processing failed: ${response.statusText}`);
        }

        return await response.json();
    }

    showProcessingSection() {
        document.getElementById('processingSection').style.display = 'block';
        document.getElementById('resultsSection').style.display = 'none';
    }

    updateProcessingStatus(status) {
        document.getElementById('processingStatus').textContent = status;
    }

    showResults(result) {
        const resultsSection = document.getElementById('resultsSection');
        const resultsGrid = document.getElementById('resultsGrid');
        
        resultsGrid.innerHTML = '';
        
        // Create result card
        const resultCard = document.createElement('div');
        resultCard.className = 'result-card';
        
        const cardHeader = document.createElement('h3');
        cardHeader.textContent = 'Extracted Contact Information';
        resultCard.appendChild(cardHeader);

        // Display extracted data
        if (result.extracted_data) {
            Object.entries(result.extracted_data).forEach(([key, value]) => {
                const dataItem = document.createElement('div');
                dataItem.className = 'data-item';
                
                const label = document.createElement('span');
                label.className = 'data-label';
                label.textContent = key;
                
                const valueSpan = document.createElement('span');
                valueSpan.className = 'data-value';
                valueSpan.textContent = value;
                
                dataItem.appendChild(label);
                dataItem.appendChild(valueSpan);
                resultCard.appendChild(dataItem);
            });
        }

        // CRM sync status
        const statusItem = document.createElement('div');
        statusItem.className = 'data-item';
        
        const statusLabel = document.createElement('span');
        statusLabel.className = 'data-label';
        statusLabel.textContent = 'CRM Sync';
        
        const statusBadge = document.createElement('span');
        statusBadge.className = `status-badge ${result.crm_contact_id ? 'status-success' : 'status-failed'}`;
        statusBadge.textContent = result.crm_contact_id ? 'Success' : 'Failed';
        
        statusItem.appendChild(statusLabel);
        statusItem.appendChild(statusBadge);
        resultCard.appendChild(statusItem);

        if (result.crm_contact_id) {
            const crmIdItem = document.createElement('div');
            crmIdItem.className = 'data-item';
            
            const crmLabel = document.createElement('span');
            crmLabel.className = 'data-label';
            crmLabel.textContent = 'CRM Contact ID';
            
            const crmValue = document.createElement('span');
            crmValue.className = 'data-value';
            crmValue.textContent = result.crm_contact_id;
            
            crmIdItem.appendChild(crmLabel);
            crmIdItem.appendChild(crmValue);
            resultCard.appendChild(crmIdItem);
        }

        resultsGrid.appendChild(resultCard);
        resultsSection.style.display = 'block';
    }

    showError(message) {
        const resultsSection = document.getElementById('resultsSection');
        const resultsGrid = document.getElementById('resultsGrid');
        
        resultsGrid.innerHTML = `
            <div class="result-card">
                <h3 style="color: #dc3545;">Error</h3>
                <p style="color: #666;">${message}</p>
            </div>
        `;
        
        resultsSection.style.display = 'block';
    }

    async loadHistory() {
        try {
            const response = await fetch(`${this.baseURL}/documents`);
            if (!response.ok) return;

            const documents = await response.json();
            this.displayHistory(documents);
        } catch (error) {
            console.error('Failed to load history:', error);
        }
    }

    displayHistory(documents) {
        const historyList = document.getElementById('historyList');
        historyList.innerHTML = '';

        documents.forEach(doc => {
            const historyItem = document.createElement('div');
            historyItem.className = 'history-item';
            
            const date = new Date(doc.created_at).toLocaleDateString('en-US', {
                year: 'numeric',
                month: 'short',
                day: 'numeric',
                hour: '2-digit',
                minute: '2-digit'
            });

            historyItem.innerHTML = `
                <div class="history-header">
                    <span class="history-filename">${doc.filename}</span>
                    <span class="history-date">${date}</span>
                </div>
                <div class="history-status">
                    <span class="status-badge status-${doc.processing_status}">
                        ${doc.processing_status}
                    </span>
                </div>
            `;

            historyList.appendChild(historyItem);
        });
    }
}

// Initialize the application
document.addEventListener('DOMContentLoaded', () => {
    new DocumentProcessor();
});