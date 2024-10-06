#!python3
import json
import time

import requests
from requests.auth import HTTPBasicAuth


class AAMUnofficial(object):
    def __init__(self, base_url, web_username, web_password, verify=False):
        """
        Creates an instance of the Axis Audio Manager Pro unofficial (web client) API driver.
        :param base_url: Base url to Axis Audio Manager Pro server
        :param web_username: Username to access the API
        :param web_password: Password to access the API
        :param verify: Enable verification of SSL certificates, default False
        """
        self.base_url = base_url
        self.web_username = web_username
        self.web_password = web_password
        self.verify = verify
        self.access_token = None
        self.expires_at = time.time()

    def get_access_token(self):
        """
        Retrieves and stores an OAuth access token for further access to the API.
        :return: access token string or None
        """
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
        """
        Execute an API request against the AAMP server.
        :param url: relative URL to the API endpoint
        :param data: json payload to include in the request, default None
        :param method: method to use for the request, default GET
        :param headers: dict of additional headers to include in the request
        :return: Response object
        """
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
        """
        Retrieves the volume calibration configuration for a zone or site.
        :param type: use zones for a zone, sites for a site
        :param id: id number of the zone or site
        :return: dict
        """
        response = self._execute_api_request(f"webapi/v1/{type}/{id}/volumes", method="GET")
        if response.status_code == 200:
            return response.json()['data']['volumes']
        else:
            raise RuntimeError(response.content) #TODO

    def set_volume_calibration(self, type, id, category, volume):
        """
        Sets the volume calibration level for a zone or site.
        :param type: use zones for a zone, sites for a site
        :param id: id number of the zone or site
        :param category: volume category either MUSIC, ANNOUNCEMENT, or PAGING
        :param volume: volume level, range -100000 to 100000
        :return: boolean, True if successful
        """
        data = {"defaultGainOffset":volume}
        response = self._execute_api_request(f"webapi/v1/{type}/{id}/volumes/{category}", data=data, method="PUT")
        return response.status_code == 204

    def assign_device_to_zone(self, zone_id, device_id):
        """
        Moves a device to the specific zone.
        :param zone_id: Zone identifier
        :param device_id: Device identifier
        :return: boolean, True if successful
        """
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
        """
        Plays the test tone on the specified device.
        :param device_id: Device identifier
        :param length: number of seconds to play test tone
        :return: boolean, True if successful
        """
        device_id = int(device_id)
        data = {"sinkId": device_id, "toneLength": length}
        response = self._execute_api_request(f"webapi/v1/testTone", data=data, method="POST")
        print(response.content)
        if response.status_code == 201:
            return True
        else:
            return False

    def get_devices(self):
        """
        Retrieves a list of all devices and their hardware information.
        :return: list
        """
        response = self._execute_api_request(f"webapi/v1/devices?size=2147483647", method="GET")
        if response.status_code == 200:
            data = response.json()
            return data
        else:
            return None
