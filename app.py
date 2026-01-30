import os
import json
import tempfile
from datetime import datetime
from flask import Flask, render_template, request
from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload

app = Flask(__name__)
app.config['MAX_CONTENT_LENGTH'] = 100 * 1024 * 1024  # 100MB max upload

def get_drive_service():
    """Initialize Google Drive API service."""
    creds_json = os.environ.get('GOOGLE_APPLICATION_CREDENTIALS_JSON')
    if not creds_json:
        raise ValueError("GOOGLE_APPLICATION_CREDENTIALS_JSON not set")
    
    creds_dict = json.loads(creds_json)
    creds = service_account.Credentials.from_service_account_info(
        creds_dict,
        scopes=['https://www.googleapis.com/auth/drive.file']
    )
    return build('drive', 'v3', credentials=creds)

def create_folder(service, name, parent_id):
    """Create a folder in Google Drive."""
    folder_metadata = {
        'name': name,
        'mimeType': 'application/vnd.google-apps.folder',
        'parents': [parent_id]
    }
    folder = service.files().create(body=folder_metadata, fields='id').execute()
    return folder.get('id')

def upload_file(service, filepath, filename, folder_id, mimetype='application/octet-stream'):
    """Upload a file to Google Drive."""
    file_metadata = {
        'name': filename,
        'parents': [folder_id]
    }
    media = MediaFileUpload(filepath, mimetype=mimetype, resumable=True)
    service.files().create(body=file_metadata, media_body=media, fields='id').execute()

@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        try:
            # Get Drive service and folder ID
            service = get_drive_service()
            parent_folder_id = os.environ.get('GOOGLE_DRIVE_FOLDER_ID')
            if not parent_folder_id:
                raise ValueError("GOOGLE_DRIVE_FOLDER_ID not set")

            # Create a subfolder for this submission
            timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
            client_name = request.form.get('business_name', 'Unknown').replace(' ', '_')
            folder_name = f"{timestamp}_{client_name}"
            submission_folder_id = create_folder(service, folder_name, parent_folder_id)

            # Build the questionnaire answers
            answers = []
            answers.append("=" * 50)
            answers.append("HALEY DYNAMIC SYSTEMS - CLIENT INTAKE")
            answers.append("=" * 50)
            answers.append(f"Submitted: {datetime.now().strftime('%B %d, %Y at %I:%M %p')}")
            answers.append("")
            
            field_labels = {
                'business_name': 'Business Name',
                'contact_name': 'Contact Name',
                'contact_email': 'Email',
                'contact_phone': 'Phone',
                'website_url': 'Current Website',
                'elevator_pitch': 'What does your business do?',
                'services': 'Top Services/Products',
                'audience': 'Target Audience',
                'competitors': 'Competitors or Inspiration',
                'style_adjectives': 'Style Adjectives',
                'colors': 'Preferred Colors',
                'pages_needed': 'Pages Needed',
                'features': 'Special Features',
                'deadline': 'Deadline',
                'additional_notes': 'Additional Notes'
            }
            
            for key, value in request.form.items():
                label = field_labels.get(key, key.replace('_', ' ').title())
                answers.append(f"{label}:")
                answers.append(f"  {value}")
                answers.append("")

            # Save answers to temp file and upload
            with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f:
                f.write('\n'.join(answers))
                temp_answers_path = f.name
            
            upload_file(service, temp_answers_path, 'intake_answers.txt', submission_folder_id, 'text/plain')
            os.unlink(temp_answers_path)

            # Upload all photos
            if 'photos' in request.files:
                files = request.files.getlist('photos')
                for file in files:
                    if file.filename != '':
                        # Save to temp file
                        with tempfile.NamedTemporaryFile(delete=False) as tmp:
                            file.save(tmp.name)
                            temp_path = tmp.name
                        
                        # Determine mimetype
                        mimetype = file.content_type or 'application/octet-stream'
                        upload_file(service, temp_path, file.filename, submission_folder_id, mimetype)
                        os.unlink(temp_path)

            return render_template('success.html', business_name=request.form.get('business_name', 'there'))

        except Exception as e:
            print(f"Error: {e}")
            return render_template('error.html', error=str(e)), 500

    return render_template('form.html')

@app.route('/health')
def health():
    return 'ok', 200

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 8080))
    app.run(host='0.0.0.0', port=port)
