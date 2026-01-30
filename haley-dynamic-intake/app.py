import os
import tempfile
from datetime import datetime
from flask import Flask, render_template, request
from google.cloud import storage

app = Flask(__name__)
app.config['MAX_CONTENT_LENGTH'] = 100 * 1024 * 1024  # 100MB max upload

def upload_to_gcs(bucket_name, source_file, destination_blob_name):
    """Upload a file to Google Cloud Storage."""
    client = storage.Client()
    bucket = client.bucket(bucket_name)
    blob = bucket.blob(destination_blob_name)
    blob.upload_from_filename(source_file)

@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        try:
            bucket_name = os.environ.get('GCS_BUCKET_NAME')
            if not bucket_name:
                raise ValueError("GCS_BUCKET_NAME not set")

            # Create a folder path for this submission
            timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
            client_name = request.form.get('business_name', 'Unknown').replace(' ', '_')
            folder_path = f"{timestamp}_{client_name}"

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
            
            upload_to_gcs(bucket_name, temp_answers_path, f"{folder_path}/intake_answers.txt")
            os.unlink(temp_answers_path)

            # Upload all photos
            if 'photos' in request.files:
                files = request.files.getlist('photos')
                for file in files:
                    if file.filename != '':
                        with tempfile.NamedTemporaryFile(delete=False) as tmp:
                            file.save(tmp.name)
                            temp_path = tmp.name
                        
                        upload_to_gcs(bucket_name, temp_path, f"{folder_path}/{file.filename}")
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
