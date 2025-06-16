# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""Tests for the ExperimentTemplates class in the server module."""

import unittest
from unittest.mock import patch, MagicMock
from botocore.exceptions import ClientError

# Import the class to test
from awslabs.aws_fis_mcp_server.server import ExperimentTemplates


class TestExperimentTemplates(unittest.TestCase):
    """Test cases for the ExperimentTemplates class."""

    @patch('awslabs.aws_fis_mcp_server.server.aws_fis')
    @patch('awslabs.aws_fis_mcp_server.server.Context')
    async def test_create_experiment_template_minimal(self, mock_context, mock_aws_fis):
        """Test creating an experiment template with minimal parameters."""
        # Setup mock response
        template_id = 'template-1'
        mock_aws_fis.create_experiment_template.return_value = {
            'experimentTemplate': {
                'id': template_id,
                'arn': f'arn:aws:fis:us-east-1:123456789012:experiment-template/{template_id}',
                'description': 'Test Template',
                'creationTime': '2023-01-01T00:00:00.000Z',
                'lastUpdateTime': '2023-01-01T00:00:00.000Z'
            }
        }

        # Call the method with minimal parameters
        result = await ExperimentTemplates.create_experiment_template(
            clientToken='test-token',
            description='Test Template',
            role_arn='arn:aws:iam::123456789012:role/FisRole'
        )

        # Verify the result
        self.assertIn('experimentTemplate', result)
        self.assertEqual(result['experimentTemplate']['id'], template_id)
        self.assertEqual(result['experimentTemplate']['description'], 'Test Template')
        
        # Verify the AWS client was called correctly
        mock_aws_fis.create_experiment_template.assert_called_once_with(
            clientToken='test-token',
            description='Test Template',
            stopConditions=[],
            targets={},
            actions={},
            roleArn='arn:aws:iam::123456789012:role/FisRole',
            tags={},
            logConfiguration=None,
            experimentOptions=None,
            experimentReportConfiguration=None
        )

    @patch('awslabs.aws_fis_mcp_server.server.aws_fis')
    @patch('awslabs.aws_fis_mcp_server.server.Context')
    async def test_create_experiment_template_full(self, mock_context, mock_aws_fis):
        """Test creating an experiment template with all parameters."""
        # Setup mock response
        template_id = 'template-1'
        mock_aws_fis.create_experiment_template.return_value = {
            'experimentTemplate': {
                'id': template_id,
                'arn': f'arn:aws:fis:us-east-1:123456789012:experiment-template/{template_id}',
                'description': 'Test Template',
                'creationTime': '2023-01-01T00:00:00.000Z',
                'lastUpdateTime': '2023-01-01T00:00:00.000Z'
            }
        }

        # Prepare test parameters
        client_token = 'test-token'
        description = 'Test Template'
        tags = {'Name': 'Test Template'}
        stop_conditions = [{'source': 'aws:cloudwatch:alarm', 'value': 'arn:aws:cloudwatch:us-east-1:123456789012:alarm:test-alarm'}]
        targets = {
            'Instances': {
                'resource_type': 'aws:ec2:instance',
                'selection_mode': 'ALL'
            }
        }
        actions = {
            'StopInstances': {
                'action_id': 'aws:ec2:stop-instances',
                'targets': {'Instances': 'Instances'}
            }
        }
        role_arn = 'arn:aws:iam::123456789012:role/FisRole'
        log_configuration = {'log_schema_version': 1}
        experiment_options = {'actionsMode': 'run-all'}
        report_configuration = {'s3Configuration': {'bucketName': 'test-bucket'}}

        # Call the method with all parameters
        result = await ExperimentTemplates.create_experiment_template(
            clientToken=client_token,
            description=description,
            tags=tags,
            stop_conditions=stop_conditions,
            targets=targets,
            actions=actions,
            role_arn=role_arn,
            log_configuration=log_configuration,
            experiment_options=experiment_options,
            report_configuration=report_configuration
        )

        # Verify the result
        self.assertIn('experimentTemplate', result)
        self.assertEqual(result['experimentTemplate']['id'], template_id)
        
        # Verify the AWS client was called correctly
        mock_aws_fis.create_experiment_template.assert_called_once_with(
            clientToken=client_token,
            description=description,
            tags=tags,
            stopConditions=stop_conditions,
            targets=targets,
            actions=actions,
            roleArn=role_arn,
            logConfiguration=log_configuration,
            experimentOptions=experiment_options,
            experimentReportConfiguration=report_configuration
        )

    @patch('awslabs.aws_fis_mcp_server.server.aws_fis')
    @patch('awslabs.aws_fis_mcp_server.server.Context')
    async def test_create_experiment_template_error(self, mock_context, mock_aws_fis):
        """Test error handling when creating an experiment template."""
        # Setup mock to raise an exception
        mock_aws_fis.create_experiment_template.side_effect = ClientError(
            {'Error': {'Code': 'ValidationException', 'Message': 'Invalid role ARN'}},
            'create_experiment_template'
        )
        mock_context.error = MagicMock()

        # Call the method and expect an exception
        with self.assertRaises(Exception):
            await ExperimentTemplates.create_experiment_template(
                clientToken='test-token',
                description='Test Template',
                role_arn='invalid-role-arn'
            )
        
        # Verify error was logged
        mock_context.error.assert_called_once()


if __name__ == "__main__":
    unittest.main()