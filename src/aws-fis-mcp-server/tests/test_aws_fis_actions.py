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

"""Tests for the AwsFisActions class in the server module."""

import unittest

# Import the class to test
from awslabs.aws_fis_mcp_server.server import AwsFisActions
from botocore.exceptions import ClientError
from unittest.mock import AsyncMock, MagicMock, patch


class TestAwsFisActions(unittest.TestCase):
    """Test cases for the AwsFisActions class."""

    @patch('awslabs.aws_fis_mcp_server.server.aws_fis')
    @patch('awslabs.aws_fis_mcp_server.server.Context')
    async def test_list_all_fis_experiments_no_pagination(self, mock_context, mock_aws_fis):
        """Test listing FIS experiments without pagination."""
        # Setup mock response
        mock_aws_fis.list_experiments.return_value = {
            'experiments': [
                {
                    'id': 'exp-1',
                    'arn': 'arn:aws:fis:us-east-1:123456789012:experiment/exp-1',
                    'experimentTemplateId': 'template-1',
                    'state': 'completed',
                    'experimentOptions': {'option1': 'value1'},
                    'tags': {'Name': 'Test Experiment'},
                }
            ]
        }

        # Call the method
        result = await AwsFisActions.list_all_fis_experiments()

        # Verify the result
        self.assertEqual(len(result), 1)
        self.assertIn('Test Experiment', result)
        self.assertEqual(result['Test Experiment']['id'], 'exp-1')
        self.assertEqual(result['Test Experiment']['state'], 'completed')

        # Verify the AWS client was called correctly
        mock_aws_fis.list_experiments.assert_called_once()

    @patch('awslabs.aws_fis_mcp_server.server.aws_fis')
    @patch('awslabs.aws_fis_mcp_server.server.Context')
    async def test_list_all_fis_experiments_with_pagination(self, mock_context, mock_aws_fis):
        """Test listing FIS experiments with pagination."""
        # Setup mock responses for pagination
        mock_aws_fis.list_experiments.side_effect = [
            {
                'experiments': [
                    {
                        'id': 'exp-1',
                        'arn': 'arn:aws:fis:us-east-1:123456789012:experiment/exp-1',
                        'experimentTemplateId': 'template-1',
                        'state': 'completed',
                        'experimentOptions': {'option1': 'value1'},
                        'tags': {'Name': 'Test Experiment 1'},
                    }
                ],
                'nextToken': 'token1',
            },
            {
                'experiments': [
                    {
                        'id': 'exp-2',
                        'arn': 'arn:aws:fis:us-east-1:123456789012:experiment/exp-2',
                        'experimentTemplateId': 'template-2',
                        'state': 'running',
                        'experimentOptions': {'option2': 'value2'},
                        'tags': {'Name': 'Test Experiment 2'},
                    }
                ]
            },
        ]

        # Call the method
        result = await AwsFisActions.list_all_fis_experiments()

        # Verify the result
        self.assertEqual(len(result), 2)
        self.assertIn('Test Experiment 1', result)
        self.assertIn('Test Experiment 2', result)
        self.assertEqual(result['Test Experiment 1']['id'], 'exp-1')
        self.assertEqual(result['Test Experiment 2']['id'], 'exp-2')

        # Verify the AWS client was called correctly
        self.assertEqual(mock_aws_fis.list_experiments.call_count, 2)
        mock_aws_fis.list_experiments.assert_any_call()
        mock_aws_fis.list_experiments.assert_any_call(nextToken='token1')

    @patch('awslabs.aws_fis_mcp_server.server.aws_fis')
    @patch('awslabs.aws_fis_mcp_server.server.Context')
    async def test_list_all_fis_experiments_error(self, mock_context, mock_aws_fis):
        """Test error handling when listing FIS experiments."""
        # Setup mock to raise an exception
        mock_aws_fis.list_experiments.side_effect = ClientError(
            {'Error': {'Code': 'InternalServerError', 'Message': 'Test error'}}, 'list_experiments'
        )
        mock_context.error = MagicMock()

        # Call the method and expect an exception
        with self.assertRaises(Exception):
            await AwsFisActions.list_all_fis_experiments()

        # Verify error was logged
        mock_context.error.assert_called_once()

    @patch('awslabs.aws_fis_mcp_server.server.aws_fis')
    @patch('awslabs.aws_fis_mcp_server.server.Context')
    async def test_get_experiment_details_success(self, mock_context, mock_aws_fis):
        """Test getting experiment details successfully."""
        # Setup mock response
        experiment_id = 'exp-1'
        mock_aws_fis.get_experiment.return_value = {
            'experiment': {
                'id': experiment_id,
                'arn': f'arn:aws:fis:us-east-1:123456789012:experiment/{experiment_id}',
                'experimentTemplateId': 'template-1',
                'state': {'status': 'completed'},
                'experimentOptions': {'option1': 'value1'},
                'tags': {'Name': 'Test Experiment'},
            }
        }

        # Call the method
        result = await AwsFisActions.get_experiment_details(id=experiment_id)

        # Verify the result
        self.assertEqual(result['id'], experiment_id)
        self.assertEqual(result['state']['status'], 'completed')

        # Verify the AWS client was called correctly
        mock_aws_fis.get_experiment.assert_called_once_with(id=experiment_id)

    @patch('awslabs.aws_fis_mcp_server.server.aws_fis')
    @patch('awslabs.aws_fis_mcp_server.server.Context')
    async def test_get_experiment_details_error(self, mock_context, mock_aws_fis):
        """Test error handling when getting experiment details."""
        # Setup mock to raise an exception
        experiment_id = 'exp-1'
        mock_aws_fis.get_experiment.side_effect = ClientError(
            {'Error': {'Code': 'ResourceNotFoundException', 'Message': 'Experiment not found'}},
            'get_experiment',
        )
        mock_context.error = MagicMock()

        # Call the method and expect an exception
        with self.assertRaises(Exception):
            await AwsFisActions.get_experiment_details(id=experiment_id)

        # Verify error was logged
        mock_context.error.assert_called_once()

    @patch('awslabs.aws_fis_mcp_server.server.aws_fis')
    @patch('awslabs.aws_fis_mcp_server.server.Context')
    async def test_list_experiment_templates_no_pagination(self, mock_context, mock_aws_fis):
        """Test listing experiment templates without pagination."""
        # Setup mock response
        mock_aws_fis.list_experiment_templates.return_value = {
            'experimentTemplates': [
                {
                    'id': 'template-1',
                    'arn': 'arn:aws:fis:us-east-1:123456789012:experiment-template/template-1',
                    'description': 'Test Template',
                    'tags': {'Name': 'Test Template'},
                }
            ]
        }

        # Call the method
        result = await AwsFisActions.list_experiment_templates()

        # Verify the result
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0]['id'], 'template-1')
        self.assertEqual(result[0]['description'], 'Test Template')

        # Verify the AWS client was called correctly
        mock_aws_fis.list_experiment_templates.assert_called_once()

    @patch('awslabs.aws_fis_mcp_server.server.aws_fis')
    @patch('awslabs.aws_fis_mcp_server.server.Context')
    async def test_list_experiment_templates_with_pagination(self, mock_context, mock_aws_fis):
        """Test listing experiment templates with pagination."""
        # Setup mock responses for pagination
        mock_aws_fis.list_experiment_templates.side_effect = [
            {
                'experimentTemplates': [
                    {
                        'id': 'template-1',
                        'arn': 'arn:aws:fis:us-east-1:123456789012:experiment-template/template-1',
                        'description': 'Test Template 1',
                        'tags': {'Name': 'Test Template 1'},
                    }
                ],
                'nextToken': 'token1',
            },
            {
                'experimentTemplates': [
                    {
                        'id': 'template-2',
                        'arn': 'arn:aws:fis:us-east-1:123456789012:experiment-template/template-2',
                        'description': 'Test Template 2',
                        'tags': {'Name': 'Test Template 2'},
                    }
                ]
            },
        ]

        # Call the method
        result = await AwsFisActions.list_experiment_templates()

        # Verify the result
        self.assertEqual(len(result), 2)
        self.assertEqual(result[0]['id'], 'template-1')
        self.assertEqual(result[1]['id'], 'template-2')

        # Verify the AWS client was called correctly
        self.assertEqual(mock_aws_fis.list_experiment_templates.call_count, 2)
        mock_aws_fis.list_experiment_templates.assert_any_call()
        mock_aws_fis.list_experiment_templates.assert_any_call(nextToken='token1')

    @patch('awslabs.aws_fis_mcp_server.server.aws_fis')
    @patch('awslabs.aws_fis_mcp_server.server.Context')
    async def test_get_experiment_template_success(self, mock_context, mock_aws_fis):
        """Test getting experiment template details successfully."""
        # Setup mock response
        template_id = 'template-1'
        mock_aws_fis.get_experiment_template.return_value = {
            'experimentTemplate': {
                'id': template_id,
                'arn': f'arn:aws:fis:us-east-1:123456789012:experiment-template/{template_id}',
                'description': 'Test Template',
                'tags': {'Name': 'Test Template'},
            }
        }

        # Call the method
        result = await AwsFisActions.get_experiment_template(id=template_id)

        # Verify the result
        self.assertIn('experimentTemplate', result)
        self.assertEqual(result['experimentTemplate']['id'], template_id)

        # Verify the AWS client was called correctly
        mock_aws_fis.get_experiment_template.assert_called_once_with(id=template_id)

    @patch('awslabs.aws_fis_mcp_server.server.aws_fis')
    @patch('awslabs.aws_fis_mcp_server.server.Context')
    async def test_start_experiment_success(self, mock_context, mock_aws_fis):
        """Test starting an experiment successfully."""
        # Setup mock responses
        template_id = 'template-1'
        experiment_id = 'exp-1'

        # Mock start_experiment response
        mock_aws_fis.start_experiment.return_value = {
            'experiment': {
                'id': experiment_id,
                'arn': f'arn:aws:fis:us-east-1:123456789012:experiment/{experiment_id}',
                'experimentTemplateId': template_id,
                'state': {'status': 'pending'},
            }
        }

        # Mock get_experiment responses for polling
        mock_aws_fis.get_experiment.side_effect = [
            {'experiment': {'id': experiment_id, 'state': {'status': 'pending'}}},
            {'experiment': {'id': experiment_id, 'state': {'status': 'initiating'}}},
            {'experiment': {'id': experiment_id, 'state': {'status': 'running'}}},
            {'experiment': {'id': experiment_id, 'state': {'status': 'completed'}}},
        ]

        # Mock Context methods
        mock_context.info = AsyncMock()

        # Call the method with minimal parameters
        result = await AwsFisActions.start_experiment(
            id=template_id,
            max_timeout_seconds=10,  # Short timeout for test
            initial_poll_interval=0.1,  # Short poll interval for test
        )

        # Verify the result
        self.assertEqual(result['id'], experiment_id)
        self.assertEqual(result['state']['status'], 'completed')

        # Verify the AWS client was called correctly
        mock_aws_fis.start_experiment.assert_called_once_with(
            experimentTemplateId=template_id, experimentOptions={'actionsMode': 'run-all'}, tags={}
        )
        self.assertEqual(mock_aws_fis.get_experiment.call_count, 4)

    @patch('awslabs.aws_fis_mcp_server.server.aws_fis')
    @patch('awslabs.aws_fis_mcp_server.server.Context')
    async def test_start_experiment_failure(self, mock_context, mock_aws_fis):
        """Test handling a failed experiment."""
        # Setup mock responses
        template_id = 'template-1'
        experiment_id = 'exp-1'

        # Mock start_experiment response
        mock_aws_fis.start_experiment.return_value = {
            'experiment': {
                'id': experiment_id,
                'arn': f'arn:aws:fis:us-east-1:123456789012:experiment/{experiment_id}',
                'experimentTemplateId': template_id,
                'state': {'status': 'pending'},
            }
        }

        # Mock get_experiment responses for polling - experiment fails
        mock_aws_fis.get_experiment.side_effect = [
            {'experiment': {'id': experiment_id, 'state': {'status': 'pending'}}},
            {'experiment': {'id': experiment_id, 'state': {'status': 'running'}}},
            {
                'experiment': {
                    'id': experiment_id,
                    'state': {'status': 'failed', 'reason': 'Test failure'},
                }
            },
        ]

        # Mock Context methods
        mock_context.info = AsyncMock()
        mock_context.error = AsyncMock()

        # Call the method and expect an exception
        with self.assertRaises(Exception) as context:
            await AwsFisActions.start_experiment(
                id=template_id,
                max_timeout_seconds=10,  # Short timeout for test
                initial_poll_interval=0.1,  # Short poll interval for test
            )

        # Verify the exception message
        self.assertIn('Experiment failed', str(context.exception))

        # Verify the AWS client was called correctly
        mock_aws_fis.start_experiment.assert_called_once()
        self.assertEqual(mock_aws_fis.get_experiment.call_count, 3)
        mock_context.error.assert_called()

    @patch('awslabs.aws_fis_mcp_server.server.aws_fis')
    @patch('awslabs.aws_fis_mcp_server.server.Context')
    async def test_start_experiment_timeout(self, mock_context, mock_aws_fis):
        """Test experiment timeout handling."""
        # Setup mock responses
        template_id = 'template-1'
        experiment_id = 'exp-1'

        # Mock start_experiment response
        mock_aws_fis.start_experiment.return_value = {
            'experiment': {
                'id': experiment_id,
                'arn': f'arn:aws:fis:us-east-1:123456789012:experiment/{experiment_id}',
                'experimentTemplateId': template_id,
                'state': {'status': 'pending'},
            }
        }

        # Mock get_experiment to always return running state
        mock_aws_fis.get_experiment.return_value = {
            'experiment': {'id': experiment_id, 'state': {'status': 'running'}}
        }

        # Mock Context methods
        mock_context.info = AsyncMock()
        mock_context.error = AsyncMock()

        # Call the method and expect a timeout
        with self.assertRaises(TimeoutError):
            await AwsFisActions.start_experiment(
                id=template_id,
                max_timeout_seconds=0.5,  # Very short timeout for test
                initial_poll_interval=0.1,  # Short poll interval for test
            )

        # Verify the AWS client was called correctly
        mock_aws_fis.start_experiment.assert_called_once()
        mock_context.error.assert_called()


if __name__ == '__main__':
    unittest.main()
