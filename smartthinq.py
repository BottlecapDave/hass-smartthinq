import logging
import voluptuous as vol
from homeassistant.components import climate
import homeassistant.helpers.config_validation as cv
from homeassistant import const
import time

REQUIREMENTS = ['wideq']

LOGGER = logging.getLogger(__name__)

PLATFORM_SCHEMA = climate.PLATFORM_SCHEMA.extend({
    vol.Required('refresh_token'): cv.string,
})


def setup_platform(hass, config, add_devices, discovery_info=None):
    import wideq

    refresh_token = config.get('refresh_token')
    client = wideq.Client.from_token(refresh_token)

    add_devices(LGDevice(client, device) for device in client.devices)


class LGDevice(climate.ClimateDevice):
    def __init__(self, client, info):
        self._client = client
        self._info = info

        LOGGER.debug('device info: %s', self._info)
        self._id = self._info['deviceId']

        self._temp_cfg = None
        self._temp_cur = None

    @property
    def temperature_unit(self):
        return const.TEMP_CELSIUS

    @property
    def name(self):
        return self._info['alias']

    @property
    def available(self):
        return True

    @property
    def supported_features(self):
        return climate.SUPPORT_TARGET_TEMPERATURE

    @property
    def current_temperature(self):
        return self._temp_cur

    @property
    def target_temperature(self):
        return self._temp_cfg

    def set_temperature(self, temperature=None):
        self.client.session.set_device_controls(
            self._id,
            {'TempCfg': str(temperature)},
        )

    def update(self):
        import wideq
        with wideq.Monitor(self._client.session, self._id) as mon:
            while True:
                time.sleep(1)
                LOGGER.info('Polling...')
                res = mon.poll()
                if res:
                    self._temp_cfg = float(res['TempCfg'])
                    self._temp_cur = float(res['TempCur'])
                    break
