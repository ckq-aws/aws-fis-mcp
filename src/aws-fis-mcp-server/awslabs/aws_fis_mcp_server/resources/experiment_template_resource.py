def experiment_template_resource():
    """
    {
        "tags": {
            "Name": "StopEC2InstancesWithFilters"
        },
        "description": "Stop and restart all instances in us-east-1b with the tag env=prod in the specified VPC",
        "targets": {
            "myInstances": {
                "resourceType": "aws:ec2:instance",
                "resourceTags": {
                    "env": "prod"
                },
                "filters": [
                    {
                        "path": "Placement.AvailabilityZone",
                        "values": ["us-east-1b"]
                    },
                    {
                        "path": "State.Name",
                        "values": ["running"]
                    },
                    {
                        "path": "VpcId",
                        "values": [ "vpc-aabbcc11223344556"]
                    }
                ],
                "selectionMode": "ALL"
            }
        },
        "actions": {
            "StopInstances": {
                "actionId": "aws:ec2:stop-instances",
                "description": "stop the instances",
                "parameters": {
                    "startInstancesAfterDuration": "PT2M"
                },
                "targets": {
                    "Instances": "myInstances"
                }
            }
        },
        "stopConditions": [
            {
                "source": "aws:cloudwatch:alarm",
                "value": "arn:aws:cloudwatch:us-east-1:111122223333:alarm:alarm-name"
            }
        ],
        "roleArn": "arn:aws:iam::111122223333:role/role-name"
    }
    """