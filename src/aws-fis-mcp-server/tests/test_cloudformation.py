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

"""Tests for the CloudFormation class in the server module."""

import unittest
from unittest.mock import patch, MagicMock
from botocore.exceptions import ClientError

# Import the class to test
from awslabs.aws_fis_mcp_server.server import CloudFormation


class TestCloudFormation(unittest.TestCase):
    """Test cases for the CloudFormation class."""

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
                    'StackStatus': 'CREATE_COMPLETE'
                }
            ]
        }

        # Call the method
        result = await CloudFormation.list_cfn_stacks()

        # Verify the result
        self.assertIn('stacks', result)
        self.assertEqual(len(result['stacks']), 1)
        self.assertEqual(result['stacks'][0]['StackName'], 'test-stack')
        self.assertEqual(result['stacks'][0]['StackStatus'], 'CREATE_COMPLETE')
        
        # Verify the AWS client was called correctly
        mock_cloudformation.list_stacks.assert_called_once()

    @patch('awslabs.aws_fis_mcp_server.server.cloudformation')
    @patch('awslabs.aws_fis_mcp_server.server.Context')
    async def test_list_cfn_stacks_with_pagination(self, mock_context, mock_cloudformation):
        """Test listing CloudFormation stacks with pagination."""
        # Setup mock responses for pagination
        mock_cloudformation.list_stacks.side_effect = [
            {
                'StackSummaries': [
                    {
                        'StackId': 'arn:aws:cloudformation:us-east-1:123456789012:stack/test-stack-1/abc123',
                        'StackName': 'test-stack-1',
                        'TemplateDescription': 'Test stack 1',
                        'CreationTime': '2023-01-01T00:00:00.000Z',
                        'StackStatus': 'CREATE_COMPLETE'
                    }
                ],
                'NextToken': 'token1'
            },
            {
                'StackSummaries': [
                    {
                        'StackId': 'arn:aws:cloudformation:us-east-1:123456789012:stack/test-stack-2/def456',
                        'StackName': 'test-stack-2',
                        'TemplateDescription': 'Test stack 2',
                        'CreationTime': '2023-01-02T00:00:00.000Z',
                        'StackStatus': 'CREATE_COMPLETE'
                    }
                ]
            }
        ]

        # Call the method
        result = await CloudFormation.list_cfn_stacks()

        # Verify the result
        self.assertIn('stacks', result)
        self.assertEqual(len(result['stacks']), 2)
        self.assertEqual(result['stacks'][0]['StackName'], 'test-stack-1')
        self.assertEqual(result['stacks'][1]['StackName'], 'test-stack-2')
        
        # Verify the AWS client was called correctly
        self.assertEqual(mock_cloudformation.list_stacks.call_count, 2)
        mock_cloudformation.list_stacks.assert_any_call()
        mock_cloudformation.list_stacks.assert_any_call(NextToken='token1')

    @patch('awslabs.aws_fis_mcp_server.server.cloudformation')
    @patch('awslabs.aws_fis_mcp_server.server.Context')
    async def test_list_cfn_stacks_error(self, mock_context, mock_cloudformation):
        """Test error handling when listing CloudFormation stacks."""
        # Setup mock to raise an exception
        mock_cloudformation.list_stacks.side_effect = ClientError(
            {'Error': {'Code': 'InternalServerError', 'Message': 'Test error'}},
            'list_stacks'
        )
        mock_context.error = MagicMock()

        # Call the method and expect an exception
        with self.assertRaises(Exception):
            await CloudFormation.list_cfn_stacks()
        
        # Verify error was logged
        mock_context.error.assert_called_once()

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
                    'LastUpdatedTimestamp': '2023-01-01T00:00:00.000Z'
                }
            ]
        }

        # Call the method
        result = await CloudFormation.get_stack_resources(stack_name=stack_name)

        # Verify the result
        self.assertIn('resources', result)
        self.assertEqual(len(result['resources']), 1)
        self.assertEqual(result['resources'][0]['LogicalResourceId'], 'TestInstance')
        self.assertEqual(result['resources'][0]['ResourceType'], 'AWS::EC2::Instance')
        
        # Verify the AWS client was called correctly
        mock_cloudformation.list_stack_resources.assert_called_once_with(StackName=stack_name)

    @patch('awslabs.aws_fis_mcp_server.server.cloudformation')
    @patch('awslabs.aws_fis_mcp_server.server.Context')
    async def test_get_stack_resources_with_pagination(self, mock_context, mock_cloudformation):
        """Test getting stack resources with pagination."""
        # Setup mock responses for pagination
        stack_name = 'test-stack'
        mock_cloudformation.list_stack_resources.side_effect = [
            {
                'StackResourceSummaries': [
                    {
                        'LogicalResourceId': 'TestInstance1',
                        'PhysicalResourceId': 'i-12345678901234567',
                        'ResourceType': 'AWS::EC2::Instance',
                        'ResourceStatus': 'CREATE_COMPLETE',
                        'LastUpdatedTimestamp': '2023-01-01T00:00:00.000Z'
                    }
                ],
                'NextToken': 'token1'
            },
            {
                'StackResourceSummaries': [
                    {
                        'LogicalResourceId': 'TestInstance2',
                        'PhysicalResourceId': 'i-76543210987654321',
                        'ResourceType': 'AWS::EC2::Instance',
                        'ResourceStatus': 'CREATE_COMPLETE',
                        'LastUpdatedTimestamp': '2023-01-02T00:00:00.000Z'
                    }
                ]
            }
        ]

        # Call the method
        result = await CloudFormation.get_stack_resources(stack_name=stack_name)

        # Verify the result
        self.assertIn('resources', result)
        self.assertEqual(len(result['resources']), 2)
        self.assertEqual(result['resources'][0]['LogicalResourceId'], 'TestInstance1')
        self.assertEqual(result['resources'][1]['LogicalResourceId'], 'TestInstance2')
        
        # Verify the AWS client was called correctly
        self.assertEqual(mock_cloudformation.list_stack_resources.call_count, 2)
        mock_cloudformation.list_stack_resources.assert_any_call(StackName=stack_name)
        mock_cloudformation.list_stack_resources.assert_any_call(StackName=stack_name, NextToken='token1')

    @patch('awslabs.aws_fis_mcp_server.server.cloudformation')
    @patch('awslabs.aws_fis_mcp_server.server.Context')
    async def test_get_stack_resources_error(self, mock_context, mock_cloudformation):
        """Test error handling when getting stack resources."""
        # Setup mock to raise an exception
        stack_name = 'test-stack'
        mock_cloudformation.list_stack_resources.side_effect = ClientError(
            {'Error': {'Code': 'ValidationError', 'Message': 'Stack does not exist'}},
            'list_stack_resources'
        )
        mock_context.error = MagicMock()

        # Call the method and expect an exception
        with self.assertRaises(Exception):
            await CloudFormation.get_stack_resources(stack_name=stack_name)
        
        # Verify error was logged
        mock_context.error.assert_called_once()


if __name__ == "__main__":
    unittest.main()