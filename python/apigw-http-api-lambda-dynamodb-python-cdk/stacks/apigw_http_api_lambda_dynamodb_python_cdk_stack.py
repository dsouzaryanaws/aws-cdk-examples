# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: MIT-0

import os
from aws_cdk import (
    Stack,
    aws_dynamodb as dynamodb_,
    aws_lambda as lambda_,
    aws_apigateway as apigw_,
    aws_ec2 as ec2,
    aws_iam as iam,
    aws_wafv2 as wafv2,
    aws_cloudwatch as cloudwatch,
    Duration,
)
from constructs import Construct

TABLE_NAME = "demo_table"


class ApigwHttpApiLambdaDynamodbPythonCdkStack(Stack):
    def __init__(self, scope: Construct, construct_id: str, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        # VPC
        vpc = ec2.Vpc(
            self,
            "Ingress",
            cidr="10.1.0.0/16",
            subnet_configuration=[
                ec2.SubnetConfiguration(
                    name="Private-Subnet", subnet_type=ec2.SubnetType.PRIVATE_ISOLATED,
                    cidr_mask=24
                )
            ],
        )
        
        # Create VPC endpoint
        dynamo_db_endpoint = ec2.GatewayVpcEndpoint(
            self,
            "DynamoDBVpce",
            service=ec2.GatewayVpcEndpointAwsService.DYNAMODB,
            vpc=vpc,
        )

        # This allows to customize the endpoint policy
        dynamo_db_endpoint.add_to_policy(
            iam.PolicyStatement(  # Restrict to listing and describing tables
                principals=[iam.AnyPrincipal()],
                actions=["dynamodb:DescribeStream",
                "dynamodb:DescribeTable",
                "dynamodb:Get*",
                "dynamodb:Query",
                "dynamodb:Scan",
                "dynamodb:CreateTable",
                "dynamodb:Delete*",
                "dynamodb:Update*",
                "dynamodb:PutItem"],
                resources=["*"],
            )
        )

        # Create DynamoDb Table
        demo_table = dynamodb_.Table(
            self,
            TABLE_NAME,
            partition_key=dynamodb_.Attribute(
                name="id", type=dynamodb_.AttributeType.STRING
            ),
        )

        # Create the Lambda function with reserved concurrency (REL05-BP02)
        api_hanlder = lambda_.Function(
            self,
            "ApiHandler",
            function_name="apigw_handler",
            runtime=lambda_.Runtime.PYTHON_3_9,
            code=lambda_.Code.from_asset("lambda/apigw-handler"),
            handler="index.handler",
            vpc=vpc,
            vpc_subnets=ec2.SubnetSelection(
                subnet_type=ec2.SubnetType.PRIVATE_ISOLATED
            ),
            memory_size=1024,
            timeout=Duration.minutes(5),
            reserved_concurrent_executions=100  # REL05-BP02: Reserve concurrency
        )

        # grant permission to lambda to write to demo table
        demo_table.grant_write_data(api_hanlder)
        api_hanlder.add_environment("TABLE_NAME", demo_table.table_name)

        # Create API Gateway with explicit throttling (REL05-BP02)
        api = apigw_.RestApi(
            self,
            "Endpoint",
            throttle=apigw_.ThrottleSettings(
                rate_limit=1000,  # 1000 requests per second
                burst_limit=2000  # 2000 burst capacity
            ),
            deploy_options=apigw_.StageOptions(
                throttling_rate_limit=1000,
                throttling_burst_limit=2000
            )
        )

        # Create Lambda integration
        integration = apigw_.LambdaIntegration(api_hanlder)

        # Add resource and method with proper error responses
        resource = api.root.add_resource("data")
        method = resource.add_method(
            "POST", 
            integration,
            api_key_required=True,  # Require API key for usage plans
            method_responses=[
                apigw_.MethodResponse(
                    status_code="200",
                    response_models={"application/json": apigw_.Model.EMPTY_MODEL}
                ),
                apigw_.MethodResponse(
                    status_code="429",
                    response_models={"application/json": apigw_.Model.ERROR_MODEL}
                )
            ]
        )

        # Create usage plans with tiered throttling (REL05-BP02)
        basic_plan = api.add_usage_plan(
            "BasicPlan",
            throttle=apigw_.ThrottleSettings(
                rate_limit=100,   # 100 RPS for basic tier
                burst_limit=200
            ),
            quota=apigw_.QuotaSettings(
                limit=10000,      # 10K requests per day
                period=apigw_.Period.DAY
            )
        )

        premium_plan = api.add_usage_plan(
            "PremiumPlan", 
            throttle=apigw_.ThrottleSettings(
                rate_limit=500,   # 500 RPS for premium tier
                burst_limit=1000
            ),
            quota=apigw_.QuotaSettings(
                limit=100000,     # 100K requests per day
                period=apigw_.Period.DAY
            )
        )

        # Create API keys for different consumer tiers
        basic_key = api.add_api_key("BasicApiKey")
        premium_key = api.add_api_key("PremiumApiKey")

        # Associate keys with plans
        basic_plan.add_api_key(basic_key)
        premium_plan.add_api_key(premium_key)

        # Add usage plans to API stages
        basic_plan.add_api_stage(stage=api.deployment_stage)
        premium_plan.add_api_stage(stage=api.deployment_stage)

        # Create AWS WAF for IP-based rate limiting (REL05-BP02)
        web_acl = wafv2.CfnWebACL(
            self,
            "ApiGatewayWAF",
            scope="REGIONAL",
            default_action=wafv2.CfnWebACL.DefaultActionProperty(allow={}),
            rules=[
                wafv2.CfnWebACL.RuleProperty(
                    name="RateLimitRule",
                    priority=1,
                    statement=wafv2.CfnWebACL.StatementProperty(
                        rate_based_statement=wafv2.CfnWebACL.RateBasedStatementProperty(
                            limit=2000,  # requests per 5-minute window
                            aggregate_key_type="IP"
                        )
                    ),
                    action=wafv2.CfnWebACL.RuleActionProperty(
                        block={}
                    ),
                    visibility_config=wafv2.CfnWebACL.VisibilityConfigProperty(
                        sampled_requests_enabled=True,
                        cloud_watch_metrics_enabled=True,
                        metric_name="RateLimitRule"
                    )
                )
            ],
            visibility_config=wafv2.CfnWebACL.VisibilityConfigProperty(
                sampled_requests_enabled=True,
                cloud_watch_metrics_enabled=True,
                metric_name="ApiGatewayWAF"
            )
        )

        # Associate WAF with API Gateway
        wafv2.CfnWebACLAssociation(
            self,
            "WAFAssociation",
            resource_arn=api.arn_for_execute_api(),
            web_acl_arn=web_acl.attr_arn
        )

        # Add CloudWatch alarms for monitoring (REL05-BP02)
        cloudwatch.Alarm(
            self,
            "ApiGatewayThrottleAlarm",
            metric=cloudwatch.Metric(
                namespace="AWS/ApiGateway",
                metric_name="ThrottledRequests",
                dimensions_map={"ApiName": api.rest_api_name}
            ),
            threshold=100,
            evaluation_periods=2,
            alarm_description="API Gateway requests are being throttled"
        )

        cloudwatch.Alarm(
            self,
            "LambdaThrottleAlarm",
            metric=api_hanlder.metric_throttles(),
            threshold=10,
            evaluation_periods=2,
            alarm_description="Lambda function is being throttled"
        )