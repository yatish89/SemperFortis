

# Libraries for extracting text from .eml file
from bs4 import BeautifulSoup
from email import policy
from email.parser import BytesParser

# Libraries for genAi 
from flask import Flask, request, jsonify, session
import pandas as pd
from openai import OpenAI
import os
import PyPDF2
from docx import Document
# from app import app
from __init__ import app

key = "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"
client=OpenAI(api_key=key) 

requestTypes = {}

request_types = {
    "Adjustment": ["-"],
    "AU Transfer": ["-"],
    "Closing Notice": ["Reallocation Fees", "Amendment Fees", "Reallocation Principal", "Cashless Roll"],
    "Commitment Change": ["Decrease", "Increase"],
    "Fee Payment": ["Ongoing Fee", "Letter of Credit Fee", "Principal", "Interest", "Principal + Interest"],
    "Money Movement-Inbound": ["Principal + Interest + Fee"],
    "Money Movement - Outbound": ["Timebound", "Foreign Currency"]
}

system_promt = f"""
Task:
You are an AI model trained to process emails received and their attached file (.docx, .txt, .pdf) by Commercial Bank Lending Service teams. Your task is to analyze incoming email content and attachments to accurately interpret the intent, 
classify the request, and extract key information.

Instructions:

  1. Classify Request Types and Sub-Request Types. The Request Types and Sub-Request Types are {request_types} 
  - Read and analyze the email body and attachments.
  - Identify the primary intent and classify the request into predefined Request Type and Sub-Request Type categories.
  - For emails with multiple requests, identify all relevant request types and determine the primary request representing the sender’s main intent.
  - Provide a reasoning for each classification.

  2. Context-Based Data Extraction:
  - Extract configurable fields such as:
      -> Deal Name
      -> Loan Amount
      -> Expiration Date
      -> Customer Name
      -> Reference Number
  - Use contextual clues to extract this data from both the email body and attachments.
  - Apply priority rules where email content takes precedence over attachments for request classification but extract numerical fields from attachments when applicable.

3. Multi-Request Email Handling:
  - Detect multiple requests within a single email and identify all associated request types.
  - Prioritize identifying the primary request even when the email discusses multiple topics.

4. Duplicate Email Detection:
  - Detect and flag duplicate emails arising from:
      -> Multiple replies or forwards within the same thread.
      -> Identical content received through different channels.
  - Prevent redundant service requests by marking duplicates.

5. Customizable Priority Rules:
  - Implement priority-based extraction rules:
      -> Prioritize email body content over attachments for request classification.
      -> Extract numerical or tabular data primarily from attachments.


Expected Output:

  - Request Type: [Identified type]

  - Sub-Request Type: [Identified sub-type]

  - Primary Request: [If applicable in multi-request emails]

  - Extracted Data:
      -> Deal Name: [Extracted value]
      -> Loan Amount: [Extracted value]

  - Expiration Date: [Extracted value]

  - Duplicate Status: [Flag if duplicate]

  - Reasoning: [Detailed explanation for classification and attribute extraction]

"""


def check_duplicate_mail_or_new_request(clean_text):
    checked_prompt = f"Analyse the mail \n\n{clean_text} and judge if that the thank you mail confirming the completion of service request being made previously or completely new service request. Output should be only one word 'YES' if its a confirmation mail or 'NO' if new service request"
    response = client.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=[
            {"role": "user", "content": checked_prompt}
        ],        
    )
    result = response.choices[0].message.content.strip()
   
    return result


def make_prompt_request_for_duplicate_mail(clean_text):
    final_prompt = f"take the data \n\n{clean_text} and identify only the Deal name"
    response = client.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=[
            {"role": "user", "content": final_prompt}
        ],        
    )
    result = response.choices[0].message.content.strip()
    response_data = {
        "status": "success",
        "message": "This is a duplicate request type",
        "result": f"This is a duplicate request type.\n{result}"
    }
    return response_data


def make_prompt_request_for_new_service_request(clean_text):
    """Sends prompt to OpenAI with updated system instructions."""

    final_prompt = f"Analyse the mail \n\n{clean_text} and generates as per prompt \n\n{system_promt}"
      
    print("----------------------------------------------------- LLM Processing Details  -----------------------------------------------------", flush=True)
    
    # Send the request to OpenAI API
    response = client.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=[
            {"role": "user", "content": final_prompt}
        ],
        
    )

    # Get the response content
    result = response.choices[0].message.content.strip()


    print("OpenAI Response:", result)

    print("----------------------------------------------------- Processing Complete  -----------------------------------------------------")

    response_data = {
        "status": "success",
        "message": "LLM processing complete",
        "result": result
    }

    return response_data



