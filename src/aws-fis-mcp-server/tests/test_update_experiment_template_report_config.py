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

"""Tests for the update_experiment_template method with report configuration."""

import unittest

# Import the class to test
from awslabs.aws_fis_mcp_server.server import ExperimentTemplates
from unittest.mock import MagicMock, patch


class TestUpdateExperimentTemplateReportConfig(unittest.TestCase):
    """Test cases for the update_experiment_template method with report configuration."""

    @patch('awslabs.aws_fis_mcp_server.server.aws_fis')
    @patch('awslabs.aws_fis_mcp_server.server.Context')
    async def test_update_experiment_template_with_report_config(self, mock_context, mock_aws_fis):
        """Test updating an experiment template with report configuration."""
        # Setup mock response
        template_id = 'template-1'
        mock_aws_fis.update_experiment_template.return_value = {
            'experimentTemplate': {
                'id': template_id,
                'arn': f'arn:aws:fis:us-east-1:123456789012:experiment-template/{template_id}',
                'description': 'Updated Test Template',
                'creationTime': '2023-01-01T00:00:00.000Z',
                'lastUpdateTime': '2023-01-02T00:00:00.000Z',
                'experimentReportConfiguration': {
                    's3Configuration': {
                        'bucketName': 'updated-test-bucket',
                        'prefix': 'reports/'
                    }
                }
            }
        }

        # Prepare test parameters
        report_configuration = {
            's3Configuration': {
                'bucketName': 'updated-test-bucket',
                'prefix': 'reports/'
            }
        }

        # Call the method with report configuration
        result = await ExperimentTemplates.update_experiment_template(
            id=template_id,
            description='Updated Test Template',
            experiment_report_configuration=report_configuration
        )

        # Verify the result
        self.assertIn('experimentTemplate', result)
        self.assertEqual(result['experimentTemplate']['id'], template_id)
        self.assertEqual(
            result['experimentTemplate']['experimentReportConfiguration']['s3Configuration']['bucketName'],
            'updated-test-bucket'
        )

        # Verify the AWS client was called correctly
        mock_aws_fis.update_experiment_template.assert_called_once_with(
            id=template_id,
            description='Updated Test Template',
            stopConditions=None,
            targets=None,
            actions=None,
            roleArn=None,
            logConfiguration=None,
            experimentOptions=None,
            experimentReportConfiguration=report_configuration
        )


if __name__ == '__main__':
    unittest.main()