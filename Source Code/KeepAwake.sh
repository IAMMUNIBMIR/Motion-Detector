#!/bin/bash

# URL of Render server
URL="https://motion-detector.onrender.com"

# Send a request to the server
curl -s $URL > /dev/null

# Log responses to a file in the current directory
logfile="$(pwd)/keepawake.log"

echo "Netlify response: $response_netlify" >> $logfile
echo "Render response: $response_render" >> $logfile
echo "KeepAwake.sh ran at $(date)" >> $logfile