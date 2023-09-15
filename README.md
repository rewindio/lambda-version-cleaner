# Lambda Version Cleaner

- [Purpose](#purpose)
- [Installing](#installing)

## Purpose

This SAM template deploys a Lambda function that deletes old Lambda versions in the account deployed in.

## Installing

There are deployment workflows that handle deployment on PR merge. If you want to install manually, everything is packaged with [AWS SAM](https://aws.amazon.com/serverless/sam/). Note that the `AlarmsSNSTopic` parameter is optional and if provided, will also deploy a CloudWatch alarm on invocation errors which pushes alarm events to the specified `AlarmsSNSTopic`. Clone this repo and run the following commands:

```sh
sam build --use-container

sam deploy --debug \                        
    --stack-name lambda-version-cleaner \
    --s3-bucket <an existing bucket to store lambda sam apps in> \
    --region <AWS region to deploy to> \
    --profile <AWS profile to use> \
    --capabilities CAPABILITY_NAMED_IAM \
    --parameter-overrides \
        "NumberOfVersionsToKeep=<number> \
        AWSRegions=<comma separated list of AWS regions to delete Lambda versions from> \
        AlarmsSNSTopic=<optional input name of alarm SNS topic>" \
    --no-fail-on-empty-changeset

e.g.
sam deploy --debug \                        
    --stack-name lambda-version-cleaner \
    --s3-bucket some-s3-bucket \
    --region us-east-1 \
    --profile staging \
    --capabilities CAPABILITY_NAMED_IAM \
    --parameter-overrides \
        "NumberOfVersionsToKeep=10  \
        AWSRegions=us-east-1,us-east-2" \
    --no-fail-on-empty-changeset
```
