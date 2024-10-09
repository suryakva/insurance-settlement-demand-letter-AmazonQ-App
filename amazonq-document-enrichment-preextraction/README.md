# Amazon Q with Document Enrichment

[:material-gitlab: View code](https://gitlab.aws.dev/q-business/knowledge-base/-/tree/main/contrib/demo/amazons3-document-enrichment-preextraction?ref_type=heads){ .md-button }

## Description
This repo provides a demo of using the S3 Connector for Amazon Q Business to index on S3 files that contain text and images of text. The images are indexed using document enrichment.

Amazon Q will fail to extract text natively from images or PDFs that contains images. If you can highlight text in a PDF, then Amazon Q will be able to index it.

In this demo, PDFs for various industrial equipment will be indexed. This includes a Mill and a Lathe from [Haas](https://www.haascnc.com/owners/Service/operators-manual.html). In addition, scanned Standard Operating Procedures (SOP) will also be indexed with the help of document enrichment and Amazon Textract.

## Demo Video
This video walks through the demo script of this s3 connector.

[Video Link](https://broadcast.amazon.com/videos/1033675)

## Installation

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


## Live Demo
The link below provides access to a live deployment of this demo. Login with the following credentials to access the Amazon Q Web Experience. The demo script is provided

**IN DEVELOPMENT**

## Demo Script
If you intend to install and demo this on your own account, here are some example questions that may be asked. It highlights how Amazon Q can help operations: 1/ quickly find context or information for the machines they are operating; 2/ locate procedures or instructions. Feel free to add more documents to the S3 Bucket and perform a full sync.

1) With Amazon Q Business, you can index on various documents for vendor manuals. This includes several document types seen [here](https://docs.aws.amazon.com/amazonq/latest/business-use-dg/doc-types.html). This question is an example where an operator encounters a high alarm with little context and can ask for more information. <br><img src="./images/high_alarm.png" alt="High Alarm" width="1000"/>

2) Instructions or guidance can be provided as well. This may be steps to capture error reports, how to perform Lock out Tag Out, etc. Amazon Q Business can locate these instructions within the vendor manual. <br><img src="./images/error_report.png" alt="Error Report" width="1000"/>

3) In some cases, files may be scanned and not converted to text with OCR. Amazon Q Business will not perform OCR natively on images. To accomplish this, Amazon Q Business provides a capability called Document Enrichment. This process invokes a Lambda function where you can use OCR services like Amazon Textract to extract the text from the image. Here is a question locating the PPE requirements in an inspection checklist form.<br><img src="./images/inspection_checklist.png" alt="Inspection" width="1000"/>

4) Ask Q to analyze the Mill Machine manual and correlate with the checklist for preventative maintenance to see what may be missing. This really highlights the power of Generative AI across multiple documents <br><img src="./images/analyze_docs.png" alt="Analysis" width="1000"/>

## Roadmap
- Provide a live link to this demo

## Cleanup
Delete the cloudformation stack to cleanup this demo. 

```
cdk destroy
```

**Note**: It will delete all objects in the S3 Bucket.
