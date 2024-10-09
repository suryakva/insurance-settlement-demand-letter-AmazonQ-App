import json
import os
import logging
import base64
import boto3
import fitz  # PyMuPDF library for PDF processing
import re
import concurrent.futures
import shutil
from urllib.parse import unquote

# Configure logging
logger = logging.getLogger()
logger.setLevel(logging.INFO)

# Initialize S3 clients
s3_client = boto3.client('s3',os.environ['AWS_REGION'])

# Bedrock Runtime client used to invoke and question the models
bedrock_runtime = boto3.client(
    service_name='bedrock-runtime', 
    region_name=os.environ['AWS_REGION']
)


def pdf_to_png(pdf_file, output_folder):
    # Create output folder if it doesn't exist
    if not os.path.exists(output_folder):
        os.makedirs(output_folder)
    
    # Open the PDF file
    pdf_document = fitz.open(pdf_file)
    
    # Iterate through each page
    for page_num in range(len(pdf_document)):
        # Get the page
        page = pdf_document.load_page(page_num)
        
        # Render the page as an image
        pix = page.get_pixmap(alpha=False)
        
        # Save the image as PNG
        pix.save(os.path.join(output_folder, f"page_{page_num+1}.png"))

    # Close the PDF document
    pdf_document.close()

    # Cleanup: Delete PDF file after conversion
    os.remove(pdf_file)


# Function to extract the numeric part of the filename
def extract_page_number(filename):
    match = re.match(r"page_(\d+)\.png", filename)
    if match:
        return int(match.group(1))
    else:
        return float('inf')  # Return a large value for filenames that don't match the pattern


# Function to process each image
def process_image(image_path):
    page_number = int(image_path.split("_")[-1].split(".")[0])
    with open(image_path, 'rb') as f:
        image_data = base64.b64encode(f.read()).decode('utf-8')

    # Construct the JSON body
    body = json.dumps(
        {
            "anthropic_version": "bedrock-2023-05-31",
            "max_tokens": 200000,
            "messages": [
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "image",
                            "source": {
                                "type": "base64",
                                "media_type": "image/png",
                                "data": image_data,
                            },
                        },
                        {   "type": "text", 
                            "text":'''Transcribe the text content from an image page and output in Markdown syntax (not code blocks). Follow these steps:

1. Examine the provided page carefully.

2. Identify all elements present in the page, including headers, body text, footnotes, tables, visualizations, captions, and page numbers, etc.

3. Use markdown syntax to format your output:
    - Headings: # for main, ## for sections, ### for subsections, etc.
    - Lists: * or - for bulleted, 1. 2. 3. for numbered
    - Do not repeat yourself

4. If the element is a visualization
    - Provide a detailed description in natural language
    - Do not transcribe text in the visualization after providing the description

5. If the element is a table
    - Create a markdown table, ensuring every row has the same number of columns
    - Maintain cell alignment as closely as possible
    - Do not split a table into multiple tables
    - If a merged cell spans multiple rows or columns, place the text in the top-left cell and output ' ' for other
    - Use | for column separators, |-|-| for header row separators
    - If a cell has multiple items, list them in separate rows
    - If the table contains sub-headers, separate the sub-headers from the headers in another row

6. If the element is a paragraph
    - Transcribe each text element precisely as it appears

7. If the element is a header, footer, footnote, page number
    - Transcribe each text element precisely as it appears

Output Example:

A bar chart showing annual sales figures, with the y-axis labeled "Sales ($Million)" and the x-axis labeled "Year". The chart has bars for 2018 ($12M), 2019 ($18M), 2020 ($8M), and 2021 ($22M).
Figure 3: This chart shows annual sales in millions. The year 2020 was significantly down due to the COVID-19 pandemic.

# Annual Report

## Financial Highlights

* Revenue: $40M
* Profit: $12M
* EPS: $1.25


| | Year Ended December 31, | |
| | 2021 | 2022 |
|-|-|-|
| Cash provided by (used in): | | |
| Operating activities | $ 46,327 | $ 46,752 |
| Investing activities | (58,154) | (37,601) |
| Financing activities | 6,291 | 9,718 |

Here is the image.'''
                            
                            
                        },
                    ],
                }
            ],
        }
    )

    # Invoke the model (you need to replace this with your actual model invocation)
    response = bedrock_runtime.invoke_model(
        modelId="anthropic.claude-3-sonnet-20240229-v1:0",
        body=body
    )

    response_body = json.loads(response.get("body").read())

    # Process the response (replace this with actual processing of response)
    logger.info("Data : %s", response_body)

    # Return the processed text
    content_text = response_body["content"][0]["text"]
    return page_number, content_text



def lambda_handler(event, context):
    # Retrieve the S3 bucket and key from the event
    source_bucket = event.get("s3Bucket")
    # Get the value of "metadata" key name or item from the given event input
    metadata = event.get("metadata")

    source_key = ""
    for attribute in metadata["attributes"]:
        if attribute['name'] == '_source_uri':
            _, _, source_key = attribute['value']['stringValue'].partition(
                's3.amazonaws.com/')
            source_key = unquote(source_key)
            break
    
    
    # Download the PDF file from the source bucket to /tmp directory
    pdf_file = '/tmp/' + os.path.basename(source_key)
    s3_client.download_file(source_bucket, source_key, pdf_file)
    
    # Output folder for PNG files
    output_folder = f'/tmp/png-output-{context.aws_request_id}/'
    
    # Convert the PDF to PNG files
    pdf_to_png(pdf_file, output_folder)
    
    # Output text file path
    output_file_path = f'/tmp/output-text-file-{context.aws_request_id}.txt'

    # Process each PNG file in the folder
    with concurrent.futures.ThreadPoolExecutor() as executor:
        # Get a list of PNG file paths
        png_files = [os.path.join(output_folder, filename) for filename in os.listdir(output_folder) if filename.endswith(".png")]

        # Process images and gather results
        results = executor.map(process_image, png_files)

        # Sort results by page number
        sorted_results = sorted(results, key=lambda x: x[0])

        # Write output to text file
        with open(output_file_path, "a") as text_file:
            for page_number, content_text in sorted_results:
                text_file.write(f"Page Number: {page_number}\n")
                formatted_text = "\n".join(line.strip() for line in content_text.split("\n"))
                text_file.write(formatted_text + "\n\n")

    # Upload the output text file to the target S3 bucket
    target_key = f"pre-extraction/{source_key}.txt"
    # target_key = source_key + '.txt'
    print("target_key is :"+target_key)
    
    # s3_client.upload_file(output_file_path, target_bucket, target_key)
    s3_client.upload_file(output_file_path, source_bucket, target_key)

    logger.info("Processing completed.")
    
    # Cleanup: Delete PNG files after processing
    shutil.rmtree(output_folder)

    return {
        # 'statusCode': 200,
        # 'body': json.dumps('Hello from Lambda!')
        "version": "v0",
        "s3ObjectKey": target_key,
        "metadataUpdates": []
    }
 