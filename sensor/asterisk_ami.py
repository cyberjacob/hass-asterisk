"""Asterisk Sensors"""
import logging

from homeassistant.const import STATE_UNKNOWN
from homeassistant.helpers.entity import Entity

DATA_ASTERISK = 'asterisk'
DATA_MONITOR = 'asterisk-monitor'
DATA_MAILBOX = 'asterisk-mailbox'

_LOGGER = logging.getLogger(__name__)

def setup_platform(hass, config, add_devices, discovery_info=None):
    """Sensor setup
       Loads configuration and creates devices for extensions and mailboxes
    """
    add_devices([AsteriskSensor(hass)])
    for extension in hass.data[DATA_MONITOR]:
        add_devices([AsteriskExtension(hass, extension)])
    for mailbox in hass.data[DATA_MAILBOX]:
        add_devices([AsteriskMailbox(hass, mailbox)])


class AsteriskSensor(Entity):
    """Asterisk Server connection status sensor."""

    def __init__(self, hass):
        """Initialize the sensor."""
        self._hass = hass
        self._state = STATE_UNKNOWN

    @property
    def name(self):
        """Return the name of the sensor."""
        return 'Asterisk Connection'

    @property
    def state(self):
        """Return the state of the sensor."""
        return self._state

    @property
    def should_poll(self):
        return True

    def update(self):
        """Check the connection status and update the internal state"""
        if self._hass.data[DATA_ASTERISK].connected():
            self._state = 'connected'
        else:
            self._state = 'disconnected'
            try:
                manager.connect(host, port)
                login_status = manager.login(username=username, secret=password).get_header("Response")
            except asterisk.manager.ManagerException as exception:
                _LOGGER.error("Error connecting to Asterisk: %s", exception.args[1])


class AsteriskExtension(Entity):
    """SIP extension connection status (registration) sensor."""
    def __init__(self, hass, extension):
        self._hass = hass
        self._extension = extension
        self._state = STATE_UNKNOWN

    @property
    def name(self):
        return "Asterisk Extension " + str(self._extension)

    @property
    def state(self):
        return self._state

    @property
    def should_poll(self):
        return True

    def update(self):
        """Check the registration status and update the state"""
        response = self._hass.data[DATA_ASTERISK].sipshowpeer(self._extension)
        if response.get_header("Response", "Error") == "Error":
            self._state = STATE_UNKNOWN
            return

        status_header = response.get_header("Status", "unknown")
        # OK state includes the connection latency, which needs removing
        if "OK" in status_header:
            self._state = "OK"

        self._state = status_header

class AsteriskMailbox(Entity):
    """Voicemail Mailbox Sensor."""
    def __init__(self, hass, mailbox):
        self._hass = hass
        self._mailbox = mailbox
        self._state = STATE_UNKNOWN

    @property
    def name(self):
        return "Asterisk Mailbox " + self._mailbox

    @property
    def state(self):
        return self._state

    @property
    def should_poll(self):
        return True

    def update(self):
        """Check the mailbox status and update the state"""
        cdict = {'Action': 'MailboxStatus'}
        cdict['Peer'] = self._mailbox
        response = self._hass.data[DATA_ASTERISK].send_action(cdict)
        _LOGGER.info(response)
        _LOGGER.info(response.headers)
        if response.get_header('Response') == 'Error':
            raise Exception(response.get_header('Message'))
        self._state = response.get_header('Waiting', STATE_UNKNOWN)
