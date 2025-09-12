#!/bin/bash
# R9DM907NF3J

# Directory and file for storing run counts, last run day, and error count
RUN_COUNT_DIR="/Users/milan/bots/Instamatic/bot/run_counts_5"
LAST_RUN_DAY_FILE="$RUN_COUNT_DIR/last_run_day"
ERROR_COUNT_FILE="$RUN_COUNT_DIR/error_count"
CURRENT_USER_INDEX_FILE="$RUN_COUNT_DIR/current_user_index"
DEVICE_ID="R9DM907NF3J"

# Suppress deprecation warnings from adbutils
export PYTHONWARNINGS="ignore::DeprecationWarning:adbutils._device:forward_list,ignore::DeprecationWarning:adbutils.*,ignore::DeprecationWarning:uiautomator2.*"

# Ensure run_counts directory and initial files exist very early
mkdir -p "$RUN_COUNT_DIR"
[ ! -f "$LAST_RUN_DAY_FILE" ] && echo "$(date +"%Y%m%d")" > "$LAST_RUN_DAY_FILE"
[ ! -f "$CURRENT_USER_INDEX_FILE" ] && echo "0" > "$CURRENT_USER_INDEX_FILE"
[ ! -f "$ERROR_COUNT_FILE" ] && echo "0" > "$ERROR_COUNT_FILE"

# --- Configuration ---
# User accounts to cycle through
user_order=( "alphabetstreet.marketing" )
MAX_RUNS_PER_DAY=3

# Use Python 3 for compatibility with GramAddict 3.2.12
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PYTHON_CMD="python3"
# Activate virtual environment
source "$SCRIPT_DIR/venv39/bin/activate"

# --- Helper Functions ---

