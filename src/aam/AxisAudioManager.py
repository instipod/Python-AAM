from AAMApi import AAMApi
from AAMUnofficial import AAMUnofficial


class AxisAudioManager():
    def __init__(self, base_url, api_username, api_password, web_username=None, web_password=None, verify=False):
        """
        Create an instance of the Axis Audio Manager library.  Uses the official Axis API and the unofficial API if a web
        username and password is specified.
        :arg base_url: base url to the Audio Manager Pro interface
        :arg api_username: API username set in the AAMP interface
        :arg api_password: API password set in the AAMP interface
        :arg web_username: Web interface username for the AAMP interface (optional)
        :arg web_password: Web interface password for the AAMP interface (optional)
        :arg verify: If the HTTPS certificate should be verified, default False
        """
        self.base_url = base_url
        self.api_username = api_username
        self.api_password = api_password
        self.web_username = web_username
        self.web_password = web_password
        self.verify = verify
        self.aam_api = AAMApi(self.base_url, self.api_username, self.api_password, verify=self.verify)
        self.uno_api = AAMUnofficial(self.base_url, self.web_username, self.web_password, verify=self.verify)
        self.devices = []

    def _get_aam_api_object(self):
        """
        Retrieve a configured instance of the AAM official API object.
        :return AAMApi object
        """
        return self.aam_api

    def _get_uno_api_object(self):
        """
        Retrieve a configured instance of the AAM unofficial API object.
        :return AAMUnofficial object
        :return:
        """
        if self.are_unofficial_features_enabled():
            return self.uno_api
        else:
            return None

    def are_unofficial_features_enabled(self):
        """
        Returns if unofficial API features are enabled
        :return: boolean
        """
        return self.web_username is not None and self.web_password is not None

    def refresh_devices(self):
        """
        Caches a local list of devices used in other API calls.
        """
        if self.are_unofficial_features_enabled():
            self.devices = self._get_uno_api_object().get_devices()
        else:
            self.devices = []

    def get_devices(self):
        """
        Retrieves a list of hardware devices linked to this Audio Manager.
        :return: list of dict
        """
        if self.are_unofficial_features_enabled() and len(self.devices) == 0:
            self.refresh_devices()
        return self.devices

    def get_audio_targets(self):
        """
        Retrieve a list of all configured audio targets in the Audio Manager.
        :return list of AAMAudioTarget, AAMPhysicalZone, AAMSite, or AAMDevice objects
        """
        raw_targets = self._get_aam_api_object().get_audio_targets()
        targets = []
        for raw_target in raw_targets:
            if 'type' not in raw_target.keys():
                continue

            target = AAMAudioTarget(self, raw_target['id'], raw_target['type'])
            target._load_json(raw_target)
            target = target.get_cast_object()
            targets.append(target)
        return targets

    def get_audio_zones(self):
        """
        Retrieve a list of all configured audio zones in the Audio Manager.
        :return list of AAMPhysicalZone objects
        """
        targets = self.get_audio_targets()
        zones = []
        for target in targets:
            if isinstance(target, AAMPhysicalZone):
                zones.append(target)
        return zones

    def get_audio_devices(self):
        """
        Retrieve a list of all audio devices in the Audio Manager.
        :return list of AAMDevice objects
        """
        targets = self.get_audio_targets()
        devices = []
        for target in targets:
            if isinstance(target, AAMDevice):
                devices.append(target)
        return devices


