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

"""AWS FIS MCP Server implementation."""

import argparse
import boto3
import os
import sys
import time
from awslabs.aws_fis_mcp_server import __version__
from awslabs.aws_fis_mcp_server.consts import (
    AWS_CONFIG_MAX_ATTEMPTS,
    AWS_CONFIG_RETRY_MODE,
    AWS_CONFIG_SIGNATURE_VERSION,
    DEFAULT_AWS_REGION,
    ENV_AWS_REGION,
    ENV_FASTMCP_LOG_LEVEL,
    SERVICE_CLOUDFORMATION,
    SERVICE_CONFIG,
    SERVICE_FIS,
    SERVICE_RESOURCE_EXPLORER,
    SERVICE_S3,
)
from botocore.config import Config
from dotenv import load_dotenv
from loguru import logger
from mcp.server.fastmcp import FastMCP
from pydantic import Field
from typing import Any, Dict, List, Optional

from awslabs.aws_fis_mcp_server.tools.fis_service_tools import (
    list_all_fis_experiments,
    get_experiment_details,
    list_experiment_templates,
    get_experiment_template,
    start_experiment
)


# Configure logging
logger.remove()
logger.add(sys.stderr, level=os.getenv(ENV_FASTMCP_LOG_LEVEL, 'WARNING'))

# Load environment variables
load_dotenv()

# Global variables for CLI arguments
allow_writes = False
aws_profile_override = None
aws_region_override = None

# Global variables for AWS clients
aws_fis: Any = None
s3: Any = None
resource_explorer: Any = None
cloudformation: Any = None
aws_config_client: Any = None

# Get region from environment or default to us-east-1
AWS_REGION = os.getenv(ENV_AWS_REGION, DEFAULT_AWS_REGION)


def initialize_aws_clients(region: str, profile: Optional[str] = None):
    """Initialize AWS clients with the specified region and profile."""
    global aws_fis, s3, resource_explorer, cloudformation, aws_config_client

    try:
        # Create AWS session with optional profile
        session = (
            boto3.Session(profile_name=profile, region_name=region)
            if profile
            else boto3.Session(region_name=region)
        )

        # Create AWS config
        aws_config = Config(
            region_name=region,
            signature_version=AWS_CONFIG_SIGNATURE_VERSION,
            retries={'max_attempts': AWS_CONFIG_MAX_ATTEMPTS, 'mode': AWS_CONFIG_RETRY_MODE},
            user_agent_extra=f'awslabs/mcp/aws-fis-mcp-server/{__version__}',
        )

        # Initialize AWS clients
        aws_fis = session.client(SERVICE_FIS, config=aws_config)
        s3 = session.client(SERVICE_S3, config=aws_config)
        resource_explorer = session.client(SERVICE_RESOURCE_EXPLORER, config=aws_config)
        cloudformation = session.client(SERVICE_CLOUDFORMATION, config=aws_config)
        aws_config_client = session.client(SERVICE_CONFIG, config=aws_config)

        logger.info(f'AWS clients initialized successfully in region {region}')

    except Exception as e:
        logger.error(f'Error initializing AWS clients: {str(e)}')
        raise


# Initialize MCP server
mcp = FastMCP(
    name='awslabs.aws-fis-mcp-server',
    instructions="""An MCP Server that enables LLMs to plan, create, and execute AWS Fault Injection Simulator (FIS) experiments.

    This server provides tools for:
    - Listing and managing FIS experiments
    - Creating and executing experiment templates
    - Exploring AWS resources for fault injection
    - Working with CloudFormation stacks

    Use these tools to help users design resilient systems through controlled fault injection.

    When invoking methods in the classes do not use the self argument as it is not meant to take arguments but rather refers to the class itself.
    """,
)


# FIS Service Tools
mcp.tool(name='list_fis_experiments')(list_all_fis_experiments)
mcp.tool(name='get_experiment')(get_experiment_details)
mcp.tool(name='list_experiment_templates')(list_experiment_templates)
mcp.tool(name='get_experiment_template')(get_experiment_template)
mcp.tool(name='start_experiment')(start_experiment)

# Resource Discovery Tools
mcp.tool(name='list_cfn_stacks')
mcp.tool(name='get_stack_resources')
mcp.tool(name='list_resource_explorer_views')
mcp.tool(name='search_resources')
mcp.tool(name='create_resource_explorer_view')
mcp.tool(name='discover_resource_relationships')

# FIS Experiment Management Tools
mcp.tool(name='create_experiment_template')
mcp.tool(name='update_experiment_template')



def main():
    """Run the AWS FIS MCP Server with CLI argument support.

    This function initializes and starts the AWS FIS MCP Server, which provides
    a set of tools for interacting with AWS Fault Injection Simulator (FIS) and
    related services through the Model Context Protocol (MCP).

    CLI Arguments:
        --aws-profile: AWS profile to use for credentials
        --aws-region: AWS region to use (overrides environment variables)
        --allow-writes: Allow destructive operations like starting experiments

    The server is configured with the FastMCP framework and exposes a collection
    of tools organized into classes for different functional areas:
    - AwsFisActions: For managing FIS experiments and templates
    - ExperimentTemplates: For creating and managing experiment templates
    - ResourceDiscovery: Consolidated class for discovering AWS resources from
      CloudFormation and Resource Explorer

    When executed, the server starts listening for MCP requests and responds
    with the results of the requested operations.
    """
    global allow_writes, aws_profile_override, aws_region_override

    # Parse command line arguments
    parser = argparse.ArgumentParser(description='AWS Fault Injection Simulator (FIS) MCP Server')
    parser.add_argument(
        '--aws-profile',
        help='AWS profile to use for credentials (default: uses default profile or environment)',
    )
    parser.add_argument(
        '--aws-region',
        help='AWS region to use (default: us-east-1 or AWS_REGION environment variable)',
    )
    parser.add_argument(
        '--allow-writes',
        action='store_true',
        help='Allow destructive operations such as starting FIS experiments and creating templates',
    )

    args = parser.parse_args()

    # Store arguments in global variables
    allow_writes = args.allow_writes
    aws_profile_override = args.aws_profile
    aws_region_override = args.aws_region

    # Determine AWS region (priority: CLI arg > env var > default)
    effective_region = aws_region_override or os.getenv(ENV_AWS_REGION, DEFAULT_AWS_REGION)

    logger.info(
        'AWS FIS MCP Server starting with AWS_PROFILE: %s, AWS_REGION: %s, ALLOW_WRITES: %s',
        aws_profile_override or 'default',
        effective_region,
        allow_writes,
    )

    # Initialize AWS clients with the determined configuration
    initialize_aws_clients(effective_region, aws_profile_override)

    # Start the MCP server
    logger.info('Starting AWS FIS MCP Server')
    mcp.run()


if __name__ == '__main__':
    main()
