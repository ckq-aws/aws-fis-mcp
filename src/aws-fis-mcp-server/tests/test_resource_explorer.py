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

"""Tests for the ResourceExplorer class in the server module."""

import unittest
from awslabs.aws_fis_mcp_server.consts import DEFAULT_MAX_RESOURCES

# Import the class to test
from awslabs.aws_fis_mcp_server.server import ResourceExplorer
from botocore.exceptions import ClientError
from unittest.mock import MagicMock, patch


class TestResourceExplorer(unittest.TestCase):
    """Test cases for the ResourceExplorer class."""

    @patch('awslabs.aws_fis_mcp_server.server.resource_explorer')
    @patch('awslabs.aws_fis_mcp_server.server.Context')
    async def test_list_resources_no_pagination(self, mock_context, mock_resource_explorer):
        """Test listing resources without pagination."""
        # Setup mock response
        mock_resource_explorer.list_resources.return_value = {
            'Resources': [
                {
                    'Service': 'ec2',
                    'Region': 'us-east-1',
                    'ResourceType': 'instance',
                    'Arn': 'arn:aws:ec2:us-east-1:123456789012:instance/i-12345678901234567',
                }
            ]
        }

        # Call the method
        result = await ResourceExplorer.list_resources()

        # Verify the result
        self.assertIn('resources', result)
        self.assertEqual(len(result['resources']), 1)
        self.assertEqual(result['resources'][0]['service'], 'ec2')
        self.assertEqual(result['resources'][0]['resource_type'], 'instance')

        # Verify the AWS client was called correctly
        mock_resource_explorer.list_resources.assert_called_once_with(
            MaxResults=DEFAULT_MAX_RESOURCES
        )

    @patch('awslabs.aws_fis_mcp_server.server.resource_explorer')
    @patch('awslabs.aws_fis_mcp_server.server.Context')
    async def test_list_resources_with_pagination(self, mock_context, mock_resource_explorer):
        """Test listing resources with pagination."""
        # Setup mock responses for pagination
        mock_resource_explorer.list_resources.side_effect = [
            {
                'Resources': [
                    {
                        'Service': 'ec2',
                        'Region': 'us-east-1',
                        'ResourceType': 'instance',
                        'Arn': 'arn:aws:ec2:us-east-1:123456789012:instance/i-12345678901234567',
                    }
                ],
                'NextToken': 'token1',
            },
            {
                'Resources': [
                    {
                        'Service': 's3',
                        'Region': 'us-east-1',
                        'ResourceType': 'bucket',
                        'Arn': 'arn:aws:s3:::test-bucket',
                    }
                ]
            },
        ]

        # Call the method
        result = await ResourceExplorer.list_resources()

        # Verify the result
        self.assertIn('resources', result)
        self.assertEqual(len(result['resources']), 2)
        self.assertEqual(result['resources'][0]['service'], 'ec2')
        self.assertEqual(result['resources'][1]['service'], 's3')

        # Verify the AWS client was called correctly
        self.assertEqual(mock_resource_explorer.list_resources.call_count, 2)
        mock_resource_explorer.list_resources.assert_any_call(MaxResults=DEFAULT_MAX_RESOURCES)
        mock_resource_explorer.list_resources.assert_any_call(
            MaxResults=DEFAULT_MAX_RESOURCES, NextToken='token1'
        )

    @patch('awslabs.aws_fis_mcp_server.server.resource_explorer')
    @patch('awslabs.aws_fis_mcp_server.server.Context')
    async def test_list_resources_custom_limit(self, mock_context, mock_resource_explorer):
        """Test listing resources with a custom limit."""
        # Setup mock response
        mock_resource_explorer.list_resources.return_value = {
            'Resources': [
                {
                    'Service': 'ec2',
                    'Region': 'us-east-1',
                    'ResourceType': 'instance',
                    'Arn': 'arn:aws:ec2:us-east-1:123456789012:instance/i-12345678901234567',
                }
            ]
        }

        # Call the method with a custom limit
        custom_limit = 50
        result = await ResourceExplorer.list_resources(num_resources=custom_limit)

        # Verify the result
        self.assertIn('resources', result)

        # Verify the AWS client was called correctly with the custom limit
        mock_resource_explorer.list_resources.assert_called_once_with(MaxResults=custom_limit)

    @patch('awslabs.aws_fis_mcp_server.server.resource_explorer')
    @patch('awslabs.aws_fis_mcp_server.server.Context')
    async def test_list_resources_error(self, mock_context, mock_resource_explorer):
        """Test error handling when listing resources."""
        # Setup mock to raise an exception
        mock_resource_explorer.list_resources.side_effect = ClientError(
            {'Error': {'Code': 'InternalServerError', 'Message': 'Test error'}}, 'list_resources'
        )
        mock_context.error = MagicMock()

        # Call the method and expect an exception
        with self.assertRaises(Exception):
            await ResourceExplorer.list_resources()

        # Verify error was logged
        mock_context.error.assert_called_once()

    @patch('awslabs.aws_fis_mcp_server.server.resource_explorer')
    @patch('awslabs.aws_fis_mcp_server.server.Context')
    async def test_list_views_no_pagination(self, mock_context, mock_resource_explorer):
        """Test listing views without pagination."""
        # Setup mock response
        mock_resource_explorer.list_views.return_value = {
            'Views': [
                {
                    'ViewArn': 'arn:aws:resource-explorer-2:us-east-1:123456789012:view/test-view',
                    'ViewName': 'test-view',
                    'Filters': {'FilterString': 'service:ec2'},
                    'IncludedProperties': ['tags'],
                    'LastUpdatedAt': '2023-01-01T00:00:00.000Z',
                }
            ]
        }

        # Call the method
        result = await ResourceExplorer.list_views()

        # Verify the result
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0]['ViewName'], 'test-view')

        # Verify the AWS client was called correctly
        mock_resource_explorer.list_views.assert_called_once()

    @patch('awslabs.aws_fis_mcp_server.server.resource_explorer')
    @patch('awslabs.aws_fis_mcp_server.server.Context')
    async def test_list_views_with_pagination(self, mock_context, mock_resource_explorer):
        """Test listing views with pagination."""
        # Setup mock responses for pagination
        mock_resource_explorer.list_views.side_effect = [
            {
                'Views': [
                    {
                        'ViewArn': 'arn:aws:resource-explorer-2:us-east-1:123456789012:view/test-view-1',
                        'ViewName': 'test-view-1',
                        'Filters': {'FilterString': 'service:ec2'},
                        'IncludedProperties': ['tags'],
                        'LastUpdatedAt': '2023-01-01T00:00:00.000Z',
                    }
                ],
                'NextToken': 'token1',
            },
            {
                'Views': [
                    {
                        'ViewArn': 'arn:aws:resource-explorer-2:us-east-1:123456789012:view/test-view-2',
                        'ViewName': 'test-view-2',
                        'Filters': {'FilterString': 'service:s3'},
                        'IncludedProperties': ['tags'],
                        'LastUpdatedAt': '2023-01-02T00:00:00.000Z',
                    }
                ]
            },
        ]

        # Call the method
        result = await ResourceExplorer.list_views()

        # Verify the result
        self.assertEqual(len(result), 2)
        self.assertEqual(result[0]['ViewName'], 'test-view-1')
        self.assertEqual(result[1]['ViewName'], 'test-view-2')

        # Verify the AWS client was called correctly
        self.assertEqual(mock_resource_explorer.list_views.call_count, 2)
        mock_resource_explorer.list_views.assert_any_call()
        mock_resource_explorer.list_views.assert_any_call(NextToken='token1')

    @patch('awslabs.aws_fis_mcp_server.server.resource_explorer')
    @patch('awslabs.aws_fis_mcp_server.server.Context')
    async def test_list_views_error(self, mock_context, mock_resource_explorer):
        """Test error handling when listing views."""
        # Setup mock to raise an exception
        mock_resource_explorer.list_views.side_effect = ClientError(
            {'Error': {'Code': 'InternalServerError', 'Message': 'Test error'}}, 'list_views'
        )
        mock_context.error = MagicMock()

        # Call the method and expect an exception
        with self.assertRaises(Exception):
            await ResourceExplorer.list_views()

        # Verify error was logged
        mock_context.error.assert_called_once()

    @patch('awslabs.aws_fis_mcp_server.server.resource_explorer')
    @patch('awslabs.aws_fis_mcp_server.server.Context')
    @patch('awslabs.aws_fis_mcp_server.server.time.time')
    async def test_create_view_minimal(self, mock_time, mock_context, mock_resource_explorer):
        """Test creating a view with minimal parameters."""
        # Setup mock response
        mock_resource_explorer.create_view.return_value = {
            'View': {
                'ViewArn': 'arn:aws:resource-explorer-2:us-east-1:123456789012:view/test-view',
                'ViewName': 'test-view',
                'Filters': {'FilterString': 'service:ec2'},
                'IncludedProperties': ['tags'],
                'LastUpdatedAt': '2023-01-01T00:00:00.000Z',
            }
        }

        # Mock time.time() to return a fixed value
        mock_time.return_value = 1672531200  # 2023-01-01T00:00:00.000Z

        # Call the method with minimal parameters
        result = await ResourceExplorer.create_view(query='service:ec2', view_name='test-view')

        # Verify the result
        self.assertIn('View', result)
        self.assertEqual(result['View']['ViewName'], 'test-view')
        self.assertEqual(result['View']['Filters']['FilterString'], 'service:ec2')

        # Verify the AWS client was called correctly
        mock_resource_explorer.create_view.assert_called_once_with(
            ClientToken='create-view-1672531200',
            Filters={'FilterString': 'service:ec2'},
            Scope=None,
            Tags={},
            ViewName='test-view',
        )

    @patch('awslabs.aws_fis_mcp_server.server.resource_explorer')
    @patch('awslabs.aws_fis_mcp_server.server.Context')
    async def test_create_view_full(self, mock_context, mock_resource_explorer):
        """Test creating a view with all parameters."""
        # Setup mock response
        mock_resource_explorer.create_view.return_value = {
            'View': {
                'ViewArn': 'arn:aws:resource-explorer-2:us-east-1:123456789012:view/test-view',
                'ViewName': 'test-view',
                'Filters': {'FilterString': 'service:ec2'},
                'IncludedProperties': ['tags'],
                'LastUpdatedAt': '2023-01-01T00:00:00.000Z',
            }
        }

        # Prepare test parameters
        query = 'service:ec2'
        view_name = 'test-view'
        tags = {'Name': 'Test View'}
        scope = 'arn:aws:iam::123456789012:root'
        client_token = 'test-token'

        # Call the method with all parameters
        result = await ResourceExplorer.create_view(
            query=query, view_name=view_name, tags=tags, scope=scope, client_token=client_token
        )

        # Verify the result
        self.assertIn('View', result)
        self.assertEqual(result['View']['ViewName'], view_name)

        # Verify the AWS client was called correctly
        mock_resource_explorer.create_view.assert_called_once_with(
            ClientToken=client_token,
            Filters={'FilterString': query},
            Scope=scope,
            Tags=tags,
            ViewName=view_name,
        )

    @patch('awslabs.aws_fis_mcp_server.server.resource_explorer')
    @patch('awslabs.aws_fis_mcp_server.server.Context')
    async def test_create_view_error(self, mock_context, mock_resource_explorer):
        """Test error handling when creating a view."""
        # Setup mock to raise an exception
        mock_resource_explorer.create_view.side_effect = ClientError(
            {'Error': {'Code': 'ValidationException', 'Message': 'Invalid query syntax'}},
            'create_view',
        )
        mock_context.error = MagicMock()

        # Call the method and expect an exception
        with self.assertRaises(Exception):
            await ResourceExplorer.create_view(query='invalid:query:syntax', view_name='test-view')

        # Verify error was logged
        mock_context.error.assert_called_once()


if __name__ == '__main__':
    unittest.main()
