#!/bin/bash

# Path to your ngrok configuration file
NGROK_CONFIG="/Users/nzozaya@sitetracker.com/.ngrok2/ngrok.yml"

# Start all ngrok tunnels defined in the configuration file
ngrok start --all --config "$NGROK_CONFIG"