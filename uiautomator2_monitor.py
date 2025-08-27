#!/usr/bin/env python3
"""
UIAutomator2 Connection Monitor and Auto-Recovery
This script automatically monitors ALL connected ADB devices for UIAutomator2 issues.
"""

import uiautomator2 as u2
import time
import subprocess
import threading
import signal
import sys
import logging
from datetime import datetime
import re
import os

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)

class GlobalPortManager:
    def __init__(self):
        self.registered_ports = set()
        self.lock = threading.Lock()
    
    def register_port(self, port):
        with self.lock:
            self.registered_ports.add(port)
    
    def unregister_port(self, port):
        with self.lock:
            self.registered_ports.discard(port)
    
    def get_all_ports(self):
        with self.lock:
            return self.registered_ports.copy()
    
    def clear_all_ports(self):
        with self.lock:
            self.registered_ports.clear()

class UIAutomator2Monitor:
    def __init__(self, device_id, global_port_manager, check_interval=30):  # Increased from 10 to 30 seconds
        self.device_id = device_id
        self.global_port_manager = global_port_manager
        self.check_interval = check_interval
        self.running = False
        self.connection_failures = 0
        self.last_intervention_time = 0
        self.min_intervention_interval = 300  # Increased from 60 to 300 seconds (5 minutes)
        self.active_session_detected = False
        self.session_check_interval = 60  # Increased from 30 to 60 seconds
        self.last_session_check = 0
        self.consecutive_health_failures = 0
        self.max_health_failures_before_intervention = 3  # Only intervene after 3 consecutive failures
        
    def is_bot_session_active(self):
        """Check if there's an active GramAddict bot session running"""
        try:
            # Method 1: Check for Python processes running GramAddict
            result = subprocess.run(
                ['pgrep', '-f', 'run.py.*run.*--config'],
                capture_output=True,
                text=True
            )
            if result.returncode == 0:
                pids = result.stdout.strip().split('\n')
                for pid in pids:
                    if pid:
                        # Check if this process has open connections to our device
                        try:
                            netstat = subprocess.run(
                                ['lsof', '-p', pid, '-i', 'tcp'],
                                capture_output=True,
                                text=True
                            )
                            if netstat.returncode == 0 and self.device_id in netstat.stdout:
                                return True
                        except:
                            pass
            
            # Method 2: Check for recent activity in bot directories
            bot_dirs = [
                '/Users/milan/Documents/bots/gramaddict/bot/accounts',
                '/Users/milan/bots/Instamatic/gramaddict/bot/accounts'
            ]
            
            for bot_dir in bot_dirs:
                if os.path.exists(bot_dir):
                    # Check if any config files were modified in the last 10 minutes
                    current_time = time.time()
                    for account_dir in os.listdir(bot_dir):
                        account_path = os.path.join(bot_dir, account_dir)
                        if os.path.isdir(account_path):
                            config_path = os.path.join(account_path, 'config.yml')
                            if os.path.exists(config_path):
                                file_mtime = os.path.getmtime(config_path)
                                if current_time - file_mtime < 600:  # 10 minutes
                                    return True
            
            # Method 3: Check for active ADB connections that might be bot-related
            try:
                adb_result = subprocess.run(
                    ['adb', 'devices'],
                    capture_output=True,
                    text=True
                )
                if adb_result.returncode == 0 and self.device_id in adb_result.stdout:
                    # If device is connected, assume it might be in use
                    return True
            except:
                pass
                
            return False
        except Exception as e:
            logging.debug(f"Error checking for active sessions: {e}")
            return False
    
    def should_intervene(self):
        """Determine if we should intervene based on timing and session status"""
        current_time = time.time()
        
        # Check for active sessions less frequently
        if current_time - self.last_session_check >= self.session_check_interval:
            self.active_session_detected = self.is_bot_session_active()
            self.last_session_check = current_time
            if self.active_session_detected:
                logging.info(f"Active bot session detected for {self.device_id}, monitoring quietly")
        
        # Don't intervene if there's an active session
        if self.active_session_detected:
            logging.debug(f"Active bot session detected for {self.device_id}, skipping intervention")
            return False
        
        # Don't intervene too frequently
        if current_time - self.last_intervention_time < self.min_intervention_interval:
            return False
        
        # Only intervene after multiple consecutive health failures
        if self.consecutive_health_failures < self.max_health_failures_before_intervention:
            return False
            
        return True
    
    def check_uiautomator2_health(self):
        """Check if UIAutomator2 connection is healthy"""
        try:
            # Try to connect to the device
            d = u2.connect(self.device_id)
            
            # Basic health check - get device info
            info = d.info
            if not info:
                return False, "Failed to get device info"
            
            # Check screen size
            try:
                size = d.window_size()
                if not size or size[0] <= 0 or size[1] <= 0:
                    return False, "Invalid screen size"
            except Exception as e:
                return False, f"Screen size check failed: {e}"
            
            # If we get here, connection is healthy
            if self.consecutive_health_failures > 0:
                logging.info(f"UIAutomator2 connection recovered for {self.device_id}")
                self.consecutive_health_failures = 0
            
            return True, "Connection healthy"
            
        except Exception as e:
            self.consecutive_health_failures += 1
            return False, str(e)
    
    def clear_port_conflicts(self):
        """Clear port forwarding conflicts for this device"""
        try:
            # Get current port forwards for this device
            result = subprocess.run(
                ['adb', '-s', self.device_id, 'forward', '--list'],
                capture_output=True,
                text=True
            )
            
            if result.returncode == 0:
                lines = result.stdout.strip().split('\n')
                ports = []
                
                for line in lines:
                    if line.strip():
                        # Parse port forward line: device tcp:local_port tcp:remote_port
                        parts = line.split()
                        if len(parts) >= 3 and 'tcp:' in parts[1]:
                            local_port = parts[1].replace('tcp:', '')
                            ports.append(int(local_port))
                
                if len(ports) > 1:
                    logging.warning(f"Multiple port forwards detected: {ports}. This may cause conflicts.")
                    
                    # Clear all port forwards for this device
                    subprocess.run(['adb', '-s', self.device_id, 'forward', '--remove-all'], 
                                 capture_output=True)
                    
                    # Wait a moment for cleanup
                    time.sleep(2)
                    
                    # Check if cleanup was successful
                    result = subprocess.run(
                        ['adb', '-s', self.device_id, 'forward', '--list'],
                        capture_output=True,
                        text=True
                    )
                    
                    if result.returncode == 0 and not result.stdout.strip():
                        logging.info("All port forwards successfully cleared")
                    else:
                        remaining_ports = []
                        for line in result.stdout.strip().split('\n'):
                            if line.strip():
                                parts = line.split()
                                if len(parts) >= 3 and 'tcp:' in parts[1]:
                                    local_port = parts[1].replace('tcp:', '')
                                    remaining_ports.append(int(local_port))
                        if remaining_ports:
                            logging.warning(f"Ports still remain after cleanup: {remaining_ports}")
                        
        except Exception as e:
            logging.error(f"Error clearing port conflicts: {e}")
    
    def aggressive_port_management(self):
        """More aggressive port management when multiple conflicts detected"""
        try:
            # Kill atx-agent processes on the device
            subprocess.run(
                ['adb', '-s', self.device_id, 'shell', 'pkill', '-f', 'atx-agent'],
                capture_output=True
            )
            
            # Clear all port forwards
            subprocess.run(['adb', '-s', self.device_id, 'forward', '--remove-all'], 
                         capture_output=True)
            
            # Wait for cleanup
            time.sleep(3)
            
            logging.info(f"Aggressive port cleanup completed for {self.device_id}")
            
        except Exception as e:
            logging.error(f"Error in aggressive port management: {e}")
    
    def restart_uiautomator2(self):
        """Restart UIAutomator2 on the device"""
        try:
            logging.info(f"Restarting UIAutomator2 for {self.device_id}")
            
            # Kill existing processes
            subprocess.run(
                ['adb', '-s', self.device_id, 'shell', 'pkill', '-f', 'uiautomator'],
                capture_output=True
            )
            
            # Force stop UIAutomator packages
            subprocess.run(
                ['adb', '-s', self.device_id, 'shell', 'am', 'force-stop', 'com.github.uiautomator'],
                capture_output=True
            )
            subprocess.run(
                ['adb', '-s', self.device_id, 'shell', 'am', 'force-stop', 'com.github.uiautomator.test'],
                capture_output=True
            )
            
            # Clear app data
            subprocess.run(
                ['adb', '-s', self.device_id, 'shell', 'pm', 'clear', 'com.github.uiautomator'],
                capture_output=True
            )
            subprocess.run(
                ['adb', '-s', self.device_id, 'shell', 'pm', 'clear', 'com.github.uiautomator.test'],
                capture_output=True
            )
            
            # Wait for cleanup
            time.sleep(5)
            
            # Start MainActivity
            subprocess.run(
                ['adb', '-s', self.device_id, 'shell', 'am', 'start', '-n', 'com.github.uiautomator/.MainActivity'],
                capture_output=True
            )
            
            # Wait for startup
            time.sleep(10)
            
            # Test connection
            is_healthy, message = self.check_uiautomator2_health()
            if is_healthy:
                logging.info(f"UIAutomator2 restart successful for {self.device_id}")
                self.connection_failures = 0
                self.consecutive_health_failures = 0
                return True
            else:
                logging.warning(f"UIAutomator2 restart failed for {self.device_id}: {message}")
                return False
                
        except Exception as e:
            logging.error(f"Error restarting UIAutomator2: {e}")
            return False
    
    def monitor_device(self):
        """Main monitoring loop for a single device"""
        logging.info(f"Starting UIAutomator2 monitoring for device {self.device_id}...")
        
        while self.running:
            try:
                # Check if we should intervene
                if not self.should_intervene():
                    time.sleep(self.check_interval)
                    continue
                
                # Check UIAutomator2 health
                is_healthy, message = self.check_uiautomator2_health()
                
                if not is_healthy:
                    logging.warning(f"UIAutomator2 health check failed: {message}")
                    logging.info(f"Consecutive failures: {self.consecutive_health_failures}/{self.max_health_failures_before_intervention}")
                    
                    # Only take action after multiple consecutive failures
                    if self.consecutive_health_failures >= self.max_health_failures_before_intervention:
                        logging.warning(f"Taking action after {self.consecutive_health_failures} consecutive failures")
                        
                        # Clear port conflicts first
                        self.clear_port_conflicts()
                        
                        # Try aggressive port management
                        self.aggressive_port_management()
                        
                        # Try to restart UIAutomator2
                        if self.restart_uiautomator2():
                            logging.info("UIAutomator2 connection restored")
                            self.last_intervention_time = time.time()
                        else:
                            logging.error("Failed to restore UIAutomator2 connection")
                    else:
                        logging.info(f"Connection issue detected but waiting for more failures before intervention")
                        
                else:
                    if self.consecutive_health_failures > 0:
                        logging.info(f"Status: {self.consecutive_health_failures} connection failures (recovered)")
                    else:
                        logging.info("Status: UIAutomator2 connection healthy")
                
                # Check for port conflicts (but don't clear them unless we're intervening)
                if self.consecutive_health_failures >= self.max_health_failures_before_intervention:
                    self.clear_port_conflicts()
                
                time.sleep(self.check_interval)
                
            except Exception as e:
                logging.error(f"Error in monitoring loop for {self.device_id}: {e}")
                time.sleep(self.check_interval)
    
    def start(self):
        """Start monitoring"""
        self.running = True
        self.monitor_thread = threading.Thread(target=self.monitor_device)
        self.monitor_thread.daemon = True
        self.monitor_thread.start()
        logging.info(f"Started monitoring thread for device {self.device_id}")
    
    def stop(self):
        """Stop monitoring"""
        self.running = False
        if hasattr(self, 'monitor_thread'):
            self.monitor_thread.join(timeout=5)

