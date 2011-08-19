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


class TestPrivateImagesApi(keystone_utils.KeystoneTests):
    """
    Functional tests to verify private images functionality.
    """

    @skip_if_disabled
    def test_private_images_notadmin(self):
        """
        Test that we can upload an owned image; that we can manipulate
        its is_public setting; and that appropriate authorization
        checks are applied to other (non-admin) users.
        """
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

        # Shouldn't show up in the detail list, either
        headers = {'X-Auth-Token': keystone_utils.froggy_token}
        path = "http://%s:%d/v1/images/detail" % ("0.0.0.0", self.api_port)
        http = httplib2.Http()
        response, content = http.request(path, 'GET', headers=headers)
        self.assertEqual(response.status, 200)
        self.assertEqual(content, '{"images": []}')

        # Also check that froggy can't get the image metadata
        headers = {'X-Auth-Token': keystone_utils.froggy_token}
        path = "http://%s:%d/v1/images/1" % ("0.0.0.0", self.api_port)
        http = httplib2.Http()
        response, content = http.request(path, 'HEAD', headers=headers)
        self.assertEqual(response.status, 404)

        # Froggy shouldn't be able to get the image, either.
        headers = {'X-Auth-Token': keystone_utils.froggy_token}
        path = "http://%s:%d/v1/images/1" % ("0.0.0.0", self.api_port)
        http = httplib2.Http()
        response, content = http.request(path, 'GET', headers=headers)
        self.assertEqual(response.status, 404)

        # Froggy shouldn't be able to give themselves permission too
        # easily...
        headers = {'X-Auth-Token': keystone_utils.froggy_token,
                   'X-Image-Meta-Is-Public': 'True'}
        path = "http://%s:%d/v1/images/1" % ("0.0.0.0", self.api_port)
        http = httplib2.Http()
        response, content = http.request(path, 'PUT', headers=headers)
        self.assertEqual(response.status, 404)

        # Froggy shouldn't be able to give themselves ownership,
        # either
        headers = {'X-Auth-Token': keystone_utils.froggy_token,
                   'X-Image-Meta-Owner': 'froggy'}
        path = "http://%s:%d/v1/images/1" % ("0.0.0.0", self.api_port)
        http = httplib2.Http()
        response, content = http.request(path, 'PUT', headers=headers)
        self.assertEqual(response.status, 404)

        # Froggy can't delete it, either
        headers = {'X-Auth-Token': keystone_utils.froggy_token}
        path = "http://%s:%d/v1/images/1" % ("0.0.0.0", self.api_port)
        http = httplib2.Http()
        response, content = http.request(path, 'DELETE', headers=headers)
        self.assertEqual(response.status, 404)

        # Pattieblack should be able to see the image in lists
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

        # And in the detail list
        headers = {'X-Auth-Token': keystone_utils.pattieblack_token}
        path = "http://%s:%d/v1/images/detail" % ("0.0.0.0", self.api_port)
        http = httplib2.Http()
        response, content = http.request(path, 'GET', headers=headers)
        self.assertEqual(response.status, 200)
        data = json.loads(content)
        self.assertEqual(len(data['images']), 1)
        self.assertEqual(data['images'][0]['id'], 1)
        self.assertEqual(data['images'][0]['size'], FIVE_KB)
        self.assertEqual(data['images'][0]['name'], "Image1")
        self.assertEqual(data['images'][0]['is_public'], False)
        self.assertEqual(data['images'][0]['owner'], 'pattieblack')

        # Pattieblack should be able to get the image metadata
        headers = {'X-Auth-Token': keystone_utils.pattieblack_token}
        path = "http://%s:%d/v1/images/1" % ("0.0.0.0", self.api_port)
        http = httplib2.Http()
        response, content = http.request(path, 'HEAD', headers=headers)
        self.assertEqual(response.status, 200)
        self.assertEqual(response['x-image-meta-name'], "Image1")
        self.assertEqual(response['x-image-meta-is_public'], "False")
        self.assertEqual(response['x-image-meta-owner'], "pattieblack")

        # And of course the image itself
        headers = {'X-Auth-Token': keystone_utils.pattieblack_token}
        path = "http://%s:%d/v1/images/1" % ("0.0.0.0", self.api_port)
        http = httplib2.Http()
        response, content = http.request(path, 'GET', headers=headers)
        self.assertEqual(response.status, 200)
        self.assertEqual(content, "*" * FIVE_KB)
        self.assertEqual(response['x-image-meta-name'], "Image1")
        self.assertEqual(response['x-image-meta-is_public'], "False")
        self.assertEqual(response['x-image-meta-owner'], "pattieblack")

        # Pattieblack should be able to manipulate is_public
        headers = {'X-Auth-Token': keystone_utils.pattieblack_token,
                   'X-Image-Meta-Is-Public': 'True'}
        path = "http://%s:%d/v1/images/1" % ("0.0.0.0", self.api_port)
        http = httplib2.Http()
        response, content = http.request(path, 'PUT', headers=headers)
        self.assertEqual(response.status, 200)
        data = json.loads(content)
        self.assertEqual(data['image']['name'], "Image1")
        self.assertEqual(data['image']['is_public'], True)
        self.assertEqual(data['image']['owner'], 'pattieblack')

        # Pattieblack can't give the image away, however
        headers = {'X-Auth-Token': keystone_utils.pattieblack_token,
                   'X-Image-Meta-Owner': 'froggy'}
        path = "http://%s:%d/v1/images/1" % ("0.0.0.0", self.api_port)
        http = httplib2.Http()
        response, content = http.request(path, 'PUT', headers=headers)
        self.assertEqual(response.status, 200)
        data = json.loads(content)
        self.assertEqual(data['image']['name'], "Image1")
        self.assertEqual(data['image']['is_public'], True)
        self.assertEqual(data['image']['owner'], 'pattieblack')

        # Now that the image is public, froggy can see it
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

        # Should also be in details
        headers = {'X-Auth-Token': keystone_utils.froggy_token}
        path = "http://%s:%d/v1/images/detail" % ("0.0.0.0", self.api_port)
        http = httplib2.Http()
        response, content = http.request(path, 'GET', headers=headers)
        self.assertEqual(response.status, 200)
        data = json.loads(content)
        self.assertEqual(len(data['images']), 1)
        self.assertEqual(data['images'][0]['id'], 1)
        self.assertEqual(data['images'][0]['size'], FIVE_KB)
        self.assertEqual(data['images'][0]['name'], "Image1")
        self.assertEqual(data['images'][0]['is_public'], True)
        self.assertEqual(data['images'][0]['owner'], 'pattieblack')

        # Froggy can get the image metadata now...
        headers = {'X-Auth-Token': keystone_utils.froggy_token}
        path = "http://%s:%d/v1/images/1" % ("0.0.0.0", self.api_port)
        http = httplib2.Http()
        response, content = http.request(path, 'HEAD', headers=headers)
        self.assertEqual(response.status, 200)
        self.assertEqual(response['x-image-meta-name'], "Image1")
        self.assertEqual(response['x-image-meta-is_public'], "True")
        self.assertEqual(response['x-image-meta-owner'], "pattieblack")

        # And of course the image itself
        headers = {'X-Auth-Token': keystone_utils.froggy_token}
        path = "http://%s:%d/v1/images/1" % ("0.0.0.0", self.api_port)
        http = httplib2.Http()
        response, content = http.request(path, 'GET', headers=headers)
        self.assertEqual(response.status, 200)
        self.assertEqual(content, "*" * FIVE_KB)
        self.assertEqual(response['x-image-meta-name'], "Image1")
        self.assertEqual(response['x-image-meta-is_public'], "True")
        self.assertEqual(response['x-image-meta-owner'], "pattieblack")

        # Froggy still can't change is-public
        headers = {'X-Auth-Token': keystone_utils.froggy_token,
                   'X-Image-Meta-Is-Public': 'True'}
        path = "http://%s:%d/v1/images/1" % ("0.0.0.0", self.api_port)
        http = httplib2.Http()
        response, content = http.request(path, 'PUT', headers=headers)
        self.assertEqual(response.status, 404)

        # Or give themselves ownership
        headers = {'X-Auth-Token': keystone_utils.froggy_token,
                   'X-Image-Meta-Owner': 'froggy'}
        path = "http://%s:%d/v1/images/1" % ("0.0.0.0", self.api_port)
        http = httplib2.Http()
        response, content = http.request(path, 'PUT', headers=headers)
        self.assertEqual(response.status, 404)

        # Froggy can't delete it, either
        headers = {'X-Auth-Token': keystone_utils.froggy_token}
        path = "http://%s:%d/v1/images/1" % ("0.0.0.0", self.api_port)
        http = httplib2.Http()
        response, content = http.request(path, 'DELETE', headers=headers)
        self.assertEqual(response.status, 404)

        # But pattieblack can
        headers = {'X-Auth-Token': keystone_utils.pattieblack_token}
        path = "http://%s:%d/v1/images/1" % ("0.0.0.0", self.api_port)
        http = httplib2.Http()
        response, content = http.request(path, 'DELETE', headers=headers)
        self.assertEqual(response.status, 200)

        self.stop_servers()
