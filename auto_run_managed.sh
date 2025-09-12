#!/bin/bash
# Managed Instagram Botting Script using Python Device Manager
# This script uses the robust Python device manager for connection handling

# Suppress deprecation warnings
export PYTHONWARNINGS="ignore::DeprecationWarning:adbutils._device:forward_list,ignore::DeprecationWarning:adbutils.*,ignore::DeprecationWarning:uiautomator2.*"

# Configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PYTHON_CMD="/usr/local/bin/python3.9"
DEVICE_MANAGER="$SCRIPT_DIR/device_manager.py"

# User accounts to cycle through (you can modify this)
user_order=( "tecan.tequila" "theholygrailboxing" "area.nl" "spectrum_amsterdam" )
MAX_RUNS_PER_DAY=3

# Activate virtual environment
source "$SCRIPT_DIR/.venv39/bin/activate"

# Function to get next available device
get_available_device() {
    python3 -c "
import sys
sys.path.append('$SCRIPT_DIR')
from device_manager import DeviceManager

devices = ['11131JEC202133', '8C5X1J8PY', '98SAY16PQ3', '993AY18H94']
manager = DeviceManager(devices)
device = manager.get_available_device()
if device:
    print(device)
else:
    print('NONE')
"
}

# Function to prepare device for session
prepare_device() {
    local device_id=$1
    python3 -c "
import sys
sys.path.append('$SCRIPT_DIR')
from device_manager import DeviceManager

devices = ['11131JEC202133', '8C5X1J8PY', '98SAY16PQ3', '993AY18H94']
manager = DeviceManager(devices)
success = manager.prepare_device_for_session('$device_id')
print('SUCCESS' if success else 'FAILED')
"
}

# Function to complete session
complete_session() {
    local device_id=$1
    local success=$2
    python3 -c "
import sys
sys.path.append('$SCRIPT_DIR')
from device_manager import DeviceManager

devices = ['11131JEC202133', '8C5X1J8PY', '98SAY16PQ3', '993AY18H94']
manager = DeviceManager(devices)
manager.complete_session('$device_id', $success)
"
}

# Function to get device status
get_device_status() {
    python3 -c "
import sys
sys.path.append('$SCRIPT_DIR')
from device_manager import DeviceManager

devices = ['11131JEC202133', '8C5X1J8PY', '98SAY16PQ3', '993AY18H94']
manager = DeviceManager(devices)
status = manager.get_device_status()
for device_id, info in status.items():
    print(f'{device_id}: {info[\"status\"]} | Sessions: {info[\"session_count\"]}/{info[\"max_sessions_per_day\"]} | Errors: {info[\"error_count\"]} | UIAutomator: {info[\"uiautomator_ready\"]}')
"
}

# Function to generate random pause duration
generate_random_pause_duration() {
    echo $(( (RANDOM % 10 + 15) * 60 ))  # 15-25 minutes
}

# Function to check if it's a new day and reset counts
check_new_day() {
    python3 -c "
import sys
sys.path.append('$SCRIPT_DIR')
from device_manager import DeviceManager

devices = ['11131JEC202133', '8C5X1J8PY', '98SAY16PQ3', '993AY18H94']
manager = DeviceManager(devices)
manager._reset_daily_counts_if_needed()
print('Daily counts reset if needed')
"
}

echo "Starting Managed Instagram Botting Script..."
echo "Using Python Device Manager for robust connection handling"

# Start the device manager in background
echo "Starting device manager..."
python3 "$DEVICE_MANAGER" &
DEVICE_MANAGER_PID=$!

# Wait a moment for device manager to initialize
sleep 10

# Function to cleanup on exit
cleanup() {
    echo "Shutting down device manager..."
    kill $DEVICE_MANAGER_PID 2>/dev/null
    exit 0
}

trap cleanup SIGINT SIGTERM

while true; do
    current_hour=$(date +"%H")
    
    # Check for new day and reset counts
    check_new_day
    
    if [ "$current_hour" -ge 7 ] && [ "$current_hour" -lt 22 ]; then
        echo "=== Active Hours: $current_hour:00 ==="
        
        # Get device status
        echo "Current device status:"
        get_device_status
        echo ""
        
        # Process each user account
        for username in "${user_order[@]}"; do
            echo "--- Processing account: $username ---"
            
            # Get available device
            device_id=$(get_available_device)
            
            if [ "$device_id" = "NONE" ]; then
                echo "No devices available. Waiting..."
                sleep 300  # Wait 5 minutes
                continue
            fi
            
            echo "Using device: $device_id"
            
            # Prepare device for session
            prepare_result=$(prepare_device "$device_id")
            
            if [ "$prepare_result" != "SUCCESS" ]; then
                echo "Failed to prepare device $device_id for $username"
                complete_session "$device_id" "false"
                continue
            fi
            
            echo "Device $device_id prepared successfully"
            
            # Run GramAddict
            echo "Starting GramAddict for $username on $device_id..."
            CONFIG_PATH="$SCRIPT_DIR/accounts/$username/config.yml"
            
            if [ -f "$CONFIG_PATH" ]; then
                timeout 7200 python "$SCRIPT_DIR/run.py" run --config "$CONFIG_PATH" --device "$device_id"
                EXIT_STATUS=$?
                
                if [ $EXIT_STATUS -eq 124 ]; then
                    echo "Session for $username timed out after 2 hours (normal)"
                    complete_session "$device_id" "true"
                elif [ $EXIT_STATUS -eq 0 ]; then
                    echo "Session for $username completed successfully"
                    complete_session "$device_id" "true"
                else
                    echo "Session for $username failed with exit status $EXIT_STATUS"
                    complete_session "$device_id" "false"
                fi
            else
                echo "Config file not found: $CONFIG_PATH"
                complete_session "$device_id" "false"
            fi
            
            # Pause between accounts
            pause_duration=$(generate_random_pause_duration)
            echo "Pausing for $((pause_duration / 60)) minutes before next account..."
            sleep "$pause_duration"
        done
        
    else
        echo "Outside active hours ($current_hour:00). Sleeping for 15 minutes."
        sleep 900
    fi
done




