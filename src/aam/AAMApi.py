#!python3
import json
import requests
from requests.auth import HTTPDigestAuth


class AAMApi(object):
    def __init__(self, base_url, api_username, api_password, verify=False):
        self.base_url = base_url
        self.api_username = api_username
        self.api_password = api_password
        self.verify = verify

    def _get_api_authentication(self):
        return HTTPDigestAuth(self.api_username, self.api_password)

    def _execute_api_request(self, url, data=None, method="GET", headers={}):
        auth = self._get_api_authentication()
        headers['Accept'] = "application/json"
        if data is not None:
            headers["Content-Type"] = "application/json"
            data = json.dumps(data)
        response = requests.request(method, f"{self.base_url}/{url}", data=data, headers=headers,
                                    auth=auth, verify=self.verify)
        return response

    def get_audio_targets(self):
        response = self._execute_api_request("api/v1.1/targets", method="GET")
        if response.status_code == 200:
            return response.json()
        else:
            raise RuntimeError("Could not retrieve audio targets from AAMApi!")

    def get_audio_target(self, id):
        response = self._execute_api_request(f"api/v1.1/targets/{id}", method="GET")
        if response.status_code == 200:
            return response.json()
        elif response.status_code == 404:
            return None
        else:
            raise RuntimeError("Could not retrieve audio target from AAMApi!")

    def get_audio_zones(self):
        targets = self.get_audio_targets()
        zones = []
        for target in targets:
            if 'type' in target.keys() and target['type'] == 'physicalZone':
                zones.append(target)
        return zones

    def get_audio_files(self):
        response = self._execute_api_request("api/v1.1/audioFiles", method="GET")
        if response.status_code == 200:
            return response.json()
        else:
            raise RuntimeError("Could not retrieve audio files from AAMApi!")

    def play_audio_file(self, targets, files, repeat=1, priority="HIGH"):
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