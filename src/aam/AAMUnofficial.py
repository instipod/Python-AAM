#!python3
import json
import time

import requests
from requests.auth import HTTPBasicAuth


class AAMUnofficial(object):
    def __init__(self, base_url, web_username, web_password, verify=False):
        self.base_url = base_url
        self.web_username = web_username
        self.web_password = web_password
        self.verify = verify
        self.access_token = None
        self.expires_at = time.time()

    def get_access_token(self):
        auth = HTTPBasicAuth("client", "secret")
        headers = {'Accept': 'application/json'}
        data = {"username": self.web_username, "password": self.web_password, "grant_type": "password"}
        response = requests.post(f"{self.base_url}/oauth/token", data=data, auth=auth, headers=headers,
                                 verify=self.verify)
        if response.status_code == 200:
            json = response.json()
            self.access_token = json['access_token']
            self.expires_at = time.time() + int(json['expires_in'])
            return self.access_token
        else:
            return None

    def _execute_api_request(self, url, data=None, method="GET", headers={}):
        if self.access_token is None or time.time() - self.expires_at > 0:
            # access token is expired, should get a new one
            if self.get_access_token() is None:
                raise RuntimeError("Unable to retrieve an access token")

        headers['Authorization'] = f"Bearer {self.access_token}"
        headers['Accept'] = "application/json"
        if data is not None:
            headers["Content-Type"] = "application/json"
            data = json.dumps(data)
        response = requests.request(method, f"{self.base_url}/{url}", data=data, headers=headers,
                                    verify=self.verify)
        return response

    def get_volume_calibration(self, type, id):
        response = self._execute_api_request(f"webapi/v1/{type}/{id}/volumes", method="GET")
        if response.status_code == 200:
            return response.json()['data']['volumes']
        else:
            raise RuntimeError(response.content) #TODO

    def set_volume_calibration(self, type, id, category, volume):
        data = {"defaultGainOffset":volume}
        response = self._execute_api_request(f"webapi/v1/{type}/{id}/volumes/{category}", data=data, method="PUT")
        return response.status_code == 204

    def assign_device_to_zone(self, zone_id, device_id):
        device_id = int(device_id)
        data = {"sinkIds": [device_id]}
        response = self._execute_api_request(f"webapi/v1/zones/{zone_id}/sinksAssignment", data=data, method="POST")
        print(response.content)
        if response.status_code == 200:
            response_data = response.json()
            if 'successfulIds' in response_data.keys():
                return device_id in response_data['successfulIds']
        else:
            return False

    def start_test_tone(self, device_id, length=2):
        device_id = int(device_id)
        data = {"sinkId": device_id, "toneLength": length}
        response = self._execute_api_request(f"webapi/v1/testTone", data=data, method="POST")
        print(response.content)
        if response.status_code == 201:
            return True
        else:
            return False

    def get_devices(self):
        response = self._execute_api_request(f"webapi/v1/devices?size=2147483647", method="GET")
        if response.status_code == 200:
            data = response.json()
            return data
        else:
            return None
