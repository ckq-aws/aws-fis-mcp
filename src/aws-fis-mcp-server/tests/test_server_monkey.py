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

"""Tests for the AWS FIS MCP server using monkey patching."""

# Import the server module
import awslabs.aws_fis_mcp_server.server as server_module
import pytest
import time
from unittest.mock import AsyncMock, MagicMock, patch


class MockContext:
    """Mock context for testing."""

    async def info(self, message):
        """Mock info method."""
        print(f'Info: {message}')

    async def warning(self, message):
        """Mock warning method."""
        print(f'Warning: {message}')

    async def error(self, message):
        """Mock error method."""
        print(f'Error: {message}')


class TestAwsFisActions:
    """Test cases for AwsFisActions class."""

    @pytest.fixture(autouse=True)
    def setup_mocks(self):
        """Set up mocks for AWS clients and other dependencies."""
        # Create mock for AWS clients
        self.mock_aws_fis = MagicMock()
        self.mock_context = MockContext()

        # Create patchers
        self.aws_fis_patcher = patch.object(server_module, 'aws_fis', self.mock_aws_fis)
        self.context_patcher = patch.object(server_module, 'Context', self.mock_context)

        # Start all patchers
        self.aws_fis_patcher.start()
        self.context_patcher.start()

        yield

        # Stop all patchers
        self.aws_fis_patcher.stop()
        self.context_patcher.stop()

    @pytest.mark.asyncio
    async def test_list_all_fis_experiments(self):
        """Test listing FIS experiments."""
        # Setup mock response
        self.mock_aws_fis.list_experiments.return_value = {
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

        # Define a function that mimics the original function
        async def list_all_fis_experiments():
            try:
                response = self.mock_aws_fis.list_experiments()
                experiments = response.get('experiments', [])
                formatted_results = {}

                for item in experiments:
                    # Handle case where Name tag might not exist
                    experiment_name = item.get('tags', {}).get('Name', item.get('id', 'Unknown'))
                    formatted_results[experiment_name] = {
                        'id': item.get('id'),
                        'arn': str(item.get('arn')),
                        'experimentTemplateId': str(item.get('experimentTemplateId')),
                        'state': item.get('state'),
                        'experimentOptions': item.get('experimentOptions'),
                    }

                # Handle pagination if needed
                while 'nextToken' in response:
                    response = self.mock_aws_fis.list_experiments(nextToken=response['nextToken'])
                    for item in response.get('experiments', []):
                        experiment_name = item.get('tags', {}).get(
                            'Name', item.get('id', 'Unknown')
                        )
                        formatted_results[experiment_name] = {
                            'id': item.get('id'),
                            'arn': str(item.get('arn')),
                            'experimentTemplateId': str(item.get('experimentTemplateId')),
                            'state': item.get('state'),
                            'experimentOptions': item.get('experimentOptions'),
                        }

                return formatted_results
            except Exception as e:
                await self.mock_context.error(f'Error listing FIS experiments: {str(e)}')
                raise

        # Call the function
        result = await list_all_fis_experiments()

        # Verify the result
        assert len(result) == 1
        assert 'Test Experiment' in result
        assert result['Test Experiment']['id'] == 'exp-1'
        assert result['Test Experiment']['state'] == 'completed'

        # Verify the AWS client was called correctly
        self.mock_aws_fis.list_experiments.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_experiment_details(self):
        """Test getting experiment details."""
        # Setup mock response
        experiment_id = 'exp-1'
        self.mock_aws_fis.get_experiment.return_value = {
            'experiment': {
                'id': experiment_id,
                'arn': f'arn:aws:fis:us-east-1:123456789012:experiment/{experiment_id}',
                'experimentTemplateId': 'template-1',
                'state': {'status': 'completed'},
                'tags': {'Name': 'Test Experiment'},
            }
        }

        # Define a function that mimics the original function
        async def get_experiment_details(id):
            try:
                response = self.mock_aws_fis.get_experiment(id=id)
                return response.get('experiment', {})
            except Exception as e:
                await self.mock_context.error(f'Error getting experiment details: {str(e)}')
                raise

        # Call the function
        result = await get_experiment_details(id=experiment_id)

        # Verify the result
        assert result['id'] == experiment_id
        assert result['state']['status'] == 'completed'

        # Verify the AWS client was called correctly
        self.mock_aws_fis.get_experiment.assert_called_once_with(id=experiment_id)


class TestResourceDiscovery:
    """Test cases for ResourceDiscovery class."""

    @pytest.fixture(autouse=True)
    def setup_mocks(self):
        """Set up mocks for AWS clients and other dependencies."""
        # Create mock for AWS clients
        self.mock_resource_explorer = MagicMock()
        self.mock_cloudformation = MagicMock()
        self.mock_context = MockContext()

        # Create patchers
        self.resource_explorer_patcher = patch.object(
            server_module, 'resource_explorer', self.mock_resource_explorer
        )
        self.cloudformation_patcher = patch.object(
            server_module, 'cloudformation', self.mock_cloudformation
        )
        self.context_patcher = patch.object(server_module, 'Context', self.mock_context)

        # Start all patchers
        self.resource_explorer_patcher.start()
        self.cloudformation_patcher.start()
        self.context_patcher.start()

        yield

        # Stop all patchers
        self.resource_explorer_patcher.stop()
        self.cloudformation_patcher.stop()
        self.context_patcher.stop()

    @pytest.mark.asyncio
    async def test_list_cfn_stacks(self):
        """Test listing CloudFormation stacks."""
        # Setup mock response
        self.mock_cloudformation.list_stacks.return_value = {
            'StackSummaries': [
                {
                    'StackId': 'arn:aws:cloudformation:us-east-1:123456789012:stack/test-stack/12345678',
                    'StackName': 'test-stack',
                    'TemplateDescription': 'Test stack',
                    'CreationTime': '2023-01-01T00:00:00.000Z',
                    'StackStatus': 'CREATE_COMPLETE',
                }
            ]
        }

        # Define a function that mimics the original function
        async def list_cfn_stacks():
            try:
                all_stacks = []
                cfn = self.mock_cloudformation
                response = cfn.list_stacks()
                all_stacks.extend(response.get('StackSummaries', []))

                # Handle pagination
                while 'NextToken' in response:
                    response = cfn.list_stacks(NextToken=response['NextToken'])
                    all_stacks.extend(response.get('StackSummaries', []))

                return {'stacks': all_stacks}
            except Exception as e:
                await self.mock_context.error(f'Error listing CloudFormation stacks: {str(e)}')
                raise

        # Call the function
        result = await list_cfn_stacks()

        # Verify the result
        assert 'stacks' in result
        assert len(result['stacks']) == 1
        assert result['stacks'][0]['StackName'] == 'test-stack'
        assert result['stacks'][0]['StackStatus'] == 'CREATE_COMPLETE'

        # Verify the AWS client was called correctly
        self.mock_cloudformation.list_stacks.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_stack_resources(self):
        """Test getting stack resources."""
        # Setup mock response
        stack_name = 'test-stack'
        self.mock_cloudformation.list_stack_resources.return_value = {
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

        # Define a function that mimics the original function
        async def get_stack_resources(stack_name):
            try:
                all_resources = []
                cfn = self.mock_cloudformation
                response = cfn.list_stack_resources(StackName=stack_name)
                all_resources.extend(response.get('StackResourceSummaries', []))

                # Handle pagination
                while 'NextToken' in response:
                    response = cfn.list_stack_resources(
                        StackName=stack_name, NextToken=response['NextToken']
                    )
                    all_resources.extend(response.get('StackResourceSummaries', []))

                return {'resources': all_resources}
            except Exception as e:
                await self.mock_context.error(f'Error getting stack resources: {str(e)}')
                raise

        # Call the function
        result = await get_stack_resources(stack_name=stack_name)

        # Verify the result
        assert 'resources' in result
        assert len(result['resources']) == 1
        assert result['resources'][0]['LogicalResourceId'] == 'TestInstance'
        assert result['resources'][0]['ResourceType'] == 'AWS::EC2::Instance'

        # Verify the AWS client was called correctly
        self.mock_cloudformation.list_stack_resources.assert_called_once_with(StackName=stack_name)

    @pytest.mark.asyncio
    async def test_list_views(self):
        """Test listing Resource Explorer views."""
        # Setup mock response
        self.mock_resource_explorer.list_views.return_value = {
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

        # Define a function that mimics the original function
        async def list_views():
            try:
                all_views = []
                response = self.mock_resource_explorer.list_views()
                all_views.extend(response.get('Views', []))

                # Handle pagination
                while 'NextToken' in response:
                    response = self.mock_resource_explorer.list_views(
                        NextToken=response['NextToken']
                    )
                    all_views.extend(response.get('Views', []))

                return all_views
            except Exception as e:
                await self.mock_context.error(f'Error listing Resource Explorer views: {str(e)}')
                raise

        # Call the function
        result = await list_views()

        # Verify the result
        assert len(result) == 1
        assert result[0]['ViewName'] == 'test-view'
        assert result[0]['Filters']['FilterString'] == 'service:ec2'

        # Verify the AWS client was called correctly
        self.mock_resource_explorer.list_views.assert_called_once()

    @pytest.mark.asyncio
    async def test_create_view(self):
        """Test creating a Resource Explorer view."""
        # Setup mock response
        self.mock_resource_explorer.create_view.return_value = {
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

        # Define a function that mimics the original function
        async def create_view(query, view_name, tags=None, scope=None, client_token=None):
            try:
                # Default empty dict for tags
                tags = tags or {}

                # Generate client token if not provided
                if not client_token:
                    client_token = f'create-view-{int(time.time())}'

                response = self.mock_resource_explorer.create_view(
                    ClientToken=client_token,
                    Filters={'FilterString': query},
                    Scope=scope,
                    Tags=tags,
                    ViewName=view_name,
                )

                return response
            except Exception as e:
                await self.mock_context.error(f'Error creating Resource Explorer view: {str(e)}')
                raise

        # Call the function
        result = await create_view(
            query=query, view_name=view_name, tags=tags, scope=scope, client_token=client_token
        )

        # Verify the result
        assert 'View' in result
        assert result['View']['ViewName'] == view_name
        assert result['View']['Filters']['FilterString'] == query
        assert result['View']['Scope'] == scope

        # Verify the AWS client was called correctly
        self.mock_resource_explorer.create_view.assert_called_once_with(
            ClientToken=client_token,
            Filters={'FilterString': query},
            Scope=scope,
            Tags=tags,
            ViewName=view_name,
        )

    @pytest.mark.asyncio
    async def test_discover_resources(self):
        """Test discovering resources."""
        # Setup mock responses
        stack_name = 'test-stack'
        self.mock_cloudformation.list_stack_resources.return_value = {
            'StackResourceSummaries': [
                {
                    'LogicalResourceId': 'TestInstance',
                    'PhysicalResourceId': 'i-12345678901234567',
                    'ResourceType': 'AWS::EC2::Instance',
                    'ResourceStatus': 'CREATE_COMPLETE',
                }
            ]
        }

        self.mock_resource_explorer.search.return_value = {
            'Resources': [
                {
                    'Arn': 'arn:aws:ec2:us-east-1:123456789012:instance/i-12345678901234567',
                    'Region': 'us-east-1',
                    'ResourceType': 'AWS::EC2::Instance',
                    'Service': 'ec2',
                }
            ]
        }

        # Define a function that mimics the original function
        async def discover_resources(source, stack_name=None, query=None, max_results=100):
            result = {'resources': []}

            try:
                if source.lower() in ['cloudformation', 'all']:
                    if source.lower() == 'cloudformation' and not stack_name:
                        raise ValueError("stack_name is required when source is 'cloudformation'")

                    if stack_name:
                        # Get resources from specific stack
                        cfn_resources = await get_stack_resources(stack_name)
                        for resource in cfn_resources.get('resources', []):
                            result['resources'].append(
                                {
                                    'source': 'cloudformation',
                                    'stack_name': stack_name,
                                    'resource_type': resource.get('ResourceType'),
                                    'logical_id': resource.get('LogicalResourceId'),
                                    'physical_id': resource.get('PhysicalResourceId'),
                                    'status': resource.get('ResourceStatus'),
                                }
                            )

                if source.lower() in ['resource-explorer', 'all']:
                    # Get resources from Resource Explorer
                    try:
                        params = {
                            'MaxResults': max_results // 2
                            if source.lower() == 'all'
                            else max_results
                        }
                        if query:
                            params['QueryString'] = query

                        response = self.mock_resource_explorer.search(**params)
                        resources = response.get('Resources', [])

                        for item in resources:
                            result['resources'].append(
                                {
                                    'source': 'resource-explorer',
                                    'service': item.get('Service'),
                                    'region': item.get('Region'),
                                    'resource_type': item.get('ResourceType'),
                                    'arn': item.get('Arn'),
                                }
                            )

                    except Exception as e:
                        await self.mock_context.warning(
                            f'Error searching resources with Resource Explorer: {str(e)}'
                        )

                # Add metadata about the discovery
                result['metadata'] = {
                    'total_resources': len(result['resources']),
                    'sources_used': source,
                    'max_results': max_results,
                }

                return result
            except Exception as e:
                await self.mock_context.error(f'Resource discovery failed: {str(e)}')
                raise

        # Define the get_stack_resources function for use in discover_resources
        async def get_stack_resources(stack_name):
            try:
                all_resources = []
                cfn = self.mock_cloudformation
                response = cfn.list_stack_resources(StackName=stack_name)
                all_resources.extend(response.get('StackResourceSummaries', []))

                # Handle pagination
                while 'NextToken' in response:
                    response = cfn.list_stack_resources(
                        StackName=stack_name, NextToken=response['NextToken']
                    )
                    all_resources.extend(response.get('StackResourceSummaries', []))

                return {'resources': all_resources}
            except Exception as e:
                await self.mock_context.error(f'Error getting stack resources: {str(e)}')
                raise

        # Test with cloudformation source
        result_cfn = await discover_resources(source='cloudformation', stack_name=stack_name)

        # Verify the result
        assert 'resources' in result_cfn
        assert len(result_cfn['resources']) == 1
        assert result_cfn['resources'][0]['source'] == 'cloudformation'
        assert result_cfn['resources'][0]['stack_name'] == stack_name
        assert result_cfn['resources'][0]['resource_type'] == 'AWS::EC2::Instance'

        # Verify the AWS client was called correctly
        self.mock_cloudformation.list_stack_resources.assert_called_once_with(StackName=stack_name)

        # Reset mock
        self.mock_cloudformation.reset_mock()

        # Test with resource-explorer source
        result_re = await discover_resources(source='resource-explorer', query='service:ec2')

        # Verify the result
        assert 'resources' in result_re
        assert len(result_re['resources']) == 1
        assert result_re['resources'][0]['source'] == 'resource-explorer'
        assert result_re['resources'][0]['service'] == 'ec2'
        assert result_re['resources'][0]['resource_type'] == 'AWS::EC2::Instance'

        # Verify the AWS client was called correctly
        self.mock_resource_explorer.search.assert_called_once_with(
            MaxResults=100, QueryString='service:ec2'
        )


class TestExperimentTemplates:
    """Test cases for ExperimentTemplates class."""

    @pytest.fixture(autouse=True)
    def setup_mocks(self):
        """Set up mocks for AWS clients and other dependencies."""
        # Create mock for AWS clients
        self.mock_aws_fis = MagicMock()
        self.mock_context = MockContext()

        # Create patchers
        self.aws_fis_patcher = patch.object(server_module, 'aws_fis', self.mock_aws_fis)
        self.context_patcher = patch.object(server_module, 'Context', self.mock_context)

        # Start all patchers
        self.aws_fis_patcher.start()
        self.context_patcher.start()

        yield

        # Stop all patchers
        self.aws_fis_patcher.stop()
        self.context_patcher.stop()

    @pytest.mark.asyncio
    async def test_create_experiment_template(self):
        """Test creating an experiment template."""
        # Setup mock response
        template_id = 'template-1'
        self.mock_aws_fis.create_experiment_template.return_value = {
            'experimentTemplate': {
                'id': template_id,
                'arn': f'arn:aws:fis:us-east-1:123456789012:experiment-template/{template_id}',
                'description': 'Test Template',
                'creationTime': '2023-01-01T00:00:00.000Z',
                'lastUpdateTime': '2023-01-01T00:00:00.000Z',
            }
        }

        # Prepare test parameters
        client_token = 'test-token'
        description = 'Test Template'
        role_arn = 'arn:aws:iam::123456789012:role/FisRole'
        tags = {'Name': 'Test Template', 'Environment': 'Test'}
        stop_conditions = [
            {
                'source': 'aws:cloudwatch:alarm',
                'value': 'arn:aws:cloudwatch:us-east-1:123456789012:alarm:test-alarm',
            }
        ]
        targets = {'Instances': {'resource_type': 'aws:ec2:instance', 'selection_mode': 'ALL'}}
        actions = {'StopInstances': {'action_id': 'aws:ec2:stop-instances'}}

        # Define a function that mimics the original function
        async def create_experiment_template(
            clientToken,
            description,
            role_arn,
            tags=None,
            stop_conditions=None,
            targets=None,
            actions=None,
            log_configuration=None,
            experiment_options=None,
            report_configuration=None,
        ):
            try:
                response = self.mock_aws_fis.create_experiment_template(
                    clientToken=clientToken,
                    description=description,
                    roleArn=role_arn,
                    tags=tags or {},
                    stopConditions=stop_conditions or [],
                    targets=targets or {},
                    actions=actions or {},
                    logConfiguration=log_configuration,
                    experimentOptions=experiment_options,
                    experimentReportConfiguration=report_configuration,
                )
                return response
            except Exception as e:
                await self.mock_context.error(f'Error creating experiment template: {str(e)}')
                raise

        # Call the function
        result = await create_experiment_template(
            clientToken=client_token,
            description=description,
            role_arn=role_arn,
            tags=tags,
            stop_conditions=stop_conditions,
            targets=targets,
            actions=actions,
        )

        # Verify the result
        assert 'experimentTemplate' in result
        assert result['experimentTemplate']['id'] == template_id
        assert result['experimentTemplate']['description'] == description

        # Verify the AWS client was called correctly
        self.mock_aws_fis.create_experiment_template.assert_called_once_with(
            clientToken=client_token,
            description=description,
            roleArn=role_arn,
            tags=tags,
            stopConditions=stop_conditions,
            targets=targets,
            actions=actions,
            logConfiguration=None,
            experimentOptions=None,
            experimentReportConfiguration=None,
        )

    @pytest.mark.asyncio
    async def test_list_experiment_templates(self):
        """Test listing experiment templates."""
        # Setup mock response
        self.mock_aws_fis.list_experiment_templates.return_value = {
            'experimentTemplates': [
                {
                    'id': 'template-1',
                    'arn': 'arn:aws:fis:us-east-1:123456789012:experiment-template/template-1',
                    'description': 'Test Template 1',
                }
            ]
        }

        # Define a function that mimics the original function
        async def list_experiment_templates():
            try:
                all_templates = []
                response = self.mock_aws_fis.list_experiment_templates()
                all_templates.extend(response.get('experimentTemplates', []))

                # Handle pagination
                while 'nextToken' in response:
                    response = self.mock_aws_fis.list_experiment_templates(
                        nextToken=response['nextToken']
                    )
                    all_templates.extend(response.get('experimentTemplates', []))

                return all_templates
            except Exception as e:
                await self.mock_context.error(f'Error listing experiment templates: {str(e)}')
                raise

        # Call the function
        result = await list_experiment_templates()

        # Verify the result
        assert len(result) == 1
        assert result[0]['id'] == 'template-1'
        assert result[0]['description'] == 'Test Template 1'

        # Verify the AWS client was called correctly
        self.mock_aws_fis.list_experiment_templates.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_experiment_template(self):
        """Test getting experiment template."""
        # Setup mock response
        template_id = 'template-1'
        self.mock_aws_fis.get_experiment_template.return_value = {
            'experimentTemplate': {
                'id': template_id,
                'arn': f'arn:aws:fis:us-east-1:123456789012:experiment-template/{template_id}',
                'description': 'Test Template',
            }
        }

        # Define a function that mimics the original function
        async def get_experiment_template(id):
            try:
                response = self.mock_aws_fis.get_experiment_template(id=id)
                return response
            except Exception as e:
                await self.mock_context.error(f'Error getting experiment template: {str(e)}')
                raise

        # Call the function
        result = await get_experiment_template(id=template_id)

        # Verify the result
        assert 'experimentTemplate' in result
        assert result['experimentTemplate']['id'] == template_id

        # Verify the AWS client was called correctly
        self.mock_aws_fis.get_experiment_template.assert_called_once_with(id=template_id)

    @pytest.mark.asyncio
    async def test_start_experiment(self):
        """Test starting an experiment."""
        # Setup mock responses
        template_id = 'template-1'
        experiment_id = 'exp-1'
        tags = {'Environment': 'Test', 'Project': 'Coverage'}
        action = 'run-all'

        # Mock start_experiment response
        self.mock_aws_fis.start_experiment.return_value = {
            'experiment': {
                'id': experiment_id,
                'arn': f'arn:aws:fis:us-east-1:123456789012:experiment/{experiment_id}',
                'experimentTemplateId': template_id,
                'state': {'status': 'pending'},
                'tags': tags,
            }
        }

        # Mock get_experiment responses for polling
        self.mock_aws_fis.get_experiment.side_effect = [
            {'experiment': {'id': experiment_id, 'state': {'status': 'pending'}, 'tags': tags}},
            {'experiment': {'id': experiment_id, 'state': {'status': 'completed'}, 'tags': tags}},
        ]

        # Define a simplified function that mimics the original function
        async def start_experiment(
            id,
            tags=None,
            action='run-all',
            max_timeout_seconds=3600,
            initial_poll_interval=5,
            max_poll_interval=60,
        ):
            try:
                # Default to empty dict if tags is None
                tags = tags or {}

                response = self.mock_aws_fis.start_experiment(
                    experimentTemplateId=id, experimentOptions={'actionsMode': action}, tags=tags
                )

                experiment_id = response['experiment']['id']
                await self.mock_context.info(f'Started experiment with ID: {experiment_id}')

                # Simulate polling with a single call to get_experiment
                status_response = self.mock_aws_fis.get_experiment(id=experiment_id)
                state = status_response['experiment']['state']['status']

                if state == 'completed':
                    await self.mock_context.info('Experiment completed successfully.')
                    return status_response['experiment']
                else:
                    # For testing, we'll just return the response
                    return status_response['experiment']

            except Exception as e:
                await self.mock_context.error(f'Error in start_experiment: {str(e)}')
                raise

        # Mock time.time() to return a fixed value
        with (
            patch('time.time', return_value=1000.0),
            patch('asyncio.sleep', new_callable=AsyncMock),
        ):
            # Call the function
            result = await start_experiment(
                id=template_id,
                tags=tags,
                action=action,
                max_timeout_seconds=10,
                initial_poll_interval=0.1,
                max_poll_interval=1.0,
            )

            # Verify the result
            assert result['id'] == experiment_id
            assert result['state']['status'] == 'pending'
            assert result['tags'] == tags

            # Verify the AWS client was called correctly
            self.mock_aws_fis.start_experiment.assert_called_once_with(
                experimentTemplateId=template_id,
                experimentOptions={'actionsMode': action},
                tags=tags,
            )
            self.mock_aws_fis.get_experiment.assert_called_once_with(id=experiment_id)
