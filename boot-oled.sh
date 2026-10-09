#!/bin/sh
# Best-effort early status. Native startup must proceed if it fails.
modprobe spi_bcm2835 2>/dev/null || true
modprobe i2c-dev 2>/dev/null || true
modprobe i2c-bcm2835 2>/dev/null || true
export PYTHONPATH=/home/tc/sable-pcp-stage/src:/home/tc/quadify-pcp:/home/tc/quadify-pcp/vendor
nohup /usr/local/bin/python3.11 -u -m sable.pcp.boot_splash > /tmp/fm4-boot-oled.log 2>&1 < /dev/null &
