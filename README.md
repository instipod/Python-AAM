# Python-AAM

Unofficial Python Library for interfacing with and controlling the Axis Audio Manager Pro server product.

This library supports sending commands to AAMP both via the [officially documented API](https://www.axis.com/vapix-library/subjects/t10100065/section/t10193272/display) and additional functions using the undocumented local web client API.

### Classes Included

**AAMApi** - Wrapper around the official AAMP API

**AAMUnofficial** - Wrapper around the web client API

**AxisAudioManager** - Object oriented wrapper and classes around AAMApi and AAMUnofficial combined into one interface


### Example Usage
    aam = AxisAudioManager("https://10.0.0.1", "api", "pass", "root", "pass", verify=False)
    
    # Play a ding-dong sound on all devices
    devices = aam.get_audio_devices()
    for device in devices:
        device.ding()

    # Play an audio clip on all zones
    zones = aam.get_audio_zones()
    for zone in zones:
        zone.play_audio_file(1)