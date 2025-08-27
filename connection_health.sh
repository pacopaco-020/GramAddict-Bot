#!/bin/bash

# GramAddict Connection Health Monitor
# This script helps maintain stable ADB connections

echo "🔍 GramAddict Connection Health Monitor"
echo "======================================"

# Function to check ADB server status
check_adb_server() {
    echo "📱 Checking ADB server status..."
    if pgrep -f "adb.*server" > /dev/null; then
        echo "✅ ADB server is running"
        return 0
    else
        echo "❌ ADB server is not running"
        return 1
    fi
}

# Function to restart ADB server
restart_adb_server() {
    echo "🔄 Restarting ADB server..."
    adb kill-server
    sleep 2
    adb start-server
    sleep 3
}

# Function to check device connections
check_devices() {
    echo "📱 Checking device connections..."
    devices=$(adb devices | grep -v "List of devices attached" | grep -v "^$")
    
    if [ -z "$devices" ]; then
        echo "❌ No devices connected"
        return 1
    else
        echo "✅ Connected devices:"
        echo "$devices"
        return 0
    fi
}

# Function to test device responsiveness
test_device_responsiveness() {
    local device_id=$1
    echo "🧪 Testing responsiveness of $device_id..."
    
    if adb -s "$device_id" shell echo "test" 2>/dev/null | grep -q "test"; then
        echo "✅ Device $device_id is responsive"
        return 0
    else
        echo "❌ Device $device_id is not responsive"
        return 1
    fi
}

# Function to reconnect device
reconnect_device() {
    local device_id=$1
    echo "🔌 Attempting to reconnect $device_id..."
    
    adb disconnect "$device_id" 2>/dev/null
    sleep 2
    
    # For USB devices, try to reconnect
    adb connect "$device_id" 2>/dev/null
    sleep 3
    
    if test_device_responsiveness "$device_id"; then
        echo "✅ Successfully reconnected $device_id"
        return 0
    else
        echo "❌ Failed to reconnect $device_id"
        return 1
    fi
}

# Function to perform health check
perform_health_check() {
    echo "🏥 Performing comprehensive health check..."
    
    # Check ADB server
    if ! check_adb_server; then
        echo "🔄 Starting ADB server..."
        restart_adb_server
    fi
    
    # Check devices
    if ! check_devices; then
        echo "❌ No devices found. Please check USB connections or wireless ADB setup."
        return 1
    fi
    
    # Test each device
    local all_healthy=true
    while IFS= read -r line; do
        if [ -n "$line" ]; then
            device_id=$(echo "$line" | awk '{print $1}')
            if [ "$device_id" != "List" ]; then
                if ! test_device_responsiveness "$device_id"; then
                    echo "🔄 Attempting to reconnect $device_id..."
                    if reconnect_device "$device_id"; then
                        echo "✅ Device $device_id recovered"
                    else
                        echo "❌ Device $device_id failed to recover"
                        all_healthy=false
                    fi
                fi
            fi
        fi
    done < <(adb devices)
    
    if [ "$all_healthy" = true ]; then
        echo "✅ All devices are healthy and responsive"
        return 0
    else
        echo "⚠️  Some devices have issues"
        return 1
    fi
}

# Function to monitor continuously
monitor_continuously() {
    local interval=${1:-30}
    echo "🔄 Starting continuous monitoring (checking every ${interval}s)..."
    echo "Press Ctrl+C to stop"
    
    while true; do
        echo ""
        echo "🕐 $(date '+%Y-%m-%d %H:%M:%S') - Health Check"
        echo "----------------------------------------"
        
        if perform_health_check; then
            echo "✅ All systems operational"
        else
            echo "⚠️  Issues detected, attempting recovery..."
        fi
        
        echo "⏳ Waiting ${interval} seconds until next check..."
        sleep "$interval"
    done
}

# Main script logic
case "${1:-health}" in
    "health")
        perform_health_check
        ;;
    "restart")
        restart_adb_server
        check_devices
        ;;
    "monitor")
        monitor_continuously "${2:-30}"
        ;;
    "devices")
        check_devices
        ;;
    "help"|"-h"|"--help")
        echo "Usage: $0 [command] [options]"
        echo ""
        echo "Commands:"
        echo "  health     - Perform one-time health check (default)"
        echo "  restart    - Restart ADB server"
        echo "  monitor    - Start continuous monitoring"
        echo "  devices    - Show connected devices"
        echo "  help       - Show this help message"
        echo ""
        echo "Examples:"
        echo "  $0                    # Run health check"
        echo "  $0 restart            # Restart ADB server"
        echo "  $0 monitor            # Monitor every 30 seconds"
        echo "  $0 monitor 60         # Monitor every 60 seconds"
        ;;
    *)
        echo "Unknown command: $1"
        echo "Use '$0 help' for usage information"
        exit 1
        ;;
esac