class AAMAudioTarget():
    def __init__(self, aam, id, type):
        self.aam = aam
        self.id = id
        self.type = type
        self.data = {"enabled": False, "id": id, "type": type, "status": "unknown", "valid": False}

    def __repr__(self):
        return f"AAMAudioTarget ({self.type}) {self.id}"

    def _load_json(self, json):
        """
        Load target information from the specified JSON string into the class.
        :param json: JSON target information
        """
        self.data = json
        self.id = self.data['id']
        self.type = self.data['type']

    def _load(self):
        """
        Load target information from the API into the class.
        """
        aam_api = self.aam._get_aam_api_object()
        target = aam_api.get_audio_target(self.id)
        self._load_json(target)

    def get_cast_object(self):
        """
        Retrieves a more specific object for the type of audio target.
        :return AAAMPhysicalZone, AAMSite, AAMDevice, or AAMAudioTarget
        """
        if self.type == "physicalZone":
            target = AAMPhysicalZone(self.aam, self.data['id'])
        elif self.type == "site":
            target = AAMSite(self.aam, self.data['id'])
        elif self.type == "device":
            target = AAMDevice(self.aam, self.data['id'])
        else:
            target = self
        target._load_json(self.data)
        return target

    def is_enabled(self):
        """
        Returns if the audio target is currently enabled (plays audio).
        :return boolean
        """
        return self.data['enabled']

    def get_id(self):
        """
        Returns the string identifier for the audio target.
        :return string
        """
        return self.id

    def get_type(self):
        """
        Returns the string type for the audio target.
        :return string
        """
        return self.type

    def get_status(self):
        """
        Returns the detailed status for the audio target.
        :return string
        """
        return self.data['status']

    def get_name(self):
        """
        Returns the nice name for the audio target.
        :return string
        """
        if 'niceName' not in self.data:
            return "Unknown"
        return self.data['niceName']

    def get_children(self):
        """
        Returns a list of the audio target's children zones or devices.
        :return list of AAMAudioTarget, AAMPhysicalZone, or AAMDevice objects
        """
        if 'children' not in self.data.keys():
            return []
        children = self.data['children']
        output = []
        for child in children:
            target = AAMAudioTarget(self.aam, child, "unknown")
            target._load()
            target = target.get_cast_object()
            output.append(target)
        return output

    def get_children_zones(self):
        """
        Returns a list of the audio target's children zones.
        :return list of AAMPhysicalZone objects
        """
        children = self.get_children()
        output = []
        for child in children:
            if isinstance(child, AAMPhysicalZone):
                output.append(child)
        return output

    def get_children_devices(self):
        """
        Returns a list of the audio target's children devices.
        :return list of AAMDevice objects
        """
        children = self.get_children()
        output = []
        for child in children:
            if isinstance(child, AAMDevice):
                output.append(child)
        return output

    def play_audio_file(self, audio_file, repeat=1, priority="HIGH"):
        """
        Play a one-shot audio file on the audio target.
        :param audio_file: audio file identifiers
        :param repeat: Number of times to repeat, default 1
        :param priority: Priority level to play at, default HIGH
        :return: audio session identifier
        """
        return self.play_audio_files([audio_file], repeat, priority)

    def play_audio_files(self, audio_files, repeat=1, priority="HIGH"):
        """
        Play one-shot audio session of one or more files on the audio target.
        :param audio_files: list of audio file identifiers
        :param repeat: Number of times to repeat, default 1
        :param priority: Priority level to play at, default HIGH
        :return: audio session identifier
        """
        response = self.aam._get_aam_api_object().play_audio_file([self.id], audio_files, repeat, priority)
        return response['id']


