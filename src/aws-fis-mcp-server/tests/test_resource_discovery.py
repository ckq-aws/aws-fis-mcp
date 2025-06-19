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

"""Tests for the ResourceDiscovery class in the server module."""

import unittest
from awslabs.aws_fis_mcp_server.consts import DEFAULT_MAX_RESOURCES

# Import the class to test
from awslabs.aws_fis_mcp_server.server import ResourceDiscovery
from unittest.mock import MagicMock, patch


class TestResourceDiscovery(unittest.TestCase):
    """Test cases for the ResourceDiscovery class."""

    @patch('awslabs.aws_fis_mcp_server.server.cloudformation')
    @patch('awslabs.aws_fis_mcp_server.server.Context')
    async def test_list_cfn_stacks_no_pagination(self, mock_context, mock_cloudformation):
        """Test listing CloudFormation stacks without pagination."""
        # Setup mock response
        mock_cloudformation.list_stacks.return_value = {
            'StackSummaries': [
                {
                    'StackId': 'arn:aws:cloudformation:us-east-1:123456789012:stack/test-stack/abc123',
                    'StackName': 'test-stack',
                    'TemplateDescription': 'Test stack',
                    'CreationTime': '2023-01-01T00:00:00.000Z',
                    'StackStatus': 'CREATE_COMPLETE',
                }
            ]
        }

        # Call the method
        result = await ResourceDiscovery.list_cfn_stacks()

        # Verify the result
        self.assertIn('stacks', result)
        self.assertEqual(len(result['stacks']), 1)
        self.assertEqual(result['stacks'][0]['StackName'], 'test-stack')
        self.assertEqual(result['stacks'][0]['StackStatus'], 'CREATE_COMPLETE')

        # Verify the AWS client was called correctly
        mock_cloudformation.list_stacks.assert_called_once()

    @patch('awslabs.aws_fis_mcp_server.server.cloudformation')
    @patch('awslabs.aws_fis_mcp_server.server.Context')
    async def test_get_stack_resources_no_pagination(self, mock_context, mock_cloudformation):
        """Test getting stack resources without pagination."""
        # Setup mock response
        stack_name = 'test-stack'
        mock_cloudformation.list_stack_resources.return_value = {
            'StackResourceSummaries': [
                {
                    'LogicalResourceId': 'TestInstance',
                    'PhysicalResourceId': 'i-12345678901234567',
                    'ResourceType': 'AWS::EC2::Instance',
                    'ResourceStatus': 'CREATE_COMPLETE',
                    'LastUpdatedTimestamp': '2023-01-01T00:00:00.000Z',
                }
            ]
        }

        # Call the method
        result = await ResourceDiscovery.get_stack_resources(stack_name=stack_name)

        # Verify the result
        self.assertIn('resources', result)
        self.assertEqual(len(result['resources']), 1)
        self.assertEqual(result['resources'][0]['LogicalResourceId'], 'TestInstance')
        self.assertEqual(result['resources'][0]['ResourceType'], 'AWS::EC2::Instance')

        # Verify the AWS client was called correctly
        mock_cloudformation.list_stack_resources.assert_called_once_with(StackName=stack_name)

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
        result = await ResourceDiscovery.list_views()

        # Verify the result
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0]['ViewName'], 'test-view')

        # Verify the AWS client was called correctly
        mock_resource_explorer.list_views.assert_called_once()

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
        result = await ResourceDiscovery.create_view(query='service:ec2', view_name='test-view')

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

    @patch('awslabs.aws_fis_mcp_server.server.ResourceDiscovery.get_stack_resources')
    @patch('awslabs.aws_fis_mcp_server.server.resource_explorer')
    @patch('awslabs.aws_fis_mcp_server.server.Context')
    async def test_discover_resources_cloudformation_only(
        self, mock_context, mock_resource_explorer, mock_get_stack_resources
    ):
        """Test discovering resources from CloudFormation only."""
        # Setup mock response for get_stack_resources
        stack_name = 'test-stack'
        mock_get_stack_resources.return_value = {
            'resources': [
                {
                    'LogicalResourceId': 'TestInstance',
                    'PhysicalResourceId': 'i-12345678901234567',
                    'ResourceType': 'AWS::EC2::Instance',
                    'ResourceStatus': 'CREATE_COMPLETE',
                    'LastUpdatedTimestamp': '2023-01-01T00:00:00.000Z',
                }
            ]
        }

        # Call the method
        result = await ResourceDiscovery.discover_resources(
            source='cloudformation', stack_name=stack_name
        )

        # Verify the result
        self.assertIn('resources', result)
        self.assertEqual(len(result['resources']), 1)
        self.assertEqual(result['resources'][0]['source'], 'cloudformation')
        self.assertEqual(result['resources'][0]['stack_name'], stack_name)
        self.assertEqual(result['resources'][0]['resource_type'], 'AWS::EC2::Instance')
        self.assertEqual(result['resources'][0]['logical_id'], 'TestInstance')

        # Verify metadata
        self.assertIn('metadata', result)
        self.assertEqual(result['metadata']['total_resources'], 1)
        self.assertEqual(result['metadata']['sources_used'], 'cloudformation')

        # Verify the mock was called correctly
        mock_get_stack_resources.assert_called_once_with(stack_name)
        mock_resource_explorer.search.assert_not_called()

    @patch('awslabs.aws_fis_mcp_server.server.resource_explorer')
    @patch('awslabs.aws_fis_mcp_server.server.Context')
    async def test_discover_resources_resource_explorer_only(
        self, mock_context, mock_resource_explorer
    ):
        """Test discovering resources from Resource Explorer only."""
        # Setup mock response for resource_explorer.search
        mock_resource_explorer.search.return_value = {
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
        result = await ResourceDiscovery.discover_resources(source='resource-explorer')

        # Verify the result
        self.assertIn('resources', result)
        self.assertEqual(len(result['resources']), 1)
        self.assertEqual(result['resources'][0]['source'], 'resource-explorer')
        self.assertEqual(result['resources'][0]['service'], 'ec2')
        self.assertEqual(result['resources'][0]['resource_type'], 'instance')
        self.assertEqual(
            result['resources'][0]['arn'],
            'arn:aws:ec2:us-east-1:123456789012:instance/i-12345678901234567',
        )

        # Verify metadata
        self.assertIn('metadata', result)
        self.assertEqual(result['metadata']['total_resources'], 1)
        self.assertEqual(result['metadata']['sources_used'], 'resource-explorer')

        # Verify the mock was called correctly
        mock_resource_explorer.search.assert_called_once_with(MaxResults=DEFAULT_MAX_RESOURCES)

    @patch('awslabs.aws_fis_mcp_server.server.ResourceDiscovery.list_cfn_stacks')
    @patch('awslabs.aws_fis_mcp_server.server.ResourceDiscovery.get_stack_resources')
    @patch('awslabs.aws_fis_mcp_server.server.resource_explorer')
    @patch('awslabs.aws_fis_mcp_server.server.Context')
    async def test_discover_resources_all_sources(
        self, mock_context, mock_resource_explorer, mock_get_stack_resources, mock_list_cfn_stacks
    ):
        """Test discovering resources from all sources."""
        # Setup mock responses
        mock_list_cfn_stacks.return_value = {
            'stacks': [
                {
                    'StackId': 'arn:aws:cloudformation:us-east-1:123456789012:stack/test-stack/abc123',
                    'StackName': 'test-stack',
                    'TemplateDescription': 'Test stack',
                    'CreationTime': '2023-01-01T00:00:00.000Z',
                    'StackStatus': 'CREATE_COMPLETE',
                }
            ]
        }

        mock_get_stack_resources.return_value = {
            'resources': [
                {
                    'LogicalResourceId': 'TestInstance',
                    'PhysicalResourceId': 'i-12345678901234567',
                    'ResourceType': 'AWS::EC2::Instance',
                    'ResourceStatus': 'CREATE_COMPLETE',
                    'LastUpdatedTimestamp': '2023-01-01T00:00:00.000Z',
                }
            ]
        }

        mock_resource_explorer.search.return_value = {
            'Resources': [
                {
                    'Service': 's3',
                    'Region': 'us-east-1',
                    'ResourceType': 'bucket',
                    'Arn': 'arn:aws:s3:::test-bucket',
                }
            ]
        }

        # Call the method
        result = await ResourceDiscovery.discover_resources(source='all', max_results=10)

        # Verify the result
        self.assertIn('resources', result)
        self.assertEqual(
            len(result['resources']), 2
        )  # 1 from CloudFormation, 1 from Resource Explorer

        # Check CloudFormation resource
        cfn_resource = next(r for r in result['resources'] if r['source'] == 'cloudformation')
        self.assertEqual(cfn_resource['stack_name'], 'test-stack')
        self.assertEqual(cfn_resource['resource_type'], 'AWS::EC2::Instance')

        # Check Resource Explorer resource
        re_resource = next(r for r in result['resources'] if r['source'] == 'resource-explorer')
        self.assertEqual(re_resource['service'], 's3')
        self.assertEqual(re_resource['resource_type'], 'bucket')

        # Verify metadata
        self.assertIn('metadata', result)
        self.assertEqual(result['metadata']['total_resources'], 2)
        self.assertEqual(result['metadata']['sources_used'], 'all')
        self.assertEqual(result['metadata']['max_results'], 10)

        # Verify the mocks were called correctly
        mock_list_cfn_stacks.assert_called_once()
        mock_get_stack_resources.assert_called_once_with('test-stack')
        mock_resource_explorer.search.assert_called_once_with(MaxResults=5)  # Half of max_results

    @patch('awslabs.aws_fis_mcp_server.server.Context')
    async def test_discover_resources_invalid_source(self, mock_context):
        """Test discovering resources with an invalid source."""
        mock_context.error = MagicMock()

        # Call the method with an invalid source and expect an exception
        with self.assertRaises(ValueError):
            await ResourceDiscovery.discover_resources(source='invalid-source')

    @patch('awslabs.aws_fis_mcp_server.server.Context')
    async def test_discover_resources_missing_stack_name(self, mock_context):
        """Test discovering resources from CloudFormation without a stack name."""
        mock_context.error = MagicMock()

        # Call the method without a stack name and expect an exception
        with self.assertRaises(ValueError):
            await ResourceDiscovery.discover_resources(source='cloudformation')

        # Verify error was logged
        mock_context.error.assert_called_once()


if __name__ == '__main__':
    unittest.main()
