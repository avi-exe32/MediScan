import google.genai as genai
import os

os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = 'credentials/gcp-key.json'
client = genai.Client(vertexai=True, project='electvoice', location='us-central1')

try:
    models = client.models.list()
    for m in models:
        print(m.name)
except Exception as e:
    print(e)
