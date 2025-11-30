import requests

# Upload file
with open('uploads/Sample NDA.pdf', 'rb') as f:
    files = {'files': f}
    response = requests.post('http://localhost:8000/ingest', files=files)
    print(response.json())