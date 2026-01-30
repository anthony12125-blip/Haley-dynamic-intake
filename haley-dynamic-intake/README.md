# Haley Dynamic Systems - Client Intake Portal

A client-facing intake form that collects project info and uploads files directly to your Google Drive.

## Setup

### 1. Create a Service Account

1. Go to [Google Cloud Console](https://console.cloud.google.com) → IAM & Admin → Service Accounts
2. Click "Create Service Account"
3. Name it something like `drive-uploader`
4. Click "Create and Continue" (skip the optional permissions)
5. Click "Done"
6. Click on your new service account → Keys tab → Add Key → Create new key → JSON
7. Download the JSON file (you'll need the contents)

### 2. Enable the Google Drive API

1. In Google Cloud Console → APIs & Services → Library
2. Search for "Google Drive API"
3. Click Enable

### 3. Create & Share a Drive Folder

1. In Google Drive, create a folder (e.g., "Client Submissions")
2. Right-click → Share
3. Add your service account email (looks like `drive-uploader@your-project.iam.gserviceaccount.com`)
4. Give it "Editor" access
5. Copy the folder ID from the URL:
   ```
   https://drive.google.com/drive/folders/1aBcDeFgHiJkLmNoPqRsTuVwXyZ
                                           └─────── this part ───────┘
   ```

### 4. Set Environment Variables in Cloud Run

After deploying, add these env vars in Cloud Run:

- `GOOGLE_DRIVE_FOLDER_ID`: The folder ID from step 3
- `GOOGLE_APPLICATION_CREDENTIALS_JSON`: The entire contents of the JSON key file from step 1 (paste the whole thing)

## Local Testing

```bash
export GOOGLE_DRIVE_FOLDER_ID="your-folder-id"
export GOOGLE_APPLICATION_CREDENTIALS_JSON='{"type":"service_account",...}'

pip install -r requirements.txt
python app.py
```

Then visit http://localhost:8080

## File Structure

```
/haley-dynamic-intake
├── app.py              # Flask backend
├── Dockerfile          # Container config
├── requirements.txt    # Python dependencies
├── README.md           # This file
└── templates/
    ├── form.html       # Main intake form
    ├── success.html    # Shown after successful submission
    └── error.html      # Shown if something breaks
```

## What Gets Saved

Each submission creates a folder in your Drive named:
```
2025-01-29_14-30-45_Acme_Corp
```

Inside that folder:
- `intake_answers.txt` — All their form answers
- Their uploaded files (logo, photos, etc.)
