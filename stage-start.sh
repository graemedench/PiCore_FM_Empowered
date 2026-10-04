#!/bin/sh
# Prototype startup. Returns to the recovery panel if startup fails.
cd /home/tc/sable-pcp-stage || exit 1
modprobe i2c-dev
modprobe i2c-bcm2835
# Receiver discovery is required alongside the native AirPlay daemon.
if [ -x /usr/local/etc/init.d/avahi ]; then
  /usr/local/etc/init.d/avahi start
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
