# vim: tabstop=4 shiftwidth=4 softtabstop=4

# Copyright 2011 OpenStack, LLC
# All Rights Reserved.
#
#    Licensed under the Apache License, Version 2.0 (the "License"); you may
#    not use this file except in compliance with the License. You may obtain
#    a copy of the License at
#
#         http://www.apache.org/licenses/LICENSE-2.0
#
#    Unless required by applicable law or agreed to in writing, software
#    distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
#    WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
#    License for the specific language governing permissions and limitations
#    under the License.

"""Functional test case that verifies private images functionality"""

import httplib2
import json

from glance.tests import functional
from glance.tests.functional import keystone_utils
from glance.tests.utils import execute, skip_if_disabled

class TestSharedImagesApi(keystone_utils.KeystoneTests):
    def test_share_image(self):
        self.cleanup()
        self.start_servers()

        # First, we need to push an image up
        image_data = "*" * FIVE_KB
        headers = {'Content-Type': 'application/octet-stream',
                   'X-Auth-Token': keystone_utils.pattieblack_token,
                   'X-Image-Meta-Name': 'Image1'}
        path = "http://%s:%d/v1/images" % ("0.0.0.0", self.api_port)
        http = httplib2.Http()
        response, content = http.request(path, 'POST', headers=headers,
                                         body=image_data)
        self.assertEqual(response.status, 201)
        data = json.loads(content)
        self.assertEqual(data['image']['id'], 1)
        self.assertEqual(data['image']['size'], FIVE_KB)
        self.assertEqual(data['image']['name'], "Image1")
        self.assertEqual(data['image']['is_public'], False)
        self.assertEqual(data['image']['owner'], 'pattieblack')

        # Next, make sure froggy can't list the image
        headers = {'X-Auth-Token': keystone_utils.froggy_token}
        path = "http://%s:%d/v1/images" % ("0.0.0.0", self.api_port)
        http = httplib2.Http()
        response, content = http.request(path, 'GET', headers=headers)
        self.assertEqual(response.status, 200)
        self.assertEqual(content, '{"images": []}')

        # Skipping the rest of the assertions from the private images tests.
        # The privacy (or lack thereof) is sufficiently demonstrated there.

        # Now add froggy as a shared image member
        headers = {'X-Auth-Token': keystone_utils.froggy_token}
        path = "http://%s:%d/v1/images/%s/members/%s" %
                ("0.0.0.0", self.api_port, data['image']['id'], 'froggy')
        http = httplib2.Http()
        response, content = http.request(path, 'PUT', headers=headers)
        self.assertEqual(response.status, 204)

        # Ensure pattieblack can still see the image
        headers = {'X-Auth-Token': keystone_utils.pattieblack_token}
        path = "http://%s:%d/v1/images" % ("0.0.0.0", self.api_port)
        http = httplib2.Http()
        response, content = http.request(path, 'GET', headers=headers)
        self.assertEqual(response.status, 200)
        data = json.loads(content)
        self.assertEqual(len(data['images']), 1)
        self.assertEqual(data['images'][0]['id'], 1)
        self.assertEqual(data['images'][0]['size'], FIVE_KB)
        self.assertEqual(data['images'][0]['name'], "Image1")

        # Ensure froggy can see the image now
        headers = {'X-Auth-Token': keystone_utils.froggy_token}
        path = "http://%s:%d/v1/images" % ("0.0.0.0", self.api_port)
        http = httplib2.Http()
        response, content = http.request(path, 'GET', headers=headers)
        self.assertEqual(response.status, 200)
        data = json.loads(content)
        self.assertEqual(len(data['images']), 1)
        self.assertEqual(data['images'][0]['id'], 1)
        self.assertEqual(data['images'][0]['size'], FIVE_KB)
        self.assertEqual(data['images'][0]['name'], "Image1")

        # ensure that no one else can see the image
        headers = {'X-Auth-Token': keystone_utils.bacon_token}
        path = "http://%s:%d/v1/images" % ("0.0.0.0", self.api_port)
        http = httplib2.Http()
        response, content = http.request(path, 'GET', headers=headers)
        self.assertEqual(response.status, 200)
        self.assertEqual(content, '{"images": []}')
