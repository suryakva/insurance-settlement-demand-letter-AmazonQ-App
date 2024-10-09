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
Amazon Q Business is a generative AI–powered assistant that can answer questions, provide summaries, generate content, and securely complete tasks based on data and information in your enterprise systems. It empowers employees to be more creative, data-driven, efficient, prepared, and productive. The proposed chat solution described in this post built with Amazon Q Business with Document Enrichment helps accelerate the review of these documents by quickly summarizing and extracting relevant text and image data from the document while also suggesting possible fraud scenarios guiding the claims specialist to validate the verity of the claims. 
This repo provides CDK code to build the solution. using an AWS Lambda function that calls Amazon Bedrock (Claude 3 Sonnet model) based Document Enrichment feature of Amazon Q Business to index S3 files that contain text and images. 

## High Level Architecture of the solution with Amazon Q Business

<img width="782" alt="image" src="https://github.com/user-attachments/assets/60304ad7-dca1-4257-a1d1-78fb5a839b8a">


## Installation

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

Once the deployment is complete, which can take 15-20 minutes, add your users.


The deployment takes about 140s to finish. What's included in the stack:

1. S3 bucket named `s3withdocumentenrichments-datasources3bucket*`
2. Inside the bucket, we have populated it with data from the [documents folder](https://gitlab.aws.dev/q-business/knowledge-base/-/tree/main/contrib/demo/amazons3-document-enrichment-preextraction/documents?ref_type=heads)
   <br><img src="./images/s3files.png" alt="S3" width="1000"/>
3. Prehook lambda function `S3WithDocumentEnrichmentS-QEnrichmentLambda*` that will trigger Textract for OCR.
4. Amazon Q application with data source `S3WithDocumentEnrichment`
   
### Sync Data source in Amazon Q Business
In your S3 Datasource in Q Business, perform a sync. It will take several additional minutes to index the files.<br><img src="./images/sync_now.png" alt="Sync" width="1000"/>

The web experience is not created in this project. You may preview the web experience and interact with Amazon Q.
<br><img src="./images/webexperience.png" alt="Web Experience" width="1000"/>


## Cleanup

## Conclusion
Conclusion:
As demonstrated in this solution, Amazon Q Business allows insurance claims specialists, developers, IT engineers, and business teams with minimal to no coding skills to quickly create an enterprise grade GenAI based chat application to improve their productivity in minutes. This application can be used across Financial Services, Healthcare, Media, and numerous other industries where documents need to be manually reviewed and processed for claims and other use cases.
Delete the cloudformation stack to cleanup this demo. 

```
cdk destroy
```

**Note**: It will also delete all objects in the S3 Bucket.
