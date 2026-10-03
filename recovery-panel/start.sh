#!/bin/sh
# Run after piCorePlayer startup; settings and dependencies survive in mydata.
APP=/home/tc/quadify-pcp
PIDFILE=/tmp/quadify-panel.pid
if [ -f "$PIDFILE" ]; then
    PID=$(cat "$PIDFILE")
    case "$PID" in
        ''|*[!0-9]*) ;;
        *) if [ -r "/proc/$PID/cmdline" ] && tr '\000' ' ' < "/proc/$PID/cmdline" | grep -q "$APP/panel.py"; then
               exit 0
           fi ;;
    esac
fi
nohup /usr/local/bin/python3.11 -u "$APP/panel.py" --server http://127.0.0.1:9000 >> /tmp/quadify-panel.log 2>&1 < /dev/null &
echo $! > "$PIDFILE"
