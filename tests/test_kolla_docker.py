#!/usr/bin/python

# Copyright 2016 NEC Corporation
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

import copy
import imp
import os
import sys

try:
    from unittest import mock
except ImportError:
    import mock
from oslotest import base

this_dir = os.path.dirname(sys.modules[__name__].__file__)
sys.modules['ansible'] = mock.MagicMock()
sys.modules['ansible.module_utils'] = mock.MagicMock()
sys.modules['ansible.module_utils.basic'] = mock.MagicMock()
kolla_docker_file = os.path.join(this_dir, '..', 'ansible',
                                 'library', 'kolla_docker.py')
kd = imp.load_source('kolla_docker', kolla_docker_file)


class ModuleArgsTest(base.BaseTestCase):

    def setUp(self):
        super(ModuleArgsTest, self).setUp()

    def test_module_args(self):
        argument_spec = dict(
            common_options=dict(required=False, type='dict', default=dict()),
            action=dict(
                requried=True, type='str', choices=['compare_image',
                                                    'create_volume',
                                                    'get_container_env',
                                                    'get_container_state',
                                                    'pull_image',
                                                    'remove_container',
                                                    'remove_volume',
                                                    'restart_container',
                                                    'start_container',
                                                    'stop_container']),
            api_version=dict(required=False, type='str', default='auto'),
            auth_email=dict(required=False, type='str'),
            auth_password=dict(required=False, type='str'),
            auth_registry=dict(required=False, type='str'),
            auth_username=dict(required=False, type='str'),
            detach=dict(required=False, type='bool', default=True),
            labels=dict(required=False, type='dict', default=dict()),
            name=dict(required=False, type='str'),
            environment=dict(required=False, type='dict'),
            image=dict(required=False, type='str'),
            ipc_mode=dict(required=False, type='str', choices=['host']),
            cap_add=dict(required=False, type='list', default=list()),
            security_opt=dict(required=False, type='list', default=list()),
            pid_mode=dict(required=False, type='str', choices=['host']),
            privileged=dict(required=False, type='bool', default=False),
            remove_on_exit=dict(required=False, type='bool', default=True),
            restart_policy=dict(
                required=False, type='str', choices=['no',
                                                     'never',
                                                     'on-failure',
                                                     'always']),
            restart_retries=dict(required=False, type='int', default=10),
            tls_verify=dict(required=False, type='bool', default=False),
            tls_cert=dict(required=False, type='str'),
            tls_key=dict(required=False, type='str'),
            tls_cacert=dict(required=False, type='str'),
            volumes=dict(required=False, type='list'),
            volumes_from=dict(required=False, type='list')
            )
        required_together = [
            ['tls_cert', 'tls_key']
        ]

        kd.AnsibleModule = mock.MagicMock()
        kd.generate_module()
        kd.AnsibleModule.assert_called_with(
            argument_spec=argument_spec,
            required_together=required_together,
            bypass_checks=True
        )

FAKE_DATA = {

    'params': {
        'detach': True,
        'environment': {},
        'host_config': {
            'network_mode': 'host',
            'ipc_mode': '',
            'cap_add': None,
            'security_opt': None,
            'pid_mode': '',
            'privileged': False,
            'volumes_from': None,
            'restart_policy': 'always',
            'restart_retries': 10},
        'labels': {'build-date': '2016-06-02',
                   'kolla_version': '2.0.1',
                   'license': 'GPLv2',
                   'name': 'ubuntu Base Image',
                   'vendor': 'ubuntuOS'},
        'image': 'myregistrydomain.com:5000/ubuntu:16.04',
        'name': 'test_container',
        'volumes': None,
        'tty': True
    },

    'images': [
        {'Created': 1462317178,
         'Labels': {},
         'VirtualSize': 120759015,
         'ParentId': '',
         'RepoTags': ['myregistrydomain.com:5000/ubuntu:16.04'],
         'Id': 'sha256:c5f1cf30',
         'Size': 120759015},
        {'Created': 1461802380,
         'Labels': {},
         'VirtualSize': 403096303,
         'ParentId': '',
         'RepoTags': ['myregistrydomain.com:5000/centos:7.0'],
         'Id': 'sha256:336a6',
         'Size': 403096303}
    ],

    'containers': [
        {'Created': 1463578194,
         'Status': 'Up 23 hours',
         'HostConfig': {'NetworkMode': 'default'},
         'Id': 'e40d8e7187',
         'Image': 'myregistrydomain.com:5000/ubuntu:16.04',
         'ImageID': 'sha256:c5f1cf30',
         'Labels': {},
         'Names': '/my_container'}
    ],

}


