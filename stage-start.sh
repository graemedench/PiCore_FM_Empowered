#!/bin/sh
# Prototype startup. Returns to the recovery panel if startup fails.
cd /home/tc/sable-pcp-stage || exit 1
modprobe i2c-dev
modprobe i2c-bcm2835
modprobe brcmfmac 2>/dev/null || true
# Receiver discovery is required alongside the native AirPlay daemon.
if [ -x /usr/local/etc/init.d/avahi ]; then
  # Native avahi start restarts DBus once, which detaches an already-running
  # Bluetooth daemon. Preserve the shared bus when starting discovery late.
  pidof dbus-daemon >/dev/null || /usr/local/etc/init.d/dbus start
  pidof avahi-daemon >/dev/null || /usr/local/sbin/avahi-daemon -D
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
