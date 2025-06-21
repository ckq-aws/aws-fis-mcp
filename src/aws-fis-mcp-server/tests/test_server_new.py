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

"""Tests for the create_resource_explorer_view function in the AWS FIS MCP server."""

import time
import pytest
from unittest.mock import MagicMock, patch, AsyncMock
from botocore.exceptions import ClientError

# Import the modules to test - mock the boto3 session and clients first
with patch('boto3.Session'):
    with patch('fastmcp.FastMCP'):  # Mock FastMCP to prevent decorator issues
        import awslabs.aws_fis_mcp_server.server as server_module


class TestResourceExplorerView:
    """Test cases for Resource Explorer view creation functionality."""
    
    @pytest.fixture(autouse=True)
    def setup_mocks(self):
        """Set up mocks for AWS clients and other dependencies."""
        # Create mock for AWS clients
        self.mock_resource_explorer = MagicMock()
        self.mock_context = AsyncMock()
        
        # Create patchers
        self.resource_explorer_patcher = patch.object(server_module, 'resource_explorer', self.mock_resource_explorer)
        self.context_patcher = patch.object(server_module, 'Context', self.mock_context)
        self.time_patcher = patch.object(time, 'time')
        
        # Start all patchers
        self.resource_explorer_patcher.start()
        self.context_patcher.start()
        self.mock_time = self.time_patcher.start()
        
        yield
        
        # Stop all patchers
        self.resource_explorer_patcher.stop()
        self.context_patcher.stop()
        self.time_patcher.stop()
    
    @pytest.mark.asyncio
    async def test_create_resource_explorer_view_success(self):
        """Test creating a Resource Explorer view successfully."""
        # Setup mock response
        view_name = "test-view"
        query = "service:ec2"
        scope = "Local"
        tags = {"Environment": "Test", "Project": "FIS"}
        client_token = "test-token"
        
        expected_response = {
            "View": {
                "ViewArn": f"arn:aws:resource-explorer-2:us-east-1:123456789012:view/{view_name}",
                "ViewName": view_name,
                "Filters": {"FilterString": query},
                "IncludedProperties": [],
                "Scope": scope,
                "LastUpdatedAt": "2023-01-01T00:00:00.000Z",
                "Tags": tags
            }
        }
        
        self.mock_resource_explorer.create_view.return_value = expected_response
        
        # Call the function
        result = await server_module.create_resource_explorer_view(
            query=query,
            view_name=view_name,
            tags=tags,
            scope=scope,
            client_token=client_token
        )
        
        # Verify the result
        assert result == expected_response
        
        # Verify the AWS client was called correctly
        self.mock_resource_explorer.create_view.assert_called_once_with(
            ClientToken=client_token,
            Filters={"FilterString": query},
            Scope=scope,
            Tags=tags,
            ViewName=view_name
        )
    
    @pytest.mark.asyncio
    async def test_create_resource_explorer_view_with_default_client_token(self):
        """Test creating a Resource Explorer view with a generated client token."""
        # Setup mock response and time
        view_name = "test-view"
        query = "service:ec2"
        scope = "Local"
        tags = {"Environment": "Test"}
        
        # Mock time.time() to return a fixed value
        self.mock_time.return_value = 1609459200  # 2021-01-01 00:00:00
        
        expected_response = {
            "View": {
                "ViewArn": f"arn:aws:resource-explorer-2:us-east-1:123456789012:view/{view_name}",
                "ViewName": view_name
            }
        }
        
        self.mock_resource_explorer.create_view.return_value = expected_response
        
        # Call the function without providing a client token
        result = await server_module.create_resource_explorer_view(
            query=query,
            view_name=view_name,
            tags=tags,
            scope=scope
        )
        
        # Verify the result
        assert result == expected_response
        
        # Verify the AWS client was called with a generated client token
        self.mock_resource_explorer.create_view.assert_called_once_with(
            ClientToken=f'create-view-1609459200',
            Filters={"FilterString": query},
            Scope=scope,
            Tags=tags,
            ViewName=view_name
        )
    
    @pytest.mark.asyncio
    async def test_create_resource_explorer_view_with_default_tags(self):
        """Test creating a Resource Explorer view with default empty tags."""
        # Setup mock response
        view_name = "test-view"
        query = "service:ec2"
        scope = "Local"
        client_token = "test-token"
        
        expected_response = {
            "View": {
                "ViewArn": f"arn:aws:resource-explorer-2:us-east-1:123456789012:view/{view_name}",
                "ViewName": view_name
            }
        }
        
        self.mock_resource_explorer.create_view.return_value = expected_response
        
        # Call the function without providing tags
        result = await server_module.create_resource_explorer_view(
            query=query,
            view_name=view_name,
            scope=scope,
            client_token=client_token
        )
        
        # Verify the result
        assert result == expected_response
        
        # Verify the AWS client was called with empty tags
        self.mock_resource_explorer.create_view.assert_called_once_with(
            ClientToken=client_token,
            Filters={"FilterString": query},
            Scope=scope,
            Tags={},
            ViewName=view_name
        )
    
    @pytest.mark.asyncio
    async def test_create_resource_explorer_view_error(self):
        """Test error handling when creating a Resource Explorer view."""
        # Setup mock to raise an exception
        view_name = "test-view"
        query = "service:ec2"
        scope = "Local"
        client_token = "test-token"
        
        error_message = "Access denied"
        self.mock_resource_explorer.create_view.side_effect = ClientError(
            {'Error': {'Code': 'AccessDeniedException', 'Message': error_message}},
            'create_view'
        )
        
        # Call the function and expect an exception
        with pytest.raises(ClientError) as excinfo:
            await server_module.create_resource_explorer_view(
                query=query,
                view_name=view_name,
                scope=scope,
                client_token=client_token
            )
        
        # Verify the exception message contains the expected error
        assert error_message in str(excinfo.value)
        
        # Verify that Context.error was called for the error
        self.mock_context.error.assert_called_once()
        assert "Error creating Resource Explorer view" in self.mock_context.error.call_args[0][0]
        assert error_message in self.mock_context.error.call_args[0][0]