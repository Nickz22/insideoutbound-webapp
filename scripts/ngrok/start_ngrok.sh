#!/bin/bash

# Path to your ngrok configuration file
NGROK_CONFIG="./scripts/ngrok/ngrok.yml"

# Start all ngrok tunnels defined in the configuration file
ngrok start --all --config "$NGROK_CONFIG"