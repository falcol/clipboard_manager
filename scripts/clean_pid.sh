#!/bin/bash

# Stop clipboard manager and clean up: Another instance is already running
pkill -f "python.*main.py" 2>/dev/null
sleep 1
rm ~/.clipboard_manager.lock 2>/dev/null
echo "Clipboard Manager stopped and cleaned up"