# Initial file validation route
@app.route('/validate', methods=['POST'])
def validate_data():
    try:
        print("-------------- BACKEND --------------")
        # Get the uploaded file from the request
        # file = request.files['file']
        if 'file' not in request.files:
            return jsonify({'error': 'No file part in the request'}), 400

        file = next(iter(request.files.values()))  # Get the first uploaded file

        if file.filename == '':
            return jsonify({'error': 'No selected file'}), 400

        # Determine file extension
        file_ext = os.path.splitext(file.filename)[1].lower()

        # Define file paths
        base_path = "C:/Users/Admin/Desktop/Hackathon/SemperFortis/backend/data/"


# ------------------------- Handling .eml File -----------------------------------------------------------------------------

        if file_ext == '.eml':
            # Handle .eml files
            print("-------------- .eml selected --------------")
            file_path = os.path.join(base_path, "file.eml")
            file.save(file_path)
            
            # Open and parse the email
            with open(file_path, "rb") as file:
                msg = BytesParser(policy=policy.default).parse(file)

            # Extract HTML or plain text content
            if msg.is_multipart():
                for part in msg.iter_parts():
                    if part.get_content_type() == "text/html":
                        html_content = part.get_content()
                        break
                    else:
                        html_content = msg.get_body(preferencelist=('plain')).get_content()
            else:
                html_content = msg.get_content()

            # Parse HTML using BeautifulSoup
            soup = BeautifulSoup(html_content, "html.parser")
            clean_text = soup.get_text(separator="\n", strip=True)
            print("Extracted text from .eml : ", clean_text)

# ------------------------- Handling .pdf File -----------------------------------------------------------------------------

        elif file_ext == '.pdf':
            # Handle .pdf files
            print("-------------- .pdf selected --------------")
            file_path = os.path.join(base_path, "file.pdf")
            file.save(file_path)

            # Extract text from PDF
            with open(file_path, "rb") as pdf_file:
                pdf_reader = PyPDF2.PdfReader(pdf_file)
                clean_text = ""
                for page_num in range(len(pdf_reader.pages)):
                    clean_text += pdf_reader.pages[page_num].extract_text()
            print("Extracted text from .pdf: ", clean_text)

# ------------------------- Handling .txt File -----------------------------------------------------------------------------

        elif file_ext == '.txt':
            # Handle .txt files
            print(" -------------- .txt selected --------------")
            file_path = os.path.join(base_path, "file.txt")
            file.save(file_path)

            # Read content from TXT file
            with open(file_path, "r", encoding="utf-8") as txt_file:
                clean_text = txt_file.read()
            print("Extracted text from .txt:", clean_text)

# ------------------------- Handling .docx File -----------------------------------------------------------------------------                

        elif file_ext == '.docx':
            try:
                # Handle .docx (Word) files
                print(" -------------- .docx selected --------------")
                file_path = os.path.join(base_path, "file.docx")
                file.save(file_path)

                # Check if file is saved correctly
                if not os.path.exists(file_path) or os.path.getsize(file_path) == 0:
                    raise Exception("File not saved correctly or is empty.")

                # Extract text from DOCX
                doc = Document(file_path)
                clean_text = "\n".join([para.text for para in doc.paragraphs])

                if clean_text.strip():
                    print("Extracted text from .docx:", clean_text)
                else:
                    print("The file is empty or contains no readable text.")

            except Exception as e:
                print(f"Error processing .docx file: {str(e)}")
                return jsonify({'error': f'Error processing .docx file: {str(e)}'}), 500

 # ------------------------------------------------------------------------------------------------------    
  
        else:
            return jsonify({'error': 'Unsupported file format'}), 400

        # Initial validation (process text with your function)
        response_output = check_duplicate_mail_or_new_request(clean_text)
        print(" Is mail duplicate............................", response_output)

        if response_output=='NO':
            final_response_data = make_prompt_request_for_new_service_request(clean_text)
        elif response_output=='YES':
            final_response_data = make_prompt_request_for_duplicate_mail(clean_text)
        else:
            return jsonify({'error': 'Invalid response type'}), 400

        return jsonify({'result': final_response_data}), 200

    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == "__main__":
  app.run(debug=True, use_reloader=False)