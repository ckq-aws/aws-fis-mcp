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

"""Tests for the create_view method in ResourceDiscovery class."""

import unittest

# Import the class to test
from awslabs.aws_fis_mcp_server.server import ResourceDiscovery
from botocore.exceptions import ClientError
from unittest.mock import MagicMock, patch


class TestResourceDiscoveryCreateView(unittest.TestCase):
    """Test cases for the create_view method in ResourceDiscovery class."""

    @patch('awslabs.aws_fis_mcp_server.server.resource_explorer')
    @patch('awslabs.aws_fis_mcp_server.server.Context')
    async def test_create_view_with_all_parameters(self, mock_context, mock_resource_explorer):
        """Test creating a view with all parameters."""
        # Setup mock response
        mock_resource_explorer.create_view.return_value = {
            'View': {
                'ViewArn': 'arn:aws:resource-explorer-2:us-east-1:123456789012:view/test-view',
                'ViewName': 'test-view',
                'Filters': {'FilterString': 'service:ec2'},
                'IncludedProperties': ['tags'],
                'LastUpdatedAt': '2023-01-01T00:00:00.000Z',
                'Scope': 'arn:aws:iam::123456789012:root',
            }
        }

        # Prepare test parameters
        query = 'service:ec2'
        view_name = 'test-view'
        tags = {'Name': 'Test View', 'Environment': 'Test'}
        scope = 'arn:aws:iam::123456789012:root'
        client_token = 'test-token-123'

        # Call the method with all parameters
        result = await ResourceDiscovery.create_view(
            query=query,
            view_name=view_name,
            tags=tags,
            scope=scope,
            client_token=client_token
        )

        # Verify the result
        self.assertIn('View', result)
        self.assertEqual(result['View']['ViewName'], view_name)
        self.assertEqual(result['View']['Filters']['FilterString'], query)
        self.assertEqual(result['View']['Scope'], scope)

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
            {'Error': {'Code': 'ValidationException', 'Message': 'Invalid filter string'}},
            'create_view',
        )
        mock_context.error = MagicMock()

        # Call the method and expect an exception
        with self.assertRaises(Exception):
            await ResourceDiscovery.create_view(
                query='invalid:filter',
                view_name='test-view'
            )

        # Verify error was logged
        mock_context.error.assert_called_once()


if __name__ == '__main__':
    unittest.main()