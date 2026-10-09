#!/bin/sh
# Prototype startup. Returns to the recovery panel if startup fails.
cd /home/tc/sable-pcp-stage || exit 1
# Ask the early status display to release SPI/GPIO before normal rendering.
touch /tmp/fm4-boot-oled.stop
if [ -f /tmp/fm4-boot-oled.pid ]; then
  oled_pid=$(cat /tmp/fm4-boot-oled.pid)
  count=0
  while kill -0 "$oled_pid" 2>/dev/null && [ "$count" -lt 30 ]; do
    sleep .1
    count=$((count + 1))
  done
  if kill -0 "$oled_pid" 2>/dev/null; then
    echo 'Early OLED did not release; refusing a second display writer' >&2
    exit 1
  fi
fi
modprobe i2c-dev
modprobe i2c-bcm2835
modprobe brcmfmac 2>/dev/null || true
modprobe sr_mod 2>/dev/null || true
# Receiver discovery is required alongside the native AirPlay daemon.
if [ -x /usr/local/etc/init.d/avahi ]; then
  # Native avahi start restarts DBus once, which detaches an already-running
  # Bluetooth daemon. Preserve the shared bus when starting discovery late.
  pidof dbus-daemon >/dev/null || /usr/local/etc/init.d/dbus start
  pidof avahi-daemon >/dev/null || /usr/local/sbin/avahi-daemon -D
fi
# Native controller startup can omit the audio helper on a fresh image.
if grep -q '^BT_OUT_DEVICE="fm4_receiver"' /usr/local/etc/pcp/pcp.cfg && pidof bluetoothd >/dev/null; then
  pidof bluealsa >/dev/null || /usr/local/etc/init.d/bluealsa start
fi
export PYTHONPATH=src:/home/tc/quadify-pcp:/home/tc/quadify-pcp/vendor
nohup /usr/local/bin/python3.11 -u -m sable.pcp.runner \
  > /tmp/sable-pcp-stage.log 2>&1 < /dev/null &
prototype_pid=$!
echo "$prototype_pid" > /tmp/sable-pcp-stage.pid
sleep 2
if ! kill -0 "$prototype_pid" 2>/dev/null; then
  /bin/sh /home/tc/quadify-pcp/start.sh
fi
