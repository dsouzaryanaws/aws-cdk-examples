# AWS API Gateway HTTP API to AWS Lambda in VPC to DynamoDB CDK Python Sample!

## Overview

Creates an [AWS Lambda](https://aws.amazon.com/lambda/) function writing to [Amazon DynamoDB](https://aws.amazon.com/dynamodb/) and invoked by [Amazon API Gateway](https://aws.amazon.com/api-gateway/) REST API with comprehensive throttling and rate limiting following AWS Well-Architected Framework REL05-BP02 best practices.

![architecture](docs/architecture.png)

## 🚀 Well-Architected Framework Compliance

This implementation follows **REL05-BP02 "Throttle requests"** best practice with:

### ✅ API Gateway Throttling
- **Rate Limit**: 1,000 requests/second
- **Burst Limit**: 2,000 requests
- **HTTP 429** responses for throttled requests

### ✅ Usage Plans & API Keys
- **Basic Plan**: 100 RPS, 10K requests/day
- **Premium Plan**: 500 RPS, 100K requests/day
- API key authentication required

### ✅ AWS WAF Rate Limiting
- IP-based rate limiting: 2,000 requests per 5-minute window
- Automatic blocking of malicious IPs
- CloudWatch metrics enabled

### ✅ Lambda Concurrency Control
- Reserved concurrency: 100 executions
- Prevents account-wide concurrency exhaustion

### ✅ Monitoring & Alarms
- API Gateway throttling alarms
- Lambda throttling alarms
- WAF blocked requests metrics

## Setup

The `cdk.json` file tells the CDK Toolkit how to execute your app.

This project is set up like a standard Python project. The initialization
process also creates a virtualenv within this project, stored under the `.venv`
directory. To create the virtualenv it assumes that there is a `python3`
(or `python` for Windows) executable in your path with access to the `venv`
package. If for any reason the automatic creation of the virtualenv fails,
you can create the virtualenv manually.

To manually create a virtualenv on MacOS and Linux:

```
$ python3 -m venv .venv
```

After the init process completes and the virtualenv is created, you can use the following
step to activate your virtualenv.

```
$ source .venv/bin/activate
```

If you are a Windows platform, you would activate the virtualenv like this:

```
% .venv\Scripts\activate.bat
```

Once the virtualenv is activated, you can install the required dependencies.

```
$ pip install -r requirements.txt
```

At this point you can now synthesize the CloudFormation template for this code.

```
$ cdk synth
```

To add additional dependencies, for example other CDK libraries, just add
them to your `setup.py` file and rerun the `pip install -r requirements.txt`
command.

## Deploy
At this point you can deploy the stack.

Using the default profile

```
$ cdk deploy
```

With specific profile

```
$ cdk deploy --profile test
```

## 🔑 API Key Management

After deployment, retrieve API keys from AWS Console:

1. Navigate to **API Gateway Console**
2. Select your API → **API Keys**
3. Copy the API key values for Basic/Premium plans
4. Use the `x-api-key` header in requests

## Testing the API

### Basic Usage (with API Key)
```bash
curl -X POST https://your-api-id.execute-api.region.amazonaws.com/prod/data \
  -H "Content-Type: application/json" \
  -H "x-api-key: YOUR_API_KEY" \
  -d '{
    "year": "2023",
    "title": "Test Movie",
    "id": "12"
  }'
```

### Expected Response
```json
{"message": "Successfully inserted data!"}
```

### Throttling Test
Generate high load to test throttling:
```bash
# This should trigger HTTP 429 responses
for i in {1..1500}; do
  curl -X POST https://your-api-id.execute-api.region.amazonaws.com/prod/data \
    -H "x-api-key: YOUR_API_KEY" \
    -d '{"year":"2023","title":"Load Test","id":"'$i'"}' &
done
```

## 📊 Monitoring

### CloudWatch Metrics
- **API Gateway**: `AWS/ApiGateway` namespace
  - `ThrottledRequests`: Monitor throttling events
  - `4XXError`: Track client errors (429s)
- **Lambda**: `AWS/Lambda` namespace  
  - `Throttles`: Monitor Lambda throttling
  - `ConcurrentExecutions`: Track concurrency usage
- **WAF**: `AWS/WAFV2` namespace
  - `BlockedRequests`: Monitor blocked IPs

### Alarms Configured
- API Gateway throttling > 100 requests
- Lambda throttling > 10 executions

## 🔧 Throttling Configuration

### Adjusting Limits
Modify throttling in `stacks/apigw_http_api_lambda_dynamodb_python_cdk_stack.py`:

```python
# API-level throttling
throttle=apigw_.ThrottleSettings(
    rate_limit=1000,  # Adjust based on load testing
    burst_limit=2000
)

# Usage plan throttling
basic_plan = api.add_usage_plan(
    "BasicPlan",
    throttle=apigw_.ThrottleSettings(
        rate_limit=100,   # Customize per tier
        burst_limit=200
    )
)
```

### Load Testing Recommendations
1. Use tools like Apache Bench or Artillery
2. Test at 80% of configured limits
3. Monitor backend (DynamoDB) performance
4. Adjust limits based on results

## Cleanup
Run below script to delete AWS resources created by this sample stack.
```
cdk destroy
```

## Useful commands

* `cdk ls`          list all stacks in the app
* `cdk synth`       emits the synthesized CloudFormation template
* `cdk deploy`      deploy this stack to your default AWS account/region
* `cdk diff`        compare deployed stack with current state
* `cdk docs`        open CDK documentation

## 📚 References

- [REL05-BP02 Throttle requests](https://docs.aws.amazon.com/wellarchitected/latest/reliability-pillar/rel_mitigate_interaction_failure_throttle_requests.html)
- [API Gateway Request Throttling](https://docs.aws.amazon.com/apigateway/latest/developerguide/api-gateway-request-throttling.html)
- [AWS WAF Rate-based Rules](https://docs.aws.amazon.com/waf/latest/developerguide/waf-rule-statement-type-rate-based.html)

Enjoy!