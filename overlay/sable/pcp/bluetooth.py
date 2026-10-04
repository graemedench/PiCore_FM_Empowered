"""Give native Bluetooth receiver playback exclusive use of the USB DAC."""
import json
import subprocess
import threading
from .receiver_hook import begin, end, state


class BluetoothHandover(threading.Thread):
    def __init__(self, stop):
        super().__init__(daemon=True, name='fm4-bluetooth')
        self.stop = stop

    def run(self):
        while not self.stop.wait(.5):
            try:
                connected = subprocess.run(['pidof', 'bluealsa-aplay'],
                    stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL).returncode == 0
                source = json.loads(state.read_text()).get('source') if state.exists() else None
                if connected and source is None:
                    begin('bluetooth')
                elif not connected and source == 'bluetooth':
                    end('bluetooth')
            except Exception as exc:
                print('Bluetooth handover:', type(exc).__name__)
