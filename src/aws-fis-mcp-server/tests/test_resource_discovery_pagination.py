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

"""Tests for pagination handling in ResourceDiscovery class methods."""

import unittest

# Import the class to test
from awslabs.aws_fis_mcp_server.server import ResourceDiscovery
from unittest.mock import MagicMock, patch


class TestResourceDiscoveryPagination(unittest.TestCase):
    """Test cases for pagination handling in ResourceDiscovery class methods."""

    @patch('awslabs.aws_fis_mcp_server.server.resource_explorer')
    @patch('awslabs.aws_fis_mcp_server.server.Context')
    async def test_list_views_with_pagination(self, mock_context, mock_resource_explorer):
        """Test listing views with pagination."""
        # Setup mock responses for pagination
        mock_resource_explorer.list_views.side_effect = [
            {
                'Views': [
                    {
                        'ViewArn': 'arn:aws:resource-explorer-2:us-east-1:123456789012:view/view-1',
                        'ViewName': 'view-1',
                        'Filters': {'FilterString': 'service:ec2'},
                    }
                ],
                'NextToken': 'token1',
            },
            {
                'Views': [
                    {
                        'ViewArn': 'arn:aws:resource-explorer-2:us-east-1:123456789012:view/view-2',
                        'ViewName': 'view-2',
                        'Filters': {'FilterString': 'service:s3'},
                    }
                ]
            },
        ]

        # Call the method
        result = await ResourceDiscovery.list_views()

        # Verify the result
        self.assertEqual(len(result), 2)
        self.assertEqual(result[0]['ViewName'], 'view-1')
        self.assertEqual(result[1]['ViewName'], 'view-2')

        # Verify the AWS client was called correctly
        self.assertEqual(mock_resource_explorer.list_views.call_count, 2)
        mock_resource_explorer.list_views.assert_any_call()
        mock_resource_explorer.list_views.assert_any_call(NextToken='token1')

    @patch('awslabs.aws_fis_mcp_server.server.resource_explorer')
    @patch('awslabs.aws_fis_mcp_server.server.Context')
    async def test_discover_resources_resource_explorer_pagination(
        self, mock_context, mock_resource_explorer
    ):
        """Test discovering resources from Resource Explorer with pagination."""
        # Setup mock responses for pagination
        mock_resource_explorer.search.side_effect = [
            {
                'Resources': [
                    {
                        'Service': 'ec2',
                        'Region': 'us-east-1',
                        'ResourceType': 'instance',
                        'Arn': 'arn:aws:ec2:us-east-1:123456789012:instance/i-1',
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
        result = await ResourceDiscovery.discover_resources(
            source='resource-explorer', max_results=10
        )

        # Verify the result
        self.assertIn('resources', result)
        self.assertEqual(len(result['resources']), 2)
        
        # Check first resource
        self.assertEqual(result['resources'][0]['source'], 'resource-explorer')
        self.assertEqual(result['resources'][0]['service'], 'ec2')
        self.assertEqual(result['resources'][0]['resource_type'], 'instance')
        
        # Check second resource
        self.assertEqual(result['resources'][1]['source'], 'resource-explorer')
        self.assertEqual(result['resources'][1]['service'], 's3')
        self.assertEqual(result['resources'][1]['resource_type'], 'bucket')

        # Verify metadata
        self.assertIn('metadata', result)
        self.assertEqual(result['metadata']['total_resources'], 2)
        self.assertEqual(result['metadata']['sources_used'], 'resource-explorer')

        # Verify the AWS client was called correctly
        self.assertEqual(mock_resource_explorer.search.call_count, 2)
        mock_resource_explorer.search.assert_any_call(MaxResults=10)
        mock_resource_explorer.search.assert_any_call(MaxResults=10, NextToken='token1')


if __name__ == '__main__':
    unittest.main()