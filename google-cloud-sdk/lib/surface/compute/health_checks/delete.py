# Copyright 2015 Google Inc. All Rights Reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#    http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
"""Command for deleting health checks."""
from googlecloudsdk.api_lib.compute import base_classes
from googlecloudsdk.api_lib.compute import utils
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.compute import flags as compute_flags
from googlecloudsdk.command_lib.compute.health_checks import flags


class Delete(base.DeleteCommand):
  """Delete health checks.

  *{command}* deletes one or more Google Compute Engine
  health checks.
  """

  HEALTH_CHECK_ARG = None

  @staticmethod
  def Args(parser):
    Delete.HEALTH_CHECK_ARG = flags.HealthCheckArgument('', plural=True)
    Delete.HEALTH_CHECK_ARG.AddArgument(parser, operation_type='delete')

  def Run(self, args):
    holder = base_classes.ComputeApiHolder(self.ReleaseTrack())
    client = holder.client

    health_check_refs = Delete.HEALTH_CHECK_ARG.ResolveAsResource(
        args,
        holder.resources,
        scope_lister=compute_flags.GetDefaultScopeLister(client))

    utils.PromptForDeletion(health_check_refs)

    requests = []
    for health_check_ref in health_check_refs:
      requests.append((client.apitools_client.healthChecks, 'Delete',
                       client.messages.ComputeHealthChecksDeleteRequest(
                           **health_check_ref.AsDict())))

    return client.MakeRequests(requests)
