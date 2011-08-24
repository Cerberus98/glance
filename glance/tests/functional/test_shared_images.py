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

FIVE_KB = 5 * 1024
FIVE_GB = 5 * 1024 * 1024 * 1024


class TestSharedImagesApi(keystone_utils.KeystoneTests):
    def _push_image(self):
        # First, we need to push an image up
        image_data = "*" * FIVE_KB
        headers = {'Content-Type': 'application/octet-stream',
                   'X-Image-Meta-Name': 'Image1'}
        path = "http://%s:%d/v1/images" % ("0.0.0.0", self.api_port)
        response, content = self._request(path, 'POST',
                                          keystone_utils.pattieblack_token,
                                          headers=headers,
                                          body=image_data)
        self.assertEqual(response.status, 201)
        data = json.loads(content)
        self.assertEqual(data['image']['id'], 1)
        self.assertEqual(data['image']['size'], FIVE_KB)
        self.assertEqual(data['image']['name'], "Image1")
        self.assertEqual(data['image']['is_public'], False)
        self.assertEqual(data['image']['owner'], 'pattieblack')
        return content

    def _request(self, path, method, auth_token, headers=None, body=None):
        http = httplib2.Http()
        headers = headers or {}
        headers['X-Auth-Token'] = auth_token
        if body:
            return http.request(path, method, headers=headers,
                                body=body)
        else:
            return http.request(path, method, headers=headers)

    def test_share_image(self):
        self.cleanup()
        self.start_servers()
        # First, we need to push an image up
        data = json.loads(self._push_image())

        # Now add froggy as a shared image member
        path = "http://%s:%d/v1/images/%s/members/%s" % \
                ("0.0.0.0", self.api_port, data['image']['id'], 'froggy')
        
        response, _ = self._request(path, 'PUT',
                                    keystone_utils.pattieblack_token)
        self.assertEqual(response.status, 204)

        # Ensure pattieblack can still see the image
        path = "http://%s:%d/v1/images" % ("0.0.0.0", self.api_port)
        response, content = self._request(path, 'GET',
                                          keystone_utils.pattieblack_token)
        self.assertEqual(response.status, 200)
        data = json.loads(content)
        self.assertEqual(len(data['images']), 1)
        self.assertEqual(data['images'][0]['id'], 1)
        self.assertEqual(data['images'][0]['size'], FIVE_KB)
        self.assertEqual(data['images'][0]['name'], "Image1")

        # Ensure froggy can see the image now
        response, content = self._request(path, 'GET',
                                          keystone_utils.froggy_token)
        self.assertEqual(response.status, 200)
        data = json.loads(content)
        self.assertEqual(len(data['images']), 1)
        self.assertEqual(data['images'][0]['id'], 1)
        self.assertEqual(data['images'][0]['size'], FIVE_KB)
        self.assertEqual(data['images'][0]['name'], "Image1")

        # ensure that no one else can see the image
        path = "http://%s:%d/v1/images" % ("0.0.0.0", self.api_port)
        response, content = self._request(path, 'GET',
                                          keystone_utils.bacon_token)
        self.assertEqual(response.status, 200)
        self.assertEqual(content, '{"images": []}')

    def test_share_and_replace_members(self):
        self.cleanup()
        self.start_servers()
        # First, we need to push an image up
        data = json.loads(self._push_image())

        image = data['image']
        # Now add froggy as a shared image member
        path = "http://%s:%d/v1/images/%s/members/%s" % \
                ("0.0.0.0", self.api_port, data['image']['id'], 'froggy')
        
        response, _ = self._request(path, 'PUT',
                                    keystone_utils.pattieblack_token)
        self.assertEqual(response.status, 204)

        # Ensure pattieblack can still see the image
        path = "http://%s:%d/v1/images" % ("0.0.0.0", self.api_port)
        response, content = self._request(path, 'GET',
                                          keystone_utils.pattieblack_token)
        self.assertEqual(response.status, 200)
        data = json.loads(content)
        self.assertEqual(len(data['images']), 1)
        self.assertEqual(data['images'][0]['id'], 1)
        self.assertEqual(data['images'][0]['size'], FIVE_KB)
        self.assertEqual(data['images'][0]['name'], "Image1")

        # Ensure froggy can see the image now
        response, content = self._request(path, 'GET',
                                          keystone_utils.froggy_token)
        self.assertEqual(response.status, 200)
        data = json.loads(content)
        self.assertEqual(len(data['images']), 1)
        self.assertEqual(data['images'][0]['id'], 1)
        self.assertEqual(data['images'][0]['size'], FIVE_KB)
        self.assertEqual(data['images'][0]['name'], "Image1")

        # ensure that no one else can see the image
        path = "http://%s:%d/v1/images" % ("0.0.0.0", self.api_port)
        response, content = self._request(path, 'GET',
                                          keystone_utils.bacon_token)
        self.assertEqual(response.status, 200)
        self.assertEqual(content, '{"images": []}')

        # Replace froggy with bacon
        body = json.dumps({'memberships': [{'member_id': 'bacon', 
                                            'can_share': False}]})
        path = "http://%s:%d/v1/images/%s/members" % \
                ("0.0.0.0", self.api_port, image['id'])
        
        response, content = self._request(path, 'PUT',
                                          keystone_utils.pattieblack_token,
                                          body=body)
        self.assertEqual(response.status, 204)

        # Ensure bacon can see the image
        path = "http://%s:%d/v1/images" % ("0.0.0.0", self.api_port)
        response, content = self._request(path, 'GET',
                                          keystone_utils.bacon_token)
        self.assertEqual(response.status, 200)
        data = json.loads(content)
        self.assertEqual(len(data['images']), 1)
        self.assertEqual(data['images'][0]['id'], 1)
        self.assertEqual(data['images'][0]['size'], FIVE_KB)
        self.assertEqual(data['images'][0]['name'], "Image1")

        # ensure that no one else can see the image
        path = "http://%s:%d/v1/images" % ("0.0.0.0", self.api_port)
        response, content = self._request(path, 'GET',
                                          keystone_utils.froggy_token)
        self.assertEqual(response.status, 200)
        self.assertEqual(content, '{"images": []}')

    def test_unshare_image(self):
        self.cleanup()
        self.start_servers()
        # First, we need to push an image up
        data = json.loads(self._push_image())

        # Now add froggy as a shared image member
        path = "http://%s:%d/v1/images/%s/members/%s" % \
                ("0.0.0.0", self.api_port, data['image']['id'], 'froggy')
        
        response, _ = self._request(path, 'PUT',
                                    keystone_utils.pattieblack_token)
        self.assertEqual(response.status, 204)
        image = data['image']

        # Ensure pattieblack can still see the image
        path = "http://%s:%d/v1/images" % ("0.0.0.0", self.api_port)
        response, content = self._request(path, 'GET',
                                          keystone_utils.pattieblack_token)
        self.assertEqual(response.status, 200)
        data = json.loads(content)
        self.assertEqual(len(data['images']), 1)
        self.assertEqual(data['images'][0]['id'], 1)
        self.assertEqual(data['images'][0]['size'], FIVE_KB)
        self.assertEqual(data['images'][0]['name'], "Image1")

        # Ensure froggy can see the image now
        response, content = self._request(path, 'GET',
                                          keystone_utils.froggy_token)
        self.assertEqual(response.status, 200)
        data = json.loads(content)
        self.assertEqual(len(data['images']), 1)
        self.assertEqual(data['images'][0]['id'], 1)
        self.assertEqual(data['images'][0]['size'], FIVE_KB)
        self.assertEqual(data['images'][0]['name'], "Image1")

        # ensure that no one else can see the image
        path = "http://%s:%d/v1/images" % ("0.0.0.0", self.api_port)
        response, content = self._request(path, 'GET',
                                          keystone_utils.bacon_token)
        self.assertEqual(response.status, 200)
        self.assertEqual(content, '{"images": []}')

        # Now remove froggy as a shared image member
        path = "http://%s:%d/v1/images/%s/members/%s" % \
                ("0.0.0.0", self.api_port, image['id'], 'froggy')
        
        response, content = self._request(path, 'DELETE',
                                    keystone_utils.pattieblack_token)
        self.assertEqual(response.status, 204)

        # ensure that no one else can see the image
        path = "http://%s:%d/v1/images" % ("0.0.0.0", self.api_port)
        response, content = self._request(path, 'GET',
                                          keystone_utils.froggy_token)
        self.assertEqual(response.status, 200)
        self.assertEqual(content, '{"images": []}')

        # Ensure pattieblack can still see the image
        path = "http://%s:%d/v1/images" % ("0.0.0.0", self.api_port)
        response, content = self._request(path, 'GET',
                                          keystone_utils.pattieblack_token)
        self.assertEqual(response.status, 200)
        data = json.loads(content)
        self.assertEqual(len(data['images']), 1)
        self.assertEqual(data['images'][0]['id'], 1)
        self.assertEqual(data['images'][0]['size'], FIVE_KB)
        self.assertEqual(data['images'][0]['name'], "Image1")

    def test_share_and_can_share_image(self):
        self.cleanup()
        self.start_servers()
        # First, we need to push an image up
        data = json.loads(self._push_image())

        # Now add froggy as a shared image member
        body = json.dumps({ 'member': { 'can_share': True }})
        path = "http://%s:%d/v1/images/%s/members/%s" % \
                ("0.0.0.0", self.api_port, data['image']['id'], 'froggy')
        
        response, content = self._request(path, 'PUT',
                                    keystone_utils.pattieblack_token,
                                    body=body)
        self.assertEqual(response.status, 204)

        image = data['image']

        # Ensure froggy can see the image now
        path = "http://%s:%d/v1/images" % ("0.0.0.0", self.api_port)
        response, content = self._request(path, 'GET',
                                          keystone_utils.froggy_token)
        self.assertEqual(response.status, 200)
        data = json.loads(content)
        self.assertEqual(len(data['images']), 1)
        self.assertEqual(data['images'][0]['id'], 1)
        self.assertEqual(data['images'][0]['size'], FIVE_KB)
        self.assertEqual(data['images'][0]['name'], "Image1")

        # Froggy is going to share with bacon
        path = "http://%s:%d/v1/images/%s/members/%s" % \
                ("0.0.0.0", self.api_port, image['id'], 'bacon')
        
        response, _ = self._request(path, 'PUT',
                                    keystone_utils.froggy_token)
        self.assertEqual(response.status, 204)

        # Ensure bacon can see the image now
        path = "http://%s:%d/v1/images" % ("0.0.0.0", self.api_port)
        response, content = self._request(path, 'GET',
                                          keystone_utils.bacon_token)
        self.assertEqual(response.status, 200)
        data = json.loads(content)
        self.assertEqual(len(data['images']), 1)
        self.assertEqual(data['images'][0]['id'], 1)
        self.assertEqual(data['images'][0]['size'], FIVE_KB)
        self.assertEqual(data['images'][0]['name'], "Image1")

        # Ensure prosciutto cannot see the image
        response, content = self._request(path, 'GET',
                                          keystone_utils.prosciutto_token)
        self.assertEqual(response.status, 200)
        self.assertEqual(content, '{"images": []}')

        # Redundant, but prove prosciutto cannot share it
        path = "http://%s:%d/v1/images/%s/members/%s" % \
                ("0.0.0.0", self.api_port, image['id'], 'franknbeans')
        response, _ = self._request(path, 'PUT',
                                    keystone_utils.prosciutto_token)
        self.assertEqual(response.status, 404)

    def test_get_members(self):
        self.cleanup()
        self.start_servers()
        # First, we need to push an image up
        data = json.loads(self._push_image())

        # Now add froggy as a shared image member
        path = "http://%s:%d/v1/images/%s/members/%s" % \
                ("0.0.0.0", self.api_port, data['image']['id'], 'froggy')
        
        response, content = self._request(path, 'PUT',
                                    keystone_utils.pattieblack_token)
        self.assertEqual(response.status, 204)

        path = "http://%s:%d/v1/images/%s/members" % \
                ("0.0.0.0", self.api_port, data['image']['id'])
        
        response, content = self._request(path, 'GET',
                                    keystone_utils.pattieblack_token)
        self.assertEqual(response.status, 200)
        body = json.loads(content)
        self.assertEqual(body['members'][0]['can_share'], False)
        self.assertEqual(body['members'][0]['member_id'], 'froggy')
