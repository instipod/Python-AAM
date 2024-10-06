#!python3
import json
import requests
from requests.auth import HTTPDigestAuth


class AAMApi(object):
    def __init__(self, base_url, api_username, api_password, verify=False):
        """
        Creates an instance of the Axis Audio Manager Pro official API driver.
        :param base_url: Base url to Axis Audio Manager Pro server
        :param api_username: Username to access the API
        :param api_password: Password to access the API
        :param verify: Enable verification of SSL certificates, default False
        """
        self.base_url = base_url
        self.api_username = api_username
        self.api_password = api_password
        self.verify = verify

    def _get_api_authentication(self):
        """
        Retrieve an instance of HTTPDigestAuth used for further API request authentication.
        :return: HTTPDigestAuth
        """
        return HTTPDigestAuth(self.api_username, self.api_password)

    def _execute_api_request(self, url, data=None, method="GET", headers={}):
        """
        Execute an API request against the AAMP server.
        :param url: relative URL to the API endpoint
        :param data: json payload to include in the request, default None
        :param method: method to use for the request, default GET
        :param headers: dict of additional headers to include in the request
        :return: Response object
        """
        auth = self._get_api_authentication()
        headers['Accept'] = "application/json"
        if data is not None:
            headers["Content-Type"] = "application/json"
            data = json.dumps(data)
        response = requests.request(method, f"{self.base_url}/{url}", data=data, headers=headers,
                                    auth=auth, verify=self.verify)
        return response

    def get_audio_targets(self):
        """
        Retrieves a list of all audio targets on the server.
        :return: list
        """
        response = self._execute_api_request("api/v1.1/targets", method="GET")
        if response.status_code == 200:
            return response.json()
        else:
            raise RuntimeError("Could not retrieve audio targets from AAMApi!")

    def get_audio_target(self, id):
        """
        Retrieve a specific audio target by identifier.
        :param id: Audio target identifier
        :return: dict
        """
        response = self._execute_api_request(f"api/v1.1/targets/{id}", method="GET")
        if response.status_code == 200:
            return response.json()
        elif response.status_code == 404:
            return None
        else:
            raise RuntimeError("Could not retrieve audio target from AAMApi!")

    def get_audio_zones(self):
        """
        Retrieves a list of all audio physical zones on the server.
        :return: list
        """
        targets = self.get_audio_targets()
        zones = []
        for target in targets:
            if 'type' in target.keys() and target['type'] == 'physicalZone':
                zones.append(target)
        return zones

    def get_audio_files(self):
        """
        Retrieves a list of all audio files available on the server.
        :return: list
        """
        response = self._execute_api_request("api/v1.1/audioFiles", method="GET")
        if response.status_code == 200:
            return response.json()
        else:
            raise RuntimeError("Could not retrieve audio files from AAMApi!")

    def play_audio_file(self, targets, files, repeat=1, priority="HIGH"):
        """
        Creates a one-shot audio session and plays a file on a specific target.
        :param targets: list of targets
        :param files: list of files to play
        :param repeat: number of times to repeat, 1 is default
        :param priority: priority level to play at, HIGH is default
        :return: dict
        """
        data = {
          "fileIds": files,
          "prio": priority,
          "repeat": repeat,
          "targets": targets
        }
        if priority != "HIGH" and priority != "MEDIUM" and priority != "LOW":
            raise KeyError("Invalid priority value")
        if len(targets) < 1 or len(files) < 1:
            #no action
            return None
        response = self._execute_api_request("api/v1.1/audioSessions/oneshotPlayAudioFiles", data=data, method="POST")
        if response.status_code == 200:
            return response.json()
        else:
            print(response.content)
            raise RuntimeError("Could not create one shot audio session from AAMApi!")