# Reset counts for a new day
reset_counts() {
    echo "Resetting daily run counts for a new day."
    rm -f "$RUN_COUNT_DIR"/*_count
    echo "$1" > "$LAST_RUN_DAY_FILE"
    echo "0" > "$ERROR_COUNT_FILE"
    echo "0" > "$CURRENT_USER_INDEX_FILE"
}

# Handle errors and implement a cooling period
increment_error_count() {
    local error_count=0
    [ -f "$ERROR_COUNT_FILE" ] && error_count=$(cat "$ERROR_COUNT_FILE")
    ((error_count++))
    echo "$error_count" > "$ERROR_COUNT_FILE"
    
    echo "Current consecutive error count: $error_count"
    
    if [ "$error_count" -ge 10 ]; then
        echo "Too many consecutive errors ($error_count). Taking a break for 45 minutes."
        sleep 2700
        echo "0" > "$ERROR_COUNT_FILE"  # Reset error count after pause
    elif [ "$error_count" -ge 5 ]; then
        echo "Too many consecutive errors. Taking a break for 5 minutes."
        sleep 300
        echo "0" > "$ERROR_COUNT_FILE"  # Reset error count after pause
    fi
}

# Check consecutive errors to decide if we should skip
check_error_count() {
    local error_count=0
    [ -f "$ERROR_COUNT_FILE" ] && error_count=$(cat "$ERROR_COUNT_FILE")
    if [ "$error_count" -ge 5 ]; then
        echo "Max consecutive errors ($error_count) reached. Skipping current session."
        return 1
    fi
    return 0
}

# Check if a new day has started
check_new_day() {
    CURRENT_DAY=$(date +"%Y%m%d")
    if [ -f "$LAST_RUN_DAY_FILE" ] && [ "$CURRENT_DAY" != "$(cat "$LAST_RUN_DAY_FILE" 2>/dev/null)" ]; then
        reset_counts "$CURRENT_DAY"
    elif [ ! -f "$LAST_RUN_DAY_FILE" ]; then
        echo "$CURRENT_DAY" > "$LAST_RUN_DAY_FILE"
    fi
}

# Get the next user index
get_next_user_index() {
    local current_user_index=0
    [ -f "$CURRENT_USER_INDEX_FILE" ] && current_user_index=$(cat "$CURRENT_USER_INDEX_FILE")
    user_index=$((current_user_index % ${#user_order[@]}))
    echo "$((current_user_index + 1))" > "$CURRENT_USER_INDEX_FILE"
    echo "$user_index"
}

# Update and check run count
update_run_count() {
    local username=$1
    local run_count_file="$RUN_COUNT_DIR/${username}_count"
    local run_count=0
    [ ! -f "$run_count_file" ] && echo "0" > "$run_count_file" # Ensure file exists
    [ -f "$run_count_file" ] && run_count=$(cat "$run_count_file")
    if [ "$run_count" -lt "$MAX_RUNS_PER_DAY" ]; then
        echo "$((run_count + 1))" > "$run_count_file"
        echo "Run count for $username: $((run_count + 1))/$MAX_RUNS_PER_DAY"
        return 0
    fi
    echo "Max runs ($MAX_RUNS_PER_DAY) reached for $username today. Skipping."
    return 1
}

# Function to generate a random pause duration between 15 and 25 minutes
generate_random_pause_duration() {
    echo $(( (RANDOM % 11 + 15) * 60 ))  # Generates a random value between 15 and 25 minutes in seconds
}

# Robust UIAutomator2 restart to resolve connection issues
restart_uiautomator() {
    echo "Performing robust restart of UIAutomator2 for $DEVICE_ID..."

    # Step 1: Kill all UIAutomator and atx-agent processes
    echo "Killing all UIAutomator and atx-agent processes..."
    adb -s "$DEVICE_ID" shell "pkill -f uiautomator" >/dev/null 2>&1 || true
    adb -s "$DEVICE_ID" shell "pkill -f atx-agent" >/dev/null 2>&1 || true
    adb -s "$DEVICE_ID" shell "pkill -f com.github.uiautomator" >/dev/null 2>&1 || true
    # Force stop the packages
    adb -s "$DEVICE_ID" shell "am force-stop com.github.uiautomator" >/dev/null 2>&1 || true
    adb -s "$DEVICE_ID" shell "am force-stop com.github.uiautomator.test" >/dev/null 2>&1 || true
    sleep 3 # Wait for processes to die

    # Step 2: Clear app data and caches
    echo "Clearing UIAutomator app data and caches..."
    adb -s "$DEVICE_ID" shell "pm clear com.github.uiautomator" >/dev/null 2>&1 || true
    adb -s "$DEVICE_ID" shell "pm clear com.github.uiautomator.test" >/dev/null 2>&1 || true
    sleep 2 # Give it time to clear data

    # Step 3: Clear any stuck port forwards
    echo "Clearing potential stuck port forwards..."
    adb -s "$DEVICE_ID" forward --remove-all >/dev/null 2>&1 || true
    sleep 1

    # Step 4: Ensure device is properly connected before proceeding
    if ! check_device_connection; then
        echo "ERROR: Device $DEVICE_ID not properly connected after cleanup. Cannot initialize UIAutomator2."
        increment_error_count # Use existing error handling
        return 1
    fi
    echo "Device connection confirmed before UIAutomator2 init."

    # Step 5: Initialize UIAutomator2 with timeout and retries
    echo "Initializing UIAutomator2 with timeout (120s) and retries..."
    local init_attempts=0
    local max_init_attempts=3
    local init_success=false

    while [ "$init_attempts" -lt "$max_init_attempts" ] && [ "$init_success" = false ]; do
        echo "UIAutomator2 init attempt $((init_attempts + 1))/$max_init_attempts..."
        if timeout 120 "$PYTHON_CMD" -m uiautomator2 init --serial "$DEVICE_ID"; then
            init_success=true
            echo "UIAutomator2 initialization successful on attempt $((init_attempts + 1))."
        else
            echo "UIAutomator2 init attempt $((init_attempts + 1)) failed."
            ((init_attempts++))
            if [ "$init_attempts" -lt "$max_init_attempts" ]; then
                echo "Waiting 10 seconds before retry..."
                sleep 10
                # Re-check device connection before next attempt, as init failure can sometimes affect it
                if ! check_device_connection; then
                    echo "ERROR: Device $DEVICE_ID lost connection during init retries. Aborting."
                    increment_error_count
                    return 1
                fi
            fi
        fi
    done

    if [ "$init_success" = false ]; then
        echo "ERROR: UIAutomator2 initialization failed after $max_init_attempts attempts."
        increment_error_count
        return 1
    fi

    # Step 6: Start UIAutomator2 MainActivity explicitly (important after clearing data)
    echo "Explicitly starting UIAutomator2 MainActivity on device $DEVICE_ID..."
    adb -s "$DEVICE_ID" shell am start -n com.github.uiautomator/.MainActivity >/dev/null 2>&1
    sleep 5 # Give it a moment to start

    # Step 7: Comprehensive connection verification with retries
    echo "Verifying uiautomator2 connection with comprehensive checks..."
    local max_verify_retries=3 # Reduced from 5 to be quicker if issues persist
    local verify_retry_count=0
    local verification_success=1 # Assume failure (0 for success, 1 for failure)

    while [ "$verify_retry_count" -lt "$max_verify_retries" ]; do
        echo "Connection verification attempt $((verify_retry_count + 1))/$max_verify_retries..."
        # Test 1: Basic connection and d.info
        if "$PYTHON_CMD" -c "import uiautomator2; d = uiautomator2.connect('$DEVICE_ID'); print(d.info)" &>/dev/null; then
            echo "✓ Basic connection test (d.info) passed."
            # Test 2: Try to get device screen info (more comprehensive)
            if "$PYTHON_CMD" -c "import uiautomator2; d = uiautomator2.connect('$DEVICE_ID'); w, h = d.window_size(); print(f'Screen size: {w}x{h}')" &>/dev/null; then
                echo "✓ Screen info test (d.window_size) passed."
                echo "Uiautomator2 connection fully verified for $DEVICE_ID (attempt $((verify_retry_count + 1)))."
                verification_success=0 # Set to success
                break
            else
                echo "✗ Screen info test (d.window_size) failed."
            fi
        else
            echo "✗ Basic connection test (d.info) failed."
        fi

        ((verify_retry_count++))
        if [ "$verification_success" -ne 0 ] && [ "$verify_retry_count" -lt "$max_verify_retries" ]; then
            echo "Verification failed. Waiting 10 seconds before retry..."
            sleep 10
        fi
    done

    if [ "$verification_success" -eq 0 ]; then
        echo "UIAutomator2 restart and verification completed successfully!"
        # Reset error count on successful uiautomator restart
        echo "0" > "$ERROR_COUNT_FILE"
        return 0 # Overall success for this function
    else
        echo "ERROR: UIAutomator2 connection verification failed after $max_verify_retries attempts for $DEVICE_ID."
        echo "This indicates a persistent UIAutomator2 or device communication issue."
        increment_error_count
        return 1 # Overall failure for this function
    fi
}

# Robust function to check if device is connected and wait if not
check_device_connection() {
    echo "Checking device connection for $DEVICE_ID..."
    local wait_time=0
    local max_wait_time=60 # Wait for a maximum of 60 seconds
    local interval=5 # Check every 5 seconds

    if ! adb devices | grep -q "$DEVICE_ID\s*device"; then
        echo "Device $DEVICE_ID not found or not in 'device' state. Waiting for device to connect (max ${max_wait_time}s)..."
        while ! adb devices | grep -q "$DEVICE_ID\s*device"; do
            if [ $wait_time -ge $max_wait_time ]; then
                echo "Device $DEVICE_ID still not connected after ${max_wait_time} seconds. Will retry later."
                increment_error_count
                return 1
            fi
            sleep $interval
            wait_time=$((wait_time + interval))
            echo "Still waiting for $DEVICE_ID... (${wait_time}s)"
        done
        echo "Device $DEVICE_ID connected."
        sleep 5 # Give it a moment to fully settle after connecting
    else
        echo "Device $DEVICE_ID is already connected."
    fi
    return 0
}

# Function to close Instagram after session
close_instagram() {
    echo "Closing Instagram app..."
    adb -s "$DEVICE_ID" shell am force-stop com.instagram.android
    sleep 3
}

# Function to close ATX Agent app after session
close_atx_agent() {
    echo "Closing ATX Agent app..."
    adb -s "$DEVICE_ID" shell am force-stop com.github.uiautomator
    adb -s "$DEVICE_ID" shell am force-stop com.github.uiautomator.test
    adb -s "$DEVICE_ID" shell "pkill -f atx-agent" >/dev/null 2>&1 || true
    sleep 3
}

# --- Main Logic ---

echo "Starting Instagram Botting Script..."

while true; do
    check_new_day
    current_hour=$(date +"%H")
    
    # Ensure current_user_index, error_count, and last_run_day files exist.
    [ ! -f "$LAST_RUN_DAY_FILE" ] && echo "$(date +"%Y%m%d")" > "$LAST_RUN_DAY_FILE"
    [ ! -f "$CURRENT_USER_INDEX_FILE" ] && echo "0" > "$CURRENT_USER_INDEX_FILE"
    [ ! -f "$ERROR_COUNT_FILE" ] && echo "0" > "$ERROR_COUNT_FILE"

    if [ "$current_hour" -ge 7 ] && [ "$current_hour" -lt 22 ]; then # Active hours (7 AM to 9:59 PM)
        echo "Within active hours ($current_hour:00). Starting session loop."

        for ((i = 0; i < ${#user_order[@]}; i++)); do
            user_index=$(get_next_user_index)
            username=${user_order[$user_index]}
            
            echo "--- Preparing for account: $username ---"
            
            # Check for device connection first
            if ! check_device_connection; then
                echo "Device connection issue for $username. Skipping session for this account."
                continue
            fi
            
            # Restart UIAutomator2 at the beginning of each session for a clean state.
            if ! restart_uiautomator; then
                echo "Failed to robustly restart UIAutomator2. Skipping session for $username."
                # Error count is incremented within restart_uiautomator on failure
                continue # Skip this session if UIAutomator2 isn't ready
            fi

            if check_error_count && update_run_count "$username"; then
                echo "Running GramAddict for account: $username"
                CONFIG_PATH="/Users/milan/bots/Instamatic/bot/accounts/$username/config.yml"
                
                # Run GramAddict with timeout
                echo "Starting GramAddict with 2-hour timeout..."
                timeout 7200 "$PYTHON_CMD" "$SCRIPT_DIR/run.py" run --config "$CONFIG_PATH" --device "$DEVICE_ID"
                EXIT_STATUS=$?
                
                if [ $EXIT_STATUS -eq 124 ]; then
                    echo "Session for $username timed out after 2 hours. This is normal if the bot finished or got stuck for long."
                    echo "0" > "$ERROR_COUNT_FILE" # Reset error count on successful timeout
                    # Close ATX Agent app after successful timeout
                    close_atx_agent
                elif [ $EXIT_STATUS -ne 0 ]; then
                    echo "Session for $username failed with exit status $EXIT_STATUS. This indicates a crash or unhandled error within GramAddict."
                    increment_error_count
                else
                    echo "Session for $username completed successfully."
                    echo "0" > "$ERROR_COUNT_FILE" # Reset error count on success
                    # Close ATX Agent app after successful completion
                    close_atx_agent
                fi
                
                close_instagram
            else
                echo "Skipping account: $username due to previous errors or max runs reached."
            fi
            
            pause_duration=$(generate_random_pause_duration)
            echo "Pausing for $((pause_duration / 60)) minutes before next account or loop."
            sleep "$pause_duration"
        done
    else # Outside active hours (10 PM to 6:59 AM)
        echo "Outside active hours ($current_hour:00). Sleeping for 15 minutes."
        sleep 900 
    fi
done