"""Give native Bluetooth receiver playback exclusive use of the USB DAC."""
import json
import threading
from pathlib import Path
from .receiver_hook import begin, end, state


class BluetoothHandover(threading.Thread):
    def __init__(self, stop):
        super().__init__(daemon=True, name='fm4-bluetooth')
        self.stop = stop

    def run(self):
        while not self.stop.wait(.5):
            try:
                connected = False
                for entry in Path('/proc').glob('[0-9]*/cmdline'):
                    try:
                        executable = entry.read_bytes().split(b'\0', 1)[0]
                        if executable.rsplit(b'/', 1)[-1] == b'bluealsa-aplay':
                            connected = True
                            break
                    except OSError:
                        pass
                source = json.loads(state.read_text()).get('source') if state.exists() else None
                if connected and source is None:
                    begin('bluetooth')
                elif not connected and source == 'bluetooth':
                    end('bluetooth')
            except Exception as exc:
                print('Bluetooth handover:', type(exc).__name__)
