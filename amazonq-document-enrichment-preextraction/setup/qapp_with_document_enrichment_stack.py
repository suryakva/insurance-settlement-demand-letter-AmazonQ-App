import aws_cdk as cdk
from constructs import Construct
from aws_cdk import (
    Duration,
    Stack,
    aws_s3 as s3,
    aws_s3_deployment as s3_deploy,
    aws_lambda as _lambda,
    aws_iam as iam,
    custom_resources as cr,
)

REGION = cdk.Aws.REGION
ACCOUNT_ID = cdk.Aws.ACCOUNT_ID
Q_APPLICATION_NAME = "QAppWithDocumentEnrichment"
Q_APPLICATION_DESCRIPTION = "Application configured with an S3 data source that has prehook document enrichment"
Q_APPLICATION_WELCOME_MESSAGE = "In this demo, PDFs with text images will be indexed"
DATASOURCE_NAME = "demandletter-s3-data-source-12345"
DATASOURCE_DESCRIPTION = "demandletter-s3-data-source"

class QAppWithDocumentEnrichmentStack(Stack):

    def __init__(self, scope: Construct, construct_id: str, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        # create s3 bucket and upload sample data to the bucket
        data_bucket = s3.Bucket(self, 
                                "DataSourceS3Bucket",
                                removal_policy=cdk.RemovalPolicy.DESTROY,
                                auto_delete_objects=True
                                )
        
        s3_deploy.BucketDeployment(self, "DeployDocuments",
                                   sources=[s3_deploy.Source.asset("documents/")],
                                   destination_bucket=data_bucket
                                   )
        
        # create a custom resouce execution role to have admin access
        # TODO: limit the role permissions here: we probably only need sts:passRole, qbusiness:* permissions
        custom_res_role = iam.Role(
            self, "QStackS3CustomResRole",
            assumed_by=iam.ServicePrincipal("lambda.amazonaws.com"),
            role_name="QStackS3CustomResRole"
        )
        custom_res_role.add_managed_policy(
            iam.ManagedPolicy.from_aws_managed_policy_name(
                "AdministratorAccess"
            )
        )
        
        # create enrichment lambda
        # grant data bucket access and textract
        
        pyMuPDF_lambda_layer = _lambda.LayerVersion(
               self, 'pyMuPDFLambdaLayer',
               code=_lambda.Code.from_asset('setup/layers/pyMuPDF-layer.zip'),
               compatible_runtimes=[_lambda.Runtime.PYTHON_3_8],
               description='pyMuPDF Library',
               layer_version_name='pyMuPDFLambdaLayer'
           )
        
        enrichment_lambda = _lambda.Function(
            self,
            "QEnrichmentLambda",
            runtime=_lambda.Runtime.PYTHON_3_8,
            handler="lambda_function.lambda_handler",
            code=_lambda.Code.from_asset(
                'setup/doc_enrichment_lambda'
            ),
            layers=[pyMuPDF_lambda_layer],
            timeout=Duration.seconds(60),
        )
        enrichment_lambda.role.add_to_principal_policy(
            iam.PolicyStatement(
                actions=[
                    'bedrock:*'
                ],
                resources=["*"]
            )
        )
        data_bucket.grant_read_write(enrichment_lambda.role)

        # create Amazon Q application
        
        sso_instance_arn_fetcher = cr.AwsCustomResource(
            self,
            "SSOInstanceArnFetcher",
            role=custom_res_role,
            timeout=Duration.minutes(10),
            install_latest_aws_sdk=True,
            on_create=cr.AwsSdkCall(
                service="@aws-sdk/client-sso-admin",
                action="ListInstances",
                physical_resource_id=cr.PhysicalResourceId.of("SSOInstanceArnFetcher"),
                output_paths=["Instances.0.InstanceArn"],  # Extract the first InstanceArn
            ),
            policy=cr.AwsCustomResourcePolicy.from_sdk_calls(
                resources=cr.AwsCustomResourcePolicy.ANY_RESOURCE
            ),
        )

        idc_instance_arn = sso_instance_arn_fetcher.get_response_field(
            "Instances.0.InstanceArn"
        )
        
        
        policy_document_json = {
            "Version": "2012-10-17",
            "Statement": [
                {
                    "Sid": "AmazonQApplicationPutMetricDataPermission",
                    "Effect": "Allow",
                    "Action": [
                        "cloudwatch:PutMetricData"
                    ],
                    "Resource": "*",
                    "Condition": {
                        "StringEquals": {
                            "cloudwatch:namespace": "AWS/QBusiness"
                        }
                    }
                },
                {
                    "Sid": "AmazonQApplicationDescribeLogGroupsPermission",
                    "Effect": "Allow",
                    "Action": [
                        "logs:DescribeLogGroups"
                    ],
                    "Resource": "*"
                },
                {
                    "Sid": "AmazonQApplicationCreateLogGroupPermission",
                    "Effect": "Allow",
                    "Action": [
                        "logs:CreateLogGroup"
                    ],
                    "Resource": [
                        f"arn:aws:logs:{REGION}:{ACCOUNT_ID}:log-group:/aws/qbusiness/*"
                    ]
                },
                {
                    "Sid": "AmazonQApplicationLogStreamPermission",
                    "Effect": "Allow",
                    "Action": [
                        "logs:DescribeLogStreams",
                        "logs:CreateLogStream",
                        "logs:PutLogEvents"
                    ],
                    "Resource": [
                        f"arn:aws:logs:{REGION}:{ACCOUNT_ID}:log-group:/aws/qbusiness/*:log-stream:*"
                    ]
                }
            ],
        }
        policy_doc = iam.PolicyDocument.from_json(policy_document_json)

        # create q application role
        q_app_role = iam.Role(
            self, 
            'QBusinessApplication',
            assumed_by=iam.ServicePrincipal(
                service='qbusiness.amazonaws.com',
                conditions={
                    "StringEquals": {
                        "aws:SourceAccount": ACCOUNT_ID,
                    },
                    "ArnLike": {
                        "aws:SourceArn": f"arn:aws:qbusiness:{REGION}:{ACCOUNT_ID}:application/*",
                    }
                }
            ),
            inline_policies={
                "AmazonQApplicationPolicy": policy_doc
            } 
        )
        
        q_application_res = cr.AwsCustomResource(
            self, 
            'QApplication',
            role=custom_res_role,
            timeout= Duration.minutes(10),
            install_latest_aws_sdk=True,
            on_create=cr.AwsSdkCall(
                service='@aws-sdk/client-qbusiness',
                action='CreateApplication',
                parameters={
                    "attachmentsConfiguration" : {
                        "attachmentsControlMode": "ENABLED"
                    },
                    "description": Q_APPLICATION_DESCRIPTION,
                    "displayName": Q_APPLICATION_NAME,
                    "identityCenterInstanceArn": idc_instance_arn,
                    "roleArn": q_app_role.role_arn
                },
                physical_resource_id=cr.PhysicalResourceId.from_response('applicationId'),
                output_paths=["applicationId"]
            ),
            on_delete=cr.AwsSdkCall(
                service='@aws-sdk/client-qbusiness',
                action='DeleteApplication',
                parameters={
                    "applicationId": cr.PhysicalResourceIdReference()
                }
            )
        )
        q_application_id = q_application_res.get_response_field('applicationId')
         # Wait for Instance ID of IdC
        q_application_res.node.add_dependency(sso_instance_arn_fetcher) 
        
        # create q for business applicaiton index
        index_res = cr.AwsCustomResource(
            self,
            'QApplicatonIndex',
            timeout= Duration.minutes(10),
            install_latest_aws_sdk=True,
            role=custom_res_role,
            on_create=cr.AwsSdkCall(
                service='@aws-sdk/client-qbusiness',
                action='CreateIndex',
                parameters={
                    "applicationId": q_application_id,
                    "capacityConfiguration": {
                        "units": 2
                    },
                    "description": f"{Q_APPLICATION_NAME}-index",
                    "displayName": f"{Q_APPLICATION_NAME}-index"
                },
                physical_resource_id=cr.PhysicalResourceId.from_response('indexId'),
                output_paths=["indexId"]
            ),
            on_delete=cr.AwsSdkCall(
                service='@aws-sdk/client-qbusiness',
                action='DeleteIndex',
                parameters={
                    "applicationId": q_application_id,
                    "indexId": cr.PhysicalResourceIdReference()
                }
            )
        )
        index_id = index_res.get_response_field('indexId')
        index_res.node.add_dependency(q_application_res)

        # create retriever
        retriever_res = cr.AwsCustomResource(
            self,
            'QApplicationRetriever',
            timeout= Duration.minutes(10),
            install_latest_aws_sdk=True,
            role=custom_res_role,
            on_create=cr.AwsSdkCall(
                service='@aws-sdk/client-qbusiness',
                action='CreateRetriever',
                parameters={
                    "applicationId": q_application_id,
                    "displayName": f"{Q_APPLICATION_NAME}-retriever",
                    "configuration": {
                        "nativeIndexConfiguration": {
                            "indexId": index_id
                        }
                    },
                    "type": "NATIVE_INDEX"
                },
                physical_resource_id=cr.PhysicalResourceId.from_response('retrieverId'),
                output_paths=["retrieverId"]
            ),
            on_delete=cr.AwsSdkCall(
                service='@aws-sdk/client-qbusiness',
                action='DeleteRetriever',
                parameters={
                    "applicationId": q_application_id,
                    "retrieverId": cr.PhysicalResourceIdReference()
                }
            )
        )

        retriever_res.node.add_dependency(index_res)

        # create a webexperience role
        webexperience_role = iam.Role(
            self,
            'WebExperienceRole',
            assumed_by=iam.ServicePrincipal('application.qbusiness.amazonaws.com'),
        )
        webexperience_role.add_to_policy(
            iam.PolicyStatement(
                actions=[
                    "qbusiness:Chat",
                    "qbusiness:ChatSync",
                    "qbusiness:ListMessages",
                    "qbusiness:ListConversations",
                    "qbusiness:DeleteConversation",
                    "qbusiness:PutFeedback",
                    "qbusiness:GetWebExperience",
                    "qbusiness:GetApplication",
                    "qbusiness:ListPlugins",
                    "qbusiness:GetChatControlsConfiguration"
                ],
                resources=[
                    f"arn:aws:qbusiness:{REGION}:{ACCOUNT_ID}:application/*",
                ]
            )
        )

        webexperience_role.add_to_policy(
            iam.PolicyStatement(
                actions=[
                    "kms:Decrypt"
                ],
                resources=[
                    f"arn:aws:kms:{REGION}:{ACCOUNT_ID}:key/key_id"
                ],
                conditions={
                    "StringLike": {"kms:ViaService": [
                            f"qbusiness.{REGION}.amazonaws.com"
                        ]
                    }
                }
            )
        )

        webexperience_role.add_to_policy(
            iam.PolicyStatement(
                actions=[
                    "qapps:CreateQApp",
                    "qapps:PredictProblemStatementFromConversation",
                    "qapps:PredictQAppFromProblemStatement",
                    "qapps:CopyQApp",
                    "qapps:GetQApp",
                    "qapps:ListQApps",
                    "qapps:UpdateQApp",
                    "qapps:DeleteQApp",
                    "qapps:AssociateQAppWithUser",
                    "qapps:DisassociateQAppFromUser",
                    "qapps:ImportDocumentToQApp",
                    "qapps:ImportDocumentToQAppSession",
                    "qapps:CreateLibraryItem",
                    "qapps:GetLibraryItem",
                    "qapps:UpdateLibraryItem",
                    "qapps:CreateLibraryItemReview",
                    "qapps:ListLibraryItems",
                    "qapps:CreateSubscriptionToken",
                    "qapps:StartQAppSession",
                    "qapps:StopQAppSession"
                ],
                resources=[
                    f"arn:aws:qbusiness:{REGION}:{ACCOUNT_ID}:application/*",
                ]
            )
        )

        # Add the assumeRolePolicy to the role
        webexperience_role.assume_role_policy.add_statements(
            iam.PolicyStatement(
                sid="QBusinessTrustPolicy",
                effect=iam.Effect.ALLOW,
                principals=[iam.ServicePrincipal("application.qbusiness.amazonaws.com")],
                actions=["sts:AssumeRole", "sts:SetContext"],
                conditions={
                    "StringEquals": {"aws:SourceAccount": f"{ACCOUNT_ID}"},
                    "ArnEquals": {
                        "aws:SourceArn": f"arn:aws:qbusiness:{REGION}:{ACCOUNT_ID}:application/*"
                    },
                },
            )
        )

        # create web experience
        webexperience_res = cr.AwsCustomResource(
            self,
            'QApplicationWebExperience',
            timeout= Duration.minutes(10),
            install_latest_aws_sdk=True,
            role=custom_res_role,
            on_create=cr.AwsSdkCall(
                service='@aws-sdk/client-qbusiness',
                action='CreateWebExperience',
                parameters={
                    "applicationId": q_application_id,
                    "title": f"{Q_APPLICATION_NAME} Demo",
                    "subtitle": Q_APPLICATION_DESCRIPTION,
                    "welcomeMessage": Q_APPLICATION_WELCOME_MESSAGE,
                    "roleArn": webexperience_role.role_arn
                },
                physical_resource_id=cr.PhysicalResourceId.from_response('webExperienceId'),
                output_paths=["webExperienceId"]
            ),
            on_delete=cr.AwsSdkCall(
                service='@aws-sdk/client-qbusiness',
                action='DeleteWebExperience',
                parameters={
                    "applicationId": q_application_id,
                    "webExperienceId": cr.PhysicalResourceIdReference()
                }
            )
        )

        webexperience_res.node.add_dependency(q_application_res)

        # create a service role for datasource execution
        datasource_role = iam.Role(
            self,
            'DataSourceRole',
            assumed_by=iam.ServicePrincipal('qbusiness.amazonaws.com'),
        )
        data_bucket.grant_read_write(datasource_role)
        datasource_role.add_to_policy(
            iam.PolicyStatement(
                actions=[
                    "qbusiness:BatchPutDocument",
                    "qbusiness:BatchDeleteDocument",
                    "qbusiness:PutGroup",
                    "qbusiness:CreateUser",
                    "qbusiness:DeleteGroup",
                    "qbusiness:UpdateUser",
                    "qbusiness:ListGroups"
                ],
                resources=[
                    f"arn:aws:qbusiness:{REGION}:{ACCOUNT_ID}:application/*",
                    f"arn:aws:qbusiness:{REGION}:{ACCOUNT_ID}:application/*/index/*",
                    f"arn:aws:qbusiness:{REGION}:{ACCOUNT_ID}:application/*/index/*/data-source/*"
                ]
            )
        )

        datasource_role.add_to_policy(
            iam.PolicyStatement(
                actions=[
                    "lambda:InvokeFunction"
                ],
                resources=[
                    f"arn:aws:lambda:{REGION}:{ACCOUNT_ID}:function:*"
                ]
            )
        )

        # create datasource
        cr.AwsCustomResource(
            self,
            'DataSource',
            timeout= Duration.minutes(10),
            install_latest_aws_sdk=True,
            role=custom_res_role,
            on_create=cr.AwsSdkCall(
                service='@aws-sdk/client-qbusiness',
                action='CreateDataSource',
                parameters={
                    "applicationId": q_application_id,
                    "description": DATASOURCE_DESCRIPTION,
                    "displayName": DATASOURCE_NAME,
                    "configuration": {
                        "type": "S3",
                        "connectionConfiguration": {
                            "repositoryEndpointMetadata": {
                                "BucketName": data_bucket.bucket_name
                            }
                        },
                        "repositoryConfigurations": {
                            "document": {
                                "fieldMappings": [
                                    {
                                        "indexFieldName": "s3_document_id",
                                        "indexFieldType": "STRING",
                                        "dataSourceFieldName": "s3_document_id"
                                    }
                                ]
                            }
                        },
                        "additionalProperties": {
                            "maxFileSizeInMegaBytes": "50",    
                            "exclusionPatterns": [
                                "pre-extraction/**"
                            ],

                            "s3BucketName": data_bucket.bucket_name
                        },
                        "syncMode": "FULL_CRAWL",
                        "version": "1.0.0"
                        },
                        "documentEnrichmentConfiguration": {
                            "preExtractionHookConfiguration": {
                                "lambdaArn": enrichment_lambda.function_arn,
                                "roleArn": datasource_role.role_arn,
                                's3BucketName': data_bucket.bucket_name
                            }
                        },
                        "indexId": index_id,
                        "roleArn": datasource_role.role_arn
                    },
                    physical_resource_id=cr.PhysicalResourceId.from_response('dataSourceId'),
                ),
                on_delete=cr.AwsSdkCall(
                    service='@aws-sdk/client-qbusiness',
                    action='DeleteDataSource',
                    parameters={
                        "applicationId": q_application_id,
                        "indexId": index_id,
                        "dataSourceId": cr.PhysicalResourceIdReference()
                    }
                )
            )
