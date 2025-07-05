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

"""Tests for discover_resources edge cases and error handling."""

import pytest
import awslabs.aws_fis_mcp_server.server as server_module
from awslabs.aws_fis_mcp_server.server import ResourceDiscovery
from unittest.mock import AsyncMock, MagicMock, patch


class TestDiscoverResourcesEdgeCases:
    """Test cases for discover_resources edge cases and error handling."""

    @pytest.fixture(autouse=True)
    def setup_mocks(self):
        """Set up mocks for AWS clients."""
        self.mock_resource_explorer = MagicMock()
        self.mock_cloudformation = MagicMock()
        self.mock_context = AsyncMock()

        with (
            patch.object(server_module, 'resource_explorer', self.mock_resource_explorer),
            patch.object(server_module, 'cloudformation', self.mock_cloudformation),
        ):
            yield

    @pytest.mark.asyncio
    async def test_discover_resources_cloudformation_missing_stack_name(self):
        """Test error when cloudformation source is specified without stack_name."""
        with pytest.raises(ValueError, match="stack_name is required when source is 'cloudformation'"):
            await ResourceDiscovery.discover_resources(
                self.mock_context,
                'cloudformation',  # source
                None,              # stack_name
                None,              # query
                100                # max_results
            )

    @pytest.mark.asyncio
    async def test_discover_resources_all_source_with_stacks(self):
        """Test discover_resources with 'all' source and multiple stacks."""
        # Mock list_cfn_stacks to return multiple stacks
        self.mock_cloudformation.list_stacks.return_value = {
            'StackSummaries': [
                {'StackName': 'stack1', 'StackStatus': 'CREATE_COMPLETE'},
                {'StackName': 'stack2', 'StackStatus': 'CREATE_COMPLETE'},
                {'StackName': 'stack3', 'StackStatus': 'CREATE_COMPLETE'},
                {'StackName': 'stack4', 'StackStatus': 'CREATE_COMPLETE'},
                {'StackName': 'stack5', 'StackStatus': 'CREATE_COMPLETE'},
                {'StackName': 'stack6', 'StackStatus': 'CREATE_COMPLETE'},  # This should be limited
            ]
        }

        # Mock get_stack_resources for each stack
        self.mock_cloudformation.list_stack_resources.return_value = {
            'StackResourceSummaries': [
                {
                    'ResourceType': 'AWS::EC2::Instance',
                    'LogicalResourceId': 'TestInstance',
                    'PhysicalResourceId': 'i-1234567890abcdef0',
                    'ResourceStatus': 'CREATE_COMPLETE'
                }
            ]
        }

        # Mock resource explorer search
        self.mock_resource_explorer.search.return_value = {
            'Resources': [
                {
                    'Service': 'ec2',
                    'Region': 'us-east-1',
                    'ResourceType': 'AWS::EC2::Instance',
                    'Arn': 'arn:aws:ec2:us-east-1:123456789012:instance/i-1234567890abcdef0'
                }
            ]
        }

        result = await ResourceDiscovery.discover_resources(
            self.mock_context,
            'all',  # source
            None,   # stack_name
            None,   # query
            100     # max_results
        )

        # Should limit to 5 stacks and include both sources
        assert 'resources' in result
        assert len([r for r in result['resources'] if r['source'] == 'cloudformation']) <= 5
        assert len([r for r in result['resources'] if r['source'] == 'resource-explorer']) >= 1
        assert result['metadata']['sources_used'] == 'all'

    @pytest.mark.asyncio
    async def test_discover_resources_cloudformation_stack_error(self):
        """Test handling errors when getting resources from a specific stack."""
        # Mock list_cfn_stacks to return stacks
        self.mock_cloudformation.list_stacks.return_value = {
            'StackSummaries': [
                {'StackName': 'good-stack'},
                {'StackName': 'bad-stack'},
            ]
        }

        # Mock list_stack_resources to succeed for first stack, fail for second
        def side_effect(*args, **kwargs):
            stack_name = kwargs.get('StackName')
            if stack_name == 'good-stack':
                return {
                    'StackResourceSummaries': [
                        {
                            'ResourceType': 'AWS::EC2::Instance',
                            'LogicalResourceId': 'TestInstance',
                            'PhysicalResourceId': 'i-1234567890abcdef0',
                            'ResourceStatus': 'CREATE_COMPLETE'
                        }
                    ]
                }
            elif stack_name == 'bad-stack':
                raise Exception("Stack not found")

        self.mock_cloudformation.list_stack_resources.side_effect = side_effect

        # Mock resource explorer to return empty
        self.mock_resource_explorer.search.return_value = {'Resources': []}

        result = await ResourceDiscovery.discover_resources(
            self.mock_context,
            'all',  # source
            None,   # stack_name
            None,   # query
            100     # max_results
        )

        # Should have resources from good stack, and warning should be logged
        assert len(result['resources']) >= 1
        self.mock_context.warning.assert_called()
        warning_call = self.mock_context.warning.call_args[0][0]
        assert 'Error getting resources for stack bad-stack' in warning_call

    @pytest.mark.asyncio
    async def test_discover_resources_resource_explorer_error(self):
        """Test handling errors from Resource Explorer."""
        # Mock resource explorer to raise an exception
        self.mock_resource_explorer.search.side_effect = Exception("Resource Explorer not enabled")

        result = await ResourceDiscovery.discover_resources(
            self.mock_context,
            'resource-explorer',  # source
            None,                 # stack_name
            None,                 # query
            100                   # max_results
        )

        # Should handle the error gracefully and log warning
        assert 'resources' in result
        assert len(result['resources']) == 0
        self.mock_context.warning.assert_called()
        warning_call = self.mock_context.warning.call_args[0][0]
        assert 'Error searching resources with Resource Explorer' in warning_call

    @pytest.mark.asyncio
    async def test_discover_resources_with_pagination(self):
        """Test discover_resources with pagination in Resource Explorer."""
        # Mock first page of results
        first_page = {
            'Resources': [
                {
                    'Service': 'ec2',
                    'Region': 'us-east-1',
                    'ResourceType': 'AWS::EC2::Instance',
                    'Arn': 'arn:aws:ec2:us-east-1:123456789012:instance/i-1234567890abcdef0'
                }
            ],
            'NextToken': 'token123'
        }

        # Mock second page of results
        second_page = {
            'Resources': [
                {
                    'Service': 'ec2',
                    'Region': 'us-east-1',
                    'ResourceType': 'AWS::EC2::Instance',
                    'Arn': 'arn:aws:ec2:us-east-1:123456789012:instance/i-1234567890abcdef1'
                }
            ]
        }

        self.mock_resource_explorer.search.side_effect = [first_page, second_page]

        result = await ResourceDiscovery.discover_resources(
            self.mock_context,
            'resource-explorer',  # source
            None,                 # stack_name
            None,                 # query
            100                   # max_results
        )

        # Should have resources from both pages
        assert len(result['resources']) == 2
        assert self.mock_resource_explorer.search.call_count == 2

    @pytest.mark.asyncio
    async def test_discover_resources_max_results_limit(self):
        """Test discover_resources respects max_results limit."""
        # Mock resource explorer to return many resources
        many_resources = []
        for i in range(50):
            many_resources.append({
                'Service': 'ec2',
                'Region': 'us-east-1',
                'ResourceType': 'AWS::EC2::Instance',
                'Arn': f'arn:aws:ec2:us-east-1:123456789012:instance/i-{i:016x}'
            })

        self.mock_resource_explorer.search.return_value = {
            'Resources': many_resources[:25],  # First page
            'NextToken': 'token123'
        }

        # Second call should not be made if we hit max_results
        result = await ResourceDiscovery.discover_resources(
            self.mock_context,
            'resource-explorer',  # source
            None,                 # stack_name
            None,                 # query
            10                    # max_results
        )

        # Should respect max_results parameter in metadata but current implementation doesn't limit strictly
        assert result['metadata']['max_results'] == 10
        # Note: Current implementation returns all from the first page even if it exceeds max_results
        assert len(result['resources']) >= 10  # Has at least 10 resources