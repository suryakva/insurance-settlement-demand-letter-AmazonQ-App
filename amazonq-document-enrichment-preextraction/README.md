# Amazon Q - Document Enrichment

## Description
This repo provides a demo of using the S3 Connector for Amazon Q Business to index on S3 files that contain text and images of text. The images are indexed using document enrichment.

Amazon Q will fail to extract text natively from images or PDFs that contains images. If you can highlight text in a PDF, then Amazon Q will be able to index it.

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


## Cleanup
Delete the cloudformation stack to cleanup this demo. 

```
cdk destroy
```

**Note**: It will also delete all objects in the S3 Bucket.
