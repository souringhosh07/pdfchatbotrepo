import os
import openai
from flask import Flask, request, jsonify
from flask_cors import CORS
from PyPDF2 import PdfFileReader
from io import BytesIO
from azure.storage.blob import BlobServiceClient, BlobClient, ContainerClient
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)
CORS(app)

# Set up OpenAI API key
openai.api_key = os.getenv("sk-None-q1KvsbUfSjSSNmP71ZYwT3BlbkFJG1UEEFY1QiN9nQvvZ3bI")

# Azure Blob Storage setup
AZURE_CONNECTION_STRING = os.getenv("AZURE_CONNECTION_STRING")
AZURE_CONTAINER_NAME = os.getenv("AZURE_CONTAINER_NAME")
blob_service_client = BlobServiceClient.from_connection_string(AZURE_CONNECTION_STRING)

def extract_text_from_pdf(file):
    reader = PdfFileReader(file)
    text = ""
    for page_num in range(reader.numPages):
        text += reader.getPage(page_num).extractText()
    return text

@app.route('/upload', methods=['POST'])
def upload_files():
    files = request.files.getlist('files')
    combined_text = ""
    
    for file in files:
        combined_text += extract_text_from_pdf(file)
    
    # Save combined text to a blob for future access
    blob_client = blob_service_client.get_blob_client(container=AZURE_CONTAINER_NAME, blob="combined_text.txt")
    blob_client.upload_blob(combined_text, overwrite=True)
    
    return jsonify({"message": "Files uploaded and processed successfully!"})

@app.route('/ask', methods=['POST'])
def ask_question():
    data = request.get_json()
    question = data.get('question')

    # Retrieve the combined text from the blob
    blob_client = blob_service_client.get_blob_client(container=AZURE_CONTAINER_NAME, blob="combined_text.txt")
    combined_text = blob_client.download_blob().content_as_text()

    response = openai.Completion.create(
        engine="davinci",
        prompt=f"{combined_text}\n\nQ: {question}\nA:",
        max_tokens=150,
        n=1,
        stop=None,
        temperature=0.7,
    )

    answer = response.choices[0].text.strip()
    return jsonify({"answer": answer})

if __name__ == '__main__':
    app.run(debug=True)
