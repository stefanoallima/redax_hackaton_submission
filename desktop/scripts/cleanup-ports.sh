#!/bin/bash
# Cleanup script for stopping all development servers
# Works on Linux/Mac

echo "Cleaning up development servers..."

# Ports used by the desktop app
ports=(5173 5174 5175 5176 5177 5178 5179)

for port in "${ports[@]}"; do
    echo "Checking port $port..."
    pid=$(lsof -ti:$port)

    if [ ! -z "$pid" ]; then
        echo "  Killing process $pid on port $port"
        kill -9 $pid 2>/dev/null
        sleep 0.5
    else
        echo "  Port $port is free"
    fi
done

echo ""
echo "Cleanup complete!"
echo "You can now run: npm run electron:dev"
