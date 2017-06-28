#!/bin/bash
if [ "$DAYS_TO_KEEP_DATA" != "0" ]; then
    find /root/server/data -type f -not -iname "*.*" -mtime +${DAYS_TO_KEEP_DATA} -delete
fi