@mock.patch("docker.Client")
def get_DockerWorker(mod_param, mock_dclient):
    module = mock.MagicMock()
    module.params = mod_param
    dw = kd.DockerWorker(module)
    return dw


class TestContainer(base.BaseTestCase):

    def setUp(self):
        super(TestContainer, self).setUp()
        self.fake_data = copy.deepcopy(FAKE_DATA)

    def test_create_container(self):
        self.dw = get_DockerWorker(self.fake_data['params'])
        self.dw.dc.create_host_config = mock.MagicMock(
            return_value=self.fake_data['params']['host_config'])
        self.dw.create_container()
        self.assertTrue(self.dw.changed)
        self.dw.dc.create_container.assert_called_once_with(
            **self.fake_data['params'])

    def test_start_container_without_pull(self):
        self.fake_data['params'].update({'auth_username': 'fake_user',
                                         'auth_password': 'fake_psw',
                                         'auth_registry': 'myrepo/myapp',
                                         'auth_email': 'fake_mail@foogle.com'})
        self.dw = get_DockerWorker(self.fake_data['params'])
        self.dw.dc.images = mock.MagicMock(
            return_value=self.fake_data['images'])
        self.dw.dc.containers = mock.MagicMock(params={'all': 'True'})
        new_container = copy.deepcopy(self.fake_data['containers'])
        new_container.append({'Names': '/test_container',
                              'Status': 'Up 2 seconds'})
        self.dw.dc.containers.side_effect = [self.fake_data['containers'],
                                             new_container]
        self.dw.check_container_differs = mock.MagicMock(return_value=False)
        self.dw.create_container = mock.MagicMock()
        self.dw.start_container()
        self.assertFalse(self.dw.changed)
        self.dw.create_container.assert_called_once_with()

    def test_start_container_with_duplicate_name(self):
        self.fake_data['params'].update({'name': 'my_container',
                                         'auth_username': 'fake_user',
                                         'auth_password': 'fake_psw',
                                         'auth_registry': 'myrepo/myapp',
                                         'auth_email': 'fake_mail@foogle.com'})
        self.dw = get_DockerWorker(self.fake_data['params'])
        self.dw.dc.images = mock.MagicMock(
            return_value=self.fake_data['images'])
        self.dw.dc.containers = mock.MagicMock(params={'all': 'True'})
        updated_cont_list = copy.deepcopy(self.fake_data['containers'])
        updated_cont_list.pop(0)
        self.dw.dc.containers.side_effect = [self.fake_data['containers'],
                                             self.fake_data['containers'],
                                             updated_cont_list,
                                             self.fake_data['containers']
                                             ]
        self.dw.check_container_differs = mock.MagicMock(return_value=True)
        self.dw.dc.remove_container = mock.MagicMock()
        self.dw.create_container = mock.MagicMock()
        self.dw.start_container()
        self.assertTrue(self.dw.changed)
        self.dw.dc.remove_container.assert_called_once_with(
            container=self.fake_data['params'].get('name'),
            force=True)
        self.dw.create_container.assert_called_once_with()

    def test_start_container(self):
        self.fake_data['params'].update({'name': 'my_container',
                                         'auth_username': 'fake_user',
                                         'auth_password': 'fake_psw',
                                         'auth_registry': 'myrepo/myapp',
                                         'auth_email': 'fake_mail@foogle.com'})
        self.dw = get_DockerWorker(self.fake_data['params'])
        self.dw.dc.images = mock.MagicMock(
            return_value=self.fake_data['images'])
        self.fake_data['containers'][0].update(
            {'Status': 'Exited 2 days ago'})
        self.dw.dc.containers = mock.MagicMock(
            return_value=self.fake_data['containers'])
        self.dw.check_container_differs = mock.MagicMock(return_value=False)
        self.dw.dc.start = mock.MagicMock()
        self.dw.start_container()
        self.assertTrue(self.dw.changed)
        self.dw.dc.start.assert_called_once_with(
            container=self.fake_data["params"].get('name'))
