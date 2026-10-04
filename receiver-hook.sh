#!/bin/sh
export PYTHONPATH=/home/tc/sable-pcp-stage/src
exec /usr/local/bin/python3.11 -m sable.pcp.receiver_hook "$@"