class AAMVolumeTarget(AAMAudioTarget):
    def get_volume_calibration_level(self, type="ALL"):
        """
        Retrieves the volume calibration level (base volume) for the target.
        :param type: the volume category to retrieve: MUSIC, ANNOUNCEMENT, PAGING, or ALL
        :return: dict of volume calibration data
        """
        if not self.aam.are_unofficial_features_enabled():
            raise NotImplementedError("Unofficial features are disabled")

        if self.type == "physicalZone":
            typeclass = "zones"
        else:
            typeclass = "sites"

        data = self.aam._get_uno_api_object().get_volume_calibration(typeclass, self.id.split("_")[1])

        if type == "ALL":
            return data
        else:
            return data[type]

    def set_volume_calibration_level(self, volume, type="ALL"):
        """
        Sets the volume calibration level (base volume) for the target.
        :param volume: integer volume level range -100000 to 100000
        :param type: the volume category to retrieve: MUSIC, ANNOUNCEMENT, PAGING, or ALL
        :return: boolean: True if successful
        """
        if not self.aam.are_unofficial_features_enabled():
            raise NotImplementedError("Unofficial features are disabled")

        if self.type == "physicalZone":
            typeclass = "zones"
        else:
            typeclass = "sites"

        if type == "MUSIC" or type == "ANNOUNCEMENT" or type == "PAGING":
            return self.aam._get_uno_api_object().set_volume_calibration(typeclass, self.id.split("_")[1],
                                                                            type, volume)
        elif type == "ALL":
            page_command = self.aam._get_uno_api_object().set_volume_calibration(typeclass, self.id.split("_")[1],
                                                                            "PAGING", volume)
            annc_command = self.aam._get_uno_api_object().set_volume_calibration(typeclass, self.id.split("_")[1],
                                                                                 "ANNOUNCEMENT", volume)
            music_command = self.aam._get_uno_api_object().set_volume_calibration(typeclass, self.id.split("_")[1],
                                                                                 "MUSIC", volume)
            return page_command and annc_command and music_command
        else:
            raise KeyError("Unsupported volume calibration type!")

class AAMPhysicalZone(AAMVolumeTarget):
    def __init__(self, aam, id):
        super().__init__(aam, id, "physicalZone")

    def __repr__(self):
        return f"AAMPhysicalZone {self.id}"

class AAMSite(AAMVolumeTarget):
    def __init__(self, aam, id):
        super().__init__(aam, id, "site")

    def __repr__(self):
        return f"AAMSite {self.id}"

class AAMDevice(AAMAudioTarget):
    def __init__(self, aam, id):
        super().__init__(aam, id, "device")
        self.device_info_loaded = False
        self.device_info = {}

    def __repr__(self):
        return f"AAMDevice {self.id}"

    def _load_device_info(self):
        """
        Loads hardware device information from the API into the class instance.
        """
        devices = self.aam.get_devices()
        this = None

        for device in devices:
            sinks = device['sinks']
            for sink in sinks:
                if sink['id'] == int(self.id.split("_")[1]):
                    this = device

        if this is not None:
            self.device_info_loaded = True
            self.device_info = device

    def get_device_information(self):
        """
        Returns a dict of the device's hardware information.
        :return: dict
        """
        if not self.device_info_loaded:
            self._load_device_info()
        return self.device_info

    def get_mac_address(self):
        """
        Returns the device's ethernet MAC address.
        :return: string
        """
        return self.get_device_information()['mac']

    def get_ip_address(self):
        """
        Returns the device's IP address.
        :return: string
        """
        return self.get_device_information()['ipAddress']

    def get_model_name(self):
        """
        Returns the device's hardware model name.
        :return: string
        """
        return self.get_device_information()['productName']

    def get_model_id(self):
        """
        Returns the device's hardware model number or identifier.
        :return: string
        """
        return self.get_device_information()['type']

    def get_firmware_version(self):
        """
        Returns the device's current firmware version.
        :return: string
        """
        return self.get_device_information()['fwVersion']

    def get_parent_zone(self):
        """
        Retrieves and returns the device's parent physical zone.
        :return: AAMPhysicalZone
        """
        zone = AAMPhysicalZone(self.aam, "zon_" + str(self.get_device_information()['sinks'][0]['zones'][0]['id']))
        zone._load()
        return zone

    def assign_to_zone(self, zone):
        """
        Reassign this device to another physical zone.
        :param zone: AAMPhysicalZone
        """
        if isinstance(zone, AAMPhysicalZone):
            zone_id = zone.get_id().split("_")[1]
        if isinstance(zone, int):
            zone_id = zone
        if isinstance(zone, str):
            zone_id = zone.split("_")[1]

        result = self.aam._get_uno_api_object().assign_device_to_zone(zone_id, self.get_id().split("_")[1])
        self._load_device_info()
        return result

    def ding(self, length=2):
        """
        Trigger the test tone to play on the device.
        :param length: Length of test tone, default 2 seconds
        """
        return self.aam._get_uno_api_object().start_test_tone(self.get_id().split("_")[1], length)