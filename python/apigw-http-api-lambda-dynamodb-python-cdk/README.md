
# AWS API Gateway HTTP API to AWS Lambda in VPC to DynamoDB CDK Python Sample!


## Overview

Creates an [AWS Lambda](https://aws.amazon.com/lambda/) function writing to [Amazon DynamoDB](https://aws.amazon.com/dynamodb/) and invoked by [Amazon API Gateway](https://aws.amazon.com/api-gateway/) REST API. 

![architecture](docs/architecture.png)

## Setup

The `cdk.json` file tells the CDK Toolkit how to execute your app.

This project is set up like a standard Python project.  The initialization
process also creates a virtualenv within this project, stored under the `.venv`
directory.  To create the virtualenv it assumes that there is a `python3`
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

## After Deploy
Navigate to AWS API Gateway console and test the API with below sample data 
```json
{
    "year":"2023", 
    "title":"kkkg",
    "id":"12"
}
```

You should get below response 

```json
{"message": "Successfully inserted data!"}
```

## Performance and Throttling Configuration

### Load Testing Guidance

Before configuring throttle limits in production, perform load testing to establish appropriate capacity:

**Recommended Testing Approach:**
1. Use tools like Apache JMeter, Artillery, or AWS Distributed Load Testing
2. Test scenarios:
   - Normal sustained load
   - Peak traffic patterns
   - Burst traffic spikes
   - Large payload requests (test both rate and request size)
3. Monitor metrics:
   - API Gateway latency and error rates
   - Lambda duration, concurrency, and throttles
   - DynamoDB consumed capacity
   - VPC endpoint throughput

**Example Load Test with Artillery:**
```bash
# Install Artillery
npm install -g artillery

# Create test-config.yml
cat > test-config.yml << EOF
config:
  target: "https://YOUR_API_ENDPOINT"
  phases:
    - duration: 60
      arrivalRate: 100
      name: "Sustained load"
    - duration: 30
      arrivalRate: 500
      name: "Peak load"
scenarios:
  - flow:
      - post:
          url: "/prod"
          json:
            year: "2023"
            title: "test"
            id: "{{ \$randomString() }}"
EOF

# Run test
artillery run test-config.yml
```

### Current Configuration (Placeholder Values)

**Note:** The values below are placeholders and should be updated based on your load testing results.

**API Gateway Throttling:**
- Rate Limit: 1000 requests/second (update after testing)
- Burst Limit: 2000 requests (update after testing)

**Lambda Configuration:**
- Reserved Concurrency: 100 executions (update after testing)
- Memory: 1024 MB
- Timeout: 5 minutes

**Testing Checklist:**
- [ ] Conduct load testing with expected traffic patterns
- [ ] Document maximum sustained request rate
- [ ] Document burst capacity
- [ ] Measure average and P99 Lambda execution duration
- [ ] Update throttle limits based on test results
- [ ] Re-test after any infrastructure changes

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

Enjoy!
