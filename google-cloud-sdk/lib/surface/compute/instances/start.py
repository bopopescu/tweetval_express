# Copyright 2014 Google Inc. All Rights Reserved.
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

"""Command for starting an instance."""

from googlecloudsdk.api_lib.compute import base_classes
from googlecloudsdk.api_lib.compute import csek_utils
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.compute.instances import flags
from googlecloudsdk.core import exceptions
from googlecloudsdk.core import resources


def _CommonArgs(parser):
  """Add parser arguments common to all tracks."""
  flags.INSTANCES_ARG.AddArgument(parser)
  csek_utils.AddCsekKeyArgs(parser, flags_about_creation=False)


class FailedToFetchInstancesError(exceptions.Error):
  pass


class Start(base.SilentCommand):
  """Start a stopped virtual machine instance.

    *{command}* is used to start a stopped Google Compute Engine virtual
  machine. Only a stopped virtual machine can be started.
  """

  @staticmethod
  def Args(parser):
    _CommonArgs(parser)

  def GetInstances(self, client, refs):
    """Fetches instance objects corresponding to the given references."""
    instance_get_requests = []
    for ref in refs:
      request_protobuf = client.messages.ComputeInstancesGetRequest(
          instance=ref.Name(),
          zone=ref.zone,
          project=ref.project)
      instance_get_requests.append((client.apitools_client.instances, 'Get',
                                    request_protobuf))

    instances = client.MakeRequests(instance_get_requests)
    return instances

  def Run(self, args):
    holder = base_classes.ComputeApiHolder(self.ReleaseTrack())
    client = holder.client

    csek_key_file = args.csek_key_file
    request_list = []
    instance_refs = flags.INSTANCES_ARG.ResolveAsResource(
        args, holder.resources,
        scope_lister=flags.GetInstanceZoneScopeLister(client))
    if csek_key_file:
      instances = self.GetInstances(client, instance_refs)
    else:
      instances = [None for _ in instance_refs]
    for instance_ref, instance in zip(instance_refs, instances):
      disks = []

      if csek_key_file:
        allow_rsa_encrypted = self.ReleaseTrack() in [base.ReleaseTrack.ALPHA,
                                                      base.ReleaseTrack.BETA]
        csek_keys = csek_utils.CsekKeyStore.FromArgs(args, allow_rsa_encrypted)
        for disk in instance.disks:
          disk_resource = resources.REGISTRY.Parse(disk.source)

          disk_key_or_none = csek_utils.MaybeLookupKeyMessage(
              csek_keys, disk_resource, client.apitools_client)

          if disk_key_or_none:
            disks.append(client.messages.CustomerEncryptionKeyProtectedDisk(
                diskEncryptionKey=disk_key_or_none,
                source=disk.source))

      if disks:
        encryption_req = client.messages.InstancesStartWithEncryptionKeyRequest(
            disks=disks)

        request = (
            client.apitools_client.instances,
            'StartWithEncryptionKey',
            client.messages.ComputeInstancesStartWithEncryptionKeyRequest(
                instance=instance_ref.Name(),
                instancesStartWithEncryptionKeyRequest=encryption_req,
                project=instance_ref.project,
                zone=instance_ref.zone))
      else:
        request = (
            client.apitools_client.instances,
            'Start',
            client.messages.ComputeInstancesStartRequest(
                instance=instance_ref.Name(),
                project=instance_ref.project,
                zone=instance_ref.zone))

      request_list.append(request)
    return client.MakeRequests(request_list)
