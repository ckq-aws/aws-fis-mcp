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

"""Tests for the models module."""

import unittest
from awslabs.aws_fis_mcp_server.models import (
    ExperimentState,
    ExperimentActionsMode,
    StopCondition,
    Target,
    Action,
    LogConfiguration,
    ExperimentTemplateRequest,
    StartExperimentRequest,
    ResourceExplorerViewRequest,
)


class TestModels(unittest.TestCase):
    """Test cases for the models module."""

    def test_experiment_state_enum(self):
        """Test the ExperimentState enum."""
        self.assertEqual(ExperimentState.PENDING, 'pending')
        self.assertEqual(ExperimentState.INITIATING, 'initiating')
        self.assertEqual(ExperimentState.RUNNING, 'running')
        self.assertEqual(ExperimentState.COMPLETED, 'completed')
        self.assertEqual(ExperimentState.STOPPED, 'stopped')
        self.assertEqual(ExperimentState.FAILED, 'failed')

    def test_experiment_actions_mode_enum(self):
        """Test the ExperimentActionsMode enum."""
        self.assertEqual(ExperimentActionsMode.RUN_ALL, 'run-all')

    def test_stop_condition_model(self):
        """Test the StopCondition model."""
        stop_condition = StopCondition(source='aws:cloudwatch:alarm', value='alarm-name')
        self.assertEqual(stop_condition.source, 'aws:cloudwatch:alarm')
        self.assertEqual(stop_condition.value, 'alarm-name')

    def test_target_model(self):
        """Test the Target model."""
        target = Target(
            resource_type='aws:ec2:instance',
            resource_arns=['arn:aws:ec2:us-east-1:123456789012:instance/i-12345678901234567'],
            selection_mode='ALL',
        )
        self.assertEqual(target.resource_type, 'aws:ec2:instance')
        self.assertEqual(
            target.resource_arns,
            ['arn:aws:ec2:us-east-1:123456789012:instance/i-12345678901234567'],
        )
        self.assertEqual(target.selection_mode, 'ALL')

    def test_action_model(self):
        """Test the Action model."""
        action = Action(
            action_id='aws:ec2:stop-instances',
            description='Stop EC2 instances',
            targets={'Instances': 'my-instances'},
        )
        self.assertEqual(action.action_id, 'aws:ec2:stop-instances')
        self.assertEqual(action.description, 'Stop EC2 instances')
        self.assertEqual(action.targets, {'Instances': 'my-instances'})

    def test_start_experiment_request_model(self):
        """Test the StartExperimentRequest model."""
        request = StartExperimentRequest(id='template-id')
        self.assertEqual(request.id, 'template-id')
        self.assertEqual(request.action, ExperimentActionsMode.RUN_ALL)
        self.assertEqual(request.max_timeout_seconds, 3600)
        self.assertEqual(request.initial_poll_interval, 5)
        self.assertEqual(request.max_poll_interval, 60)


if __name__ == '__main__':
    unittest.main()