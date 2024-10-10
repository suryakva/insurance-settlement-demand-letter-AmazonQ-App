# Settlement Demand Letter Review with Amazon Q Document Enrichment

## Introduction
A settlement demand letter is a formal request for compensation that is sent by an individual (the claimant) or their attorney to the party responsible (the insured) for an injury or their insurance company. It is often used in personal injury cases (from Automotive or other incidents) to help victims get compensation faster than a legal settlement.
A settlement demand letter typically includes:
- Incident details: A description of the accident, including the date, time, and location
- Injuries: A description of the injuries and their effects on the victim's daily life
- Treatment: A timeline of treatment, including the type of treatment and recovery progress
- Medical bills: A list of medical bills and lost income statements
- Liability: An explanation of why the policyholder/insured is liable for the victim's injuries
- Compensation: The amount of compensation demanded from the insurance company

However, there is no fixed format for these letters and are often unstructured with claim details mentioned across different sections of the document. Insurance claims specialists spend significant amount of time manually reviewing the settlement demand letter documents and subsequently perform background verification for each of the claims from third party sources. Also too often these letters have fraudulent, fabricated or exaggerated information about the incident and the declared damages to individuals and property. 

## Solution Overview
Amazon Q Business is a generative AI–powered assistant that can answer questions, provide summaries, generate content, and securely complete tasks based on data and information in your enterprise systems. It empowers employees to be more creative, data-driven, efficient, prepared, and productive. 
The proposed chat solution described in this post built with Amazon Q Business with Document Enrichment, helps accelerate the review of these documents by quickly summarizing and extracting relevant text and image data from the document while also suggesting possible fraud scenarios, guiding the claims specialist to validate the verity of the claims. This repo provides CDK code to build the entire solution. Once the infrastructure is deployed with the CDK stack, add an Identity Center user to the deployed Q Application and run a Sync of the S3 Data Source. The Sync job passes the documents in S3 to the Lambda function which converts the pages from PDF to PNG files and makes an API call to Claude 3 Sonnet using Bedrock to transcribe images to text. The Bedrock text response is parsed and stored as a text file in the "pre-extraction" folder within the same S3 bucket for Amazon Q app to index the text content and respond to user queries in the Q Application.  


## High Level Architecture of the solution with Amazon Q Business

<img width="818" alt="image" src="https://github.com/user-attachments/assets/ea15bad2-ce5d-4885-84fa-f52e95ed3f5e">


## Solution Deployment

### Prerequisite Step
This solution uses AWS IAM Identity Center to grant access to users to the Amazon Q application. Create a user for this application in IAM Identity Center by referring to the steps [here](https://docs.aws.amazon.com/amazonq/latest/qbusiness-ug/create-application.html).

### Deploy the stack
We use [AWS Cloud Development Kit (CDK)](https://docs.aws.amazon.com/cdk/v2/guide/home.html) to deploy the demo. If you haven't used CDK in the past, it will be helpful to quickly go through [getting started with CDK](https://docs.aws.amazon.com/cdk/v2/guide/getting_started.html)

The `cdk.json` file tells the CDK Toolkit how to execute your app.

This project is set up like a standard Python project.  The initialization process also creates
a virtualenv within this project, stored under the .venv directory.  To create the virtualenv
it assumes that there is a `python3` executable in your path with access to the `venv` package.
If for any reason the automatic creation of the virtualenv fails, you can create the virtualenv
manually once the init process completes.

To manually create a virtualenv on MacOS and Linux:

```
python3 -m venv .venv
```

After the init process completes and the virtualenv is created, you can use the following
step to activate your virtualenv.

```
source .venv/bin/activate
```

If you are a Windows platform, you would activate the virtualenv like this:

```
.venv\Scripts\activate.bat
```

Once the virtualenv is activated, you can install the required dependencies.

```
pip install -r requirements.txt
```

At this point you can now synthesize the CloudFormation template for this code.

```
cdk synth
```

To deploy the stack, you can do:

```
cdk deploy
```

The deployment could take 15-20 minutes to complete.


## Review and Test the Solution

### Review the Settlement Document:

<img width="612" alt="image" src="https://github.com/user-attachments/assets/b0cf23a4-c364-44a7-958b-a1c36a9edd26">

<img width="613" alt="image" src="https://github.com/user-attachments/assets/10b84e85-ccbd-422c-9cd8-377ef6308bd9">

<img width="617" alt="image" src="https://github.com/user-attachments/assets/8f9fa6e2-3cac-4527-b707-05f16a632592">

<img width="615" alt="image" src="https://github.com/user-attachments/assets/f8075a7b-7fb6-4380-92c3-49b88ad01eb2">


### Test the Amazon Q Application:

<img width="1426" alt="image" src="https://github.com/user-attachments/assets/8235a4d2-c5fb-4de7-af04-ed46ac2cbc4b">

<img width="1425" alt="image" src="https://github.com/user-attachments/assets/4d6d0469-3a60-4bae-ba42-97e291c7fb89">

<img width="1426" alt="image" src="https://github.com/user-attachments/assets/7dc6811f-2a57-4097-bdd4-ad0a41599448">

<img width="1428" alt="image" src="https://github.com/user-attachments/assets/681f7d43-5971-418d-8e4d-c7ff721bf273">

<img width="1427" alt="image" src="https://github.com/user-attachments/assets/a7edbe36-9526-4ab8-8e6f-91cc9af2abe4">


## Cleanup
Delete the cloudformation stack to cleanup this demo. 

```
cdk destroy
```

**Note**: All the objects in the S3 Bucket will also be deleted.

## Conclusion
As demonstrated in this solution, Amazon Q Business allows insurance claims specialists, developers, IT engineers, and business teams to quickly create an enterprise grade GenAI based chat application to improve their productivity in minutes. This application can be used across Financial Services, Healthcare, Media, and numerous other industries where documents need to be manually reviewed and processed for claims and other use cases.
