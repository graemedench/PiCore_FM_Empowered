#!/bin/sh
# Staged prototype. Does not change the saved boot command.
cd /home/tc/sable-pcp-stage || exit 1
modprobe i2c-dev
modprobe i2c-bcm2835
export PYTHONPATH=src:/home/tc/quadify-pcp:/home/tc/quadify-pcp/vendor
nohup /usr/local/bin/python3.11 -u -m sable.pcp.runner \
  > /tmp/sable-pcp-stage.log 2>&1 < /dev/null &
echo $! > /tmp/sable-pcp-stage.pid