class MultiDeviceMonitor:
    def __init__(self):
        self.devices = {}
        self.monitors = {}
        self.global_port_manager = GlobalPortManager()
        self.running = False
        self.device_check_interval = 60  # Increased from 30 to 60 seconds
        
    def get_connected_devices(self):
        """Get list of currently connected ADB devices"""
        try:
            result = subprocess.run(['adb', 'devices'], capture_output=True, text=True)
            if result.returncode == 0:
                devices = []
                for line in result.stdout.strip().split('\n')[1:]:  # Skip header
                    if line.strip() and '\tdevice' in line:
                        device_id = line.split('\t')[0]
                        devices.append(device_id)
                return devices
        except Exception as e:
            logging.error(f"Error getting connected devices: {e}")
        return []
    
    def add_device(self, device_id):
        """Add a new device for monitoring"""
        if device_id not in self.monitors:
            logging.info(f"Adding new device for monitoring: {device_id}")
            monitor = UIAutomator2Monitor(device_id, self.global_port_manager)
            self.monitors[device_id] = monitor
            monitor.start()
            self.devices[device_id] = True
    
    def remove_device(self, device_id):
        """Remove a device from monitoring"""
        if device_id in self.monitors:
            logging.info(f"Removing device from monitoring: {device_id}")
            self.monitors[device_id].stop()
            del self.monitors[device_id]
            del self.devices[device_id]
    
    def update_device_list(self):
        """Update the list of monitored devices"""
        current_devices = set(self.get_connected_devices())
        monitored_devices = set(self.devices.keys())
        
        # Add new devices
        for device_id in current_devices - monitored_devices:
            self.add_device(device_id)
        
        # Remove disconnected devices
        for device_id in monitored_devices - current_devices:
            self.remove_device(device_id)
    
    def start(self):
        """Start multi-device monitoring"""
        logging.info("Starting Multi-Device UIAutomator2 Monitor...")
        logging.info("This will automatically detect and monitor all connected ADB devices")
        logging.info("Monitor is configured to be conservative and avoid interfering with active bot sessions")
        
        self.running = True
        
        # Initial device detection
        self.update_device_list()
        
        # Start monitoring loop
        while self.running:
            try:
                # Update device list periodically
                self.update_device_list()
                
                # Log current status
                if self.devices:
                    device_list = ', '.join(self.devices.keys())
                    logging.info(f"Currently monitoring {len(self.devices)} device(s): {device_list}")
                
                time.sleep(self.device_check_interval)
                
            except KeyboardInterrupt:
                logging.info("Received interrupt signal, shutting down...")
                break
            except Exception as e:
                logging.error(f"Error in main monitoring loop: {e}")
                time.sleep(self.device_check_interval)
        
        self.stop()
    
    def stop(self):
        """Stop all monitoring"""
        logging.info("Stopping all device monitors...")
        self.running = False
        
        for monitor in self.monitors.values():
            monitor.stop()
        
        logging.info("All monitors stopped")

