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

"""Tests for the update_experiment_template method in the ExperimentTemplates class."""

import unittest

# Import the class to test
from awslabs.aws_fis_mcp_server.server import ExperimentTemplates
from botocore.exceptions import ClientError
from unittest.mock import MagicMock, patch


class TestUpdateExperimentTemplate(unittest.TestCase):
    """Test cases for the update_experiment_template method."""

    @patch('awslabs.aws_fis_mcp_server.server.aws_fis')
    @patch('awslabs.aws_fis_mcp_server.server.Context')
    async def test_update_experiment_template_minimal(self, mock_context, mock_aws_fis):
        """Test updating an experiment template with minimal parameters."""
        # Setup mock response
        template_id = 'template-1'
        mock_aws_fis.update_experiment_template.return_value = {
            'experimentTemplate': {
                'id': template_id,
                'arn': f'arn:aws:fis:us-east-1:123456789012:experiment-template/{template_id}',
                'description': 'Updated Test Template',
                'creationTime': '2023-01-01T00:00:00.000Z',
                'lastUpdateTime': '2023-01-02T00:00:00.000Z',
            }
        }

        # Call the method with minimal parameters
        result = await ExperimentTemplates.update_experiment_template(
            id=template_id,
            description='Updated Test Template',
        )

        # Verify the result
        self.assertIn('experimentTemplate', result)
        self.assertEqual(result['experimentTemplate']['id'], template_id)
        self.assertEqual(result['experimentTemplate']['description'], 'Updated Test Template')

        # Verify the AWS client was called correctly
        mock_aws_fis.update_experiment_template.assert_called_once_with(
            id=template_id,
            description='Updated Test Template',
            stopConditions=None,
            targets=None,
            actions=None,
            roleArn=None,
            logConfiguration=None,
            experimentOptions=None,
        )

    @patch('awslabs.aws_fis_mcp_server.server.aws_fis')
    @patch('awslabs.aws_fis_mcp_server.server.Context')
    async def test_update_experiment_template_full(self, mock_context, mock_aws_fis):
        """Test updating an experiment template with all parameters."""
        # Setup mock response
        template_id = 'template-1'
        mock_aws_fis.update_experiment_template.return_value = {
            'experimentTemplate': {
                'id': template_id,
                'arn': f'arn:aws:fis:us-east-1:123456789012:experiment-template/{template_id}',
                'description': 'Updated Test Template',
                'creationTime': '2023-01-01T00:00:00.000Z',
                'lastUpdateTime': '2023-01-02T00:00:00.000Z',
            }
        }

        # Prepare test parameters
        description = 'Updated Test Template'
        stop_conditions = [
            {
                'source': 'aws:cloudwatch:alarm',
                'value': 'arn:aws:cloudwatch:us-east-1:123456789012:alarm:updated-alarm',
            }
        ]
        targets = {'Instances': {'resource_type': 'aws:ec2:instance', 'selection_mode': 'COUNT(1)'}}
        actions = {
            'StopInstances': {
                'action_id': 'aws:ec2:stop-instances',
                'targets': {'Instances': 'Instances'},
            }
        }
        role_arn = 'arn:aws:iam::123456789012:role/UpdatedFisRole'
        log_configuration = {'log_schema_version': 2}
        experiment_options = {'actionsMode': 'skip-all'}

        # Call the method with all parameters
        result = await ExperimentTemplates.update_experiment_template(
            id=template_id,
            description=description,
            stop_conditions=stop_conditions,
            targets=targets,
            actions=actions,
            role_arn=role_arn,
            log_configuration=log_configuration,
            experiment_options=experiment_options,
        )

        # Verify the result
        self.assertIn('experimentTemplate', result)
        self.assertEqual(result['experimentTemplate']['id'], template_id)

        # Verify the AWS client was called correctly
        mock_aws_fis.update_experiment_template.assert_called_once_with(
            id=template_id,
            description=description,
            stopConditions=stop_conditions,
            targets=targets,
            actions=actions,
            roleArn=role_arn,
            logConfiguration=log_configuration,
            experimentOptions=experiment_options,
        )

    @patch('awslabs.aws_fis_mcp_server.server.aws_fis')
    @patch('awslabs.aws_fis_mcp_server.server.Context')
    async def test_update_experiment_template_error(self, mock_context, mock_aws_fis):
        """Test error handling when updating an experiment template."""
        # Setup mock to raise an exception
        template_id = 'template-1'
        mock_aws_fis.update_experiment_template.side_effect = ClientError(
            {'Error': {'Code': 'ResourceNotFoundException', 'Message': 'Template not found'}},
            'update_experiment_template',
        )
        mock_context.error = MagicMock()

        # Call the method and expect an exception
        with self.assertRaises(Exception):
            await ExperimentTemplates.update_experiment_template(
                id=template_id, description='Updated Test Template'
            )

        # Verify error was logged
        mock_context.error.assert_called_once()


if __name__ == '__main__':
    unittest.main()