def main():
    import argparse
    
    parser = argparse.ArgumentParser(description='UIAutomator2 Connection Monitor')
    parser.add_argument('--device', help='Monitor specific device ID')
    parser.add_argument('--auto-detect', action='store_true', help='Auto-detect all connected devices (default)')
    
    args = parser.parse_args()
    
    if args.device:
        # Single device mode
        logging.info(f"Starting single-device monitoring for {args.device}")
        global_port_manager = GlobalPortManager()
        monitor = UIAutomator2Monitor(args.device, global_port_manager)
        
        def signal_handler(signum, frame):
            logging.info(f"Received signal {signum}, shutting down gracefully...")
            monitor.stop()
            sys.exit(0)
        
        signal.signal(signal.SIGTERM, signal_handler)
        signal.signal(signal.SIGINT, signal_handler)
        
        try:
            monitor.start()
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            monitor.stop()
    else:
        # Multi-device auto-detect mode (default)
        logging.info("Starting auto-detect mode for all connected devices...")
        multi_monitor = MultiDeviceMonitor()
        
        def signal_handler(signum, frame):
            logging.info(f"Received signal {signum}, shutting down gracefully...")
            multi_monitor.stop()
            sys.exit(0)
        
        signal.signal(signal.SIGTERM, signal_handler)
        signal.signal(signal.SIGINT, signal_handler)
        
        try:
            multi_monitor.start()
        except KeyboardInterrupt:
            multi_monitor.stop()

if __name__ == "__main__":
    main()
