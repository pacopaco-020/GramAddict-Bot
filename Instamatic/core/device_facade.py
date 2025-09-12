import logging
import string
from datetime import datetime
from enum import Enum, auto
from inspect import stack
from os import getcwd, listdir
from random import randint, uniform
from re import search
from subprocess import PIPE, run
from time import sleep
from typing import Optional

import uiautomator2

from Instamatic.core.utils import random_sleep

logger = logging.getLogger(__name__)


def create_device(device_id, app_id):
    try:
        return DeviceFacade(device_id, app_id)
    except ImportError as e:
        logger.error(str(e))
        return None


def get_device_info(device):
    try:
        device_info = device.get_info()
        logger.debug(
            f"Phone Name: {device_info.get('productName', 'Unknown')}, SDK Version: {device_info.get('sdkInt', 'Unknown')}"
        )
        
        sdk_int = device_info.get('sdkInt')
        if sdk_int and str(sdk_int).isdigit() and int(sdk_int) < 19:
            logger.warning("Only Android 4.4+ (SDK 19+) devices are supported!")
        
        logger.debug(
            f"Screen dimension: {device_info.get('displayWidth', 'Unknown')}x{device_info.get('displayHeight', 'Unknown')}"
        )
        logger.debug(
            f"Screen resolution: {device_info.get('displaySizeDpX', 'Unknown')}x{device_info.get('displaySizeDpY', 'Unknown')}"
        )
        logger.debug(f"Device ID: {getattr(device.deviceV2, 'serial', 'Unknown')}")
    except Exception as e:
        logger.warning(f"Could not retrieve complete device info: {str(e)}")
        try:
            logger.debug(f"Device ID: {getattr(device.deviceV2, 'serial', 'Unknown')}")
        except:
            logger.debug("Device ID: Unknown")


class Timeout(Enum):
    ZERO = auto()
    TINY = auto()
    SHORT = auto()
    MEDIUM = auto()
    LONG = auto()


class SleepTime(Enum):
    ZERO = auto()
    TINY = auto()
    SHORT = auto()
    DEFAULT = auto()


class Location(Enum):
    CUSTOM = auto()
    WHOLE = auto()
    CENTER = auto()
    BOTTOM = auto()
    RIGHT = auto()
    LEFT = auto()
    BOTTOMRIGHT = auto()
    LEFTEDGE = auto()
    RIGHTEDGE = auto()
    TOPLEFT = auto()


class Direction(Enum):
    UP = auto()
    DOWN = auto()
    RIGHT = auto()
    LEFT = auto()


class Mode(Enum):
    TYPE = auto()
    PASTE = auto()


class DeviceFacade:
    def __init__(self, device_id, app_id):
        self.device_id = device_id
        self.app_id = app_id
        max_retries = 3
        for attempt in range(max_retries):
            try:
                if device_id is None or "." not in device_id:
                    self.deviceV2 = uiautomator2.connect(
                        "" if device_id is None else device_id
                    )
                else:
                    self.deviceV2 = uiautomator2.connect_adb_wifi(f"{device_id}")
                
                # Test the connection immediately to catch version parsing errors
                try:
                    _ = self.deviceV2.info
                    logger.debug(f"Device connection successful on attempt {attempt+1}")
                except Exception as info_error:
                    logger.warning(f"Device info check failed: {str(info_error)}")
                    if "InvalidVersion" in str(info_error) or "packaging.version" in str(info_error):
                        logger.info("Detected version parsing error, attempting UIAutomator2 reset...")
                        try:
                            # Force restart UIAutomator2 service
                            import subprocess
                            subprocess.run([
                                "adb", "-s", str(device_id), "shell", 
                                "am", "force-stop", "com.github.uiautomator"
                            ], capture_output=True)
                            subprocess.run([
                                "adb", "-s", str(device_id), "shell", 
                                "am", "force-stop", "com.github.uiautomator.test"
                            ], capture_output=True)
                            sleep(3)
                            # Reconnect after reset
                            if device_id is None or "." not in device_id:
                                self.deviceV2 = uiautomator2.connect(
                                    "" if device_id is None else device_id
                                )
                            else:
                                self.deviceV2 = uiautomator2.connect_adb_wifi(f"{device_id}")
                            _ = self.deviceV2.info  # Test again
                            logger.info("UIAutomator2 reset successful")
                        except Exception as reset_error:
                            logger.error(f"UIAutomator2 reset failed: {str(reset_error)}")
                            raise info_error
                    else:
                        raise info_error
                break
            except ImportError:
                raise ImportError("Please install uiautomator2: pip3 install uiautomator2")
            except Exception as e:
                logger.warning(f"Connection attempt {attempt+1}/{max_retries} failed: {str(e)}")
                if attempt < max_retries - 1:
                    sleep(2)
                else:
                    raise ConnectionError(f"Failed to connect to device after {max_retries} attempts: {str(e)}")

    def recover_from_gateway_error(self):
        """Attempt to recover from UIAutomator2 gateway errors"""
        logger.warning("Attempting to recover from UIAutomator2 gateway error...")
        try:
            # Step 1: Try to restart UIAutomator2 service on device
            import subprocess
            subprocess.run([
                "adb", "-s", str(self.device_id), "shell", 
                "am", "force-stop", "com.github.uiautomator"
            ], capture_output=True, timeout=10)
            subprocess.run([
                "adb", "-s", str(self.device_id), "shell", 
                "am", "force-stop", "com.github.uiautomator.test"
            ], capture_output=True, timeout=10)
            sleep(2)
            
            # Step 2: Clear UIAutomator2 cache
            subprocess.run([
                "adb", "-s", str(self.device_id), "shell", 
                "rm", "-rf", "/data/local/tmp/minicap*"
            ], capture_output=True, timeout=10)
            subprocess.run([
                "adb", "-s", str(self.device_id), "shell", 
                "rm", "-rf", "/data/local/tmp/minitouch*"
            ], capture_output=True, timeout=10)
            sleep(1)
            
            # Step 3: Restart UIAutomator2 MainActivity
            subprocess.run([
                "adb", "-s", str(self.device_id), "shell", 
                "am", "start", "-n", "com.github.uiautomator/.MainActivity"
            ], capture_output=True, timeout=10)
            sleep(3)
            
            # Step 4: Test connection with retry
            for attempt in range(3):
                try:
                    info = self.deviceV2.info
                    if info:
                        logger.info("UIAutomator2 gateway recovery successful")
                        return True
                except Exception as test_error:
                    logger.warning(f"Recovery test attempt {attempt + 1} failed: {test_error}")
                    if attempt < 2:
                        sleep(3)
            
            logger.warning("UIAutomator2 gateway recovery failed after all test attempts")
            return False
            
        except Exception as recovery_error:
            logger.error(f"UIAutomator2 gateway recovery failed: {str(recovery_error)}")
            return False

    def _get_current_app(self):
        max_retries = 3
        for attempt in range(max_retries):
            try:
                result = self.deviceV2.app_current()
                if result and "package" in result:
                    return result["package"]
                else:
                    logger.debug(f"app_current() returned unexpected result: {result}")
                    if attempt < max_retries - 1:
                        sleep(1)
                        continue
                    return "unknown"
            except uiautomator2.JSONRPCError as e:
                if attempt < max_retries - 1:
                    logger.debug(f"_get_current_app attempt {attempt+1} failed: {str(e)}")
                    sleep(1)
                    continue
                else:
                    logger.warning(f"_get_current_app failed after {max_retries} attempts: {str(e)}")
                    raise DeviceFacade.JsonRpcError(e)
            except Exception as e:
                if attempt < max_retries - 1:
                    logger.debug(f"_get_current_app attempt {attempt+1} failed with unexpected error: {str(e)}")
                    sleep(1)
                    continue
                else:
                    logger.warning(f"_get_current_app failed with unexpected error: {str(e)}")
                    return "unknown"

    def _ig_is_opened(self) -> bool:
        try:
            current_app = self._get_current_app()
            return current_app == self.app_id
        except Exception as e:
            logger.debug(f"_ig_is_opened check failed: {str(e)}")
            return False  # Assume not opened if we can't check

    def check_if_ig_is_opened(func):
        def wrapper(self, **kwargs):
            avoid_lst = ["choose_cloned_app", "check_if_crash_popup_is_there"]
            caller = stack()[1].function
            
            # Check if Instagram is opened with multiple attempts
            ig_opened = False
            for attempt in range(3):
                try:
                    ig_opened = self._ig_is_opened()
                    if ig_opened:
                        break
                    elif attempt < 2:  # Not the last attempt
                        logger.debug(f"Instagram check attempt {attempt+1} failed, retrying...")
                        sleep(1)
                except Exception as e:
                    logger.debug(f"Instagram check attempt {attempt+1} error: {str(e)}")
                    if attempt < 2:
                        sleep(1)
            
            if not ig_opened and caller not in avoid_lst:
                logger.warning("Instagram not detected after multiple checks")
                
                # Give Instagram more time to load, especially during initialization
                if "init" in caller.lower() or "profile" in caller.lower() or "view" in caller.lower():
                    logger.info("Detected initialization context, giving Instagram more time to load...")
                    sleep(3)
                    if self._ig_is_opened():
                        logger.info("Instagram detected after extended wait")
                        return func(self, **kwargs)
                
                # Give Instagram a moment to open if we're in navigation
                if "navigate" in caller.lower() or "search" in caller.lower():
                    logger.debug("Instagram not immediately detected, waiting briefly...")
                    sleep(2)
                    if self._ig_is_opened():
                        logger.info("Instagram detected after navigation wait")
                        return func(self, **kwargs)
                
                # Try to reopen Instagram instead of crashing immediately
                logger.info("Attempting to restart Instagram...")
                try:
                    self.deviceV2.app_start(self.app_id, wait=True)
                    sleep(3)
                    if self._ig_is_opened():
                        logger.info("Successfully reopened Instagram")
                        return func(self, **kwargs)
                    else:
                        logger.warning("Instagram restart attempted but still not detected")
                except Exception as e:
                    logger.warning(f"Failed to reopen Instagram: {e}")

                # Only raise the crash exception as a last resort
                logger.error("Instagram appears to have crashed or closed after all recovery attempts")
                raise DeviceFacade.AppHasCrashed("App has crashed / has been closed!")
            
            return func(self, **kwargs)

        return wrapper

    @check_if_ig_is_opened
    def find(
        self,
        index=None,
        **kwargs,
    ):
        try:
            view = self.deviceV2(**kwargs)
            if index is not None and view.count > 1:
                view = self.deviceV2(**kwargs)[index]
        except uiautomator2.JSONRPCError as e:
            raise DeviceFacade.JsonRpcError(e)
        return DeviceFacade.View(view=view, device=self.deviceV2)

    def back(self, modulable: bool = True):
        logger.debug("Press back button.")
        self.deviceV2.press("back")
        random_sleep(modulable=modulable)

    def start_screenrecord(self, output="debug_0000.mp4", fps=20):
        import imageio

        def _run_MOD(self):
            from collections import deque

            pipelines = [self._pipe_limit, self._pipe_convert, self._pipe_resize]
            _iter = self._iter_minicap()
            for p in pipelines:
                _iter = p(_iter)

            with imageio.get_writer(self._filename, fps=self._fps) as wr:
                frames = deque(maxlen=self._fps * 30)
                for im in _iter:
                    frames.append(im)
                if self.crash:
                    for frame in frames:
                        wr.append_data(frame)
            self._done_event.set()

        def stop_MOD(self, crash=True):
            """
            stop record and finish write video
            Returns:
                bool: whether video is recorded.
            """
            if self._running:
                self.crash = crash
                self._stop_event.set()
                ret = self._done_event.wait(10.0)

                # reset
                self._stop_event.clear()
                self._done_event.clear()
                self._running = False
                return ret

        from uiautomator2 import screenrecord as _sr

        _sr.Screenrecord._run = _run_MOD
        _sr.Screenrecord.stop = stop_MOD
        mp4_files = [f for f in listdir(getcwd()) if f.endswith(".mp4")]
        if mp4_files:
            last_mp4 = mp4_files[-1]
            debug_number = "{0:0=4d}".format(int(last_mp4[-8:-4]) + 1)
            output = f"debug_{debug_number}.mp4"
        self.deviceV2.screenrecord(output, fps)
        logger.warning("Screen recording has been started.")

    def stop_screenrecord(self, crash=True):
        if self.deviceV2.screenrecord.stop(crash=crash):
            logger.warning("Screen recorder has been stopped successfully!")

    def screenshot(self, path=None):
        if path is None:
            return self.deviceV2.screenshot()
        else:
            self.deviceV2.screenshot(path)

    def dump_hierarchy(self, path):
        try:
            # Try to dump hierarchy with retry logic
            xml_dump = None
            for attempt in range(3):
                try:
                    xml_dump = self.deviceV2.dump_hierarchy()
                    break
                except Exception as e:
                    logger.warning(f"dump_hierarchy attempt {attempt + 1} failed: {e}")
                    if attempt < 2:  # Don't sleep on last attempt
                        sleep(2)
                        # Try to recover UIAutomator2 if it's a NullPointerException
                        if "NullPointerException" in str(e):
                            logger.info("Attempting UIAutomator2 recovery due to NullPointerException")
                            self.recover_from_gateway_error()
            
            if xml_dump is None:
                # Fallback: create a minimal hierarchy dump
                logger.warning("All dump_hierarchy attempts failed, creating minimal dump")
                xml_dump = '<?xml version="1.0" encoding="UTF-8"?><hierarchy><node text="Hierarchy dump failed" /></hierarchy>'
            
            with open(path, "w", encoding="utf-8") as outfile:
                outfile.write(xml_dump)
                
        except Exception as e:
            logger.error(f"Failed to save hierarchy dump: {e}")
            # Create a basic error dump file
            try:
                with open(path, "w", encoding="utf-8") as outfile:
                    outfile.write(f'<?xml version="1.0" encoding="UTF-8"?><hierarchy><node text="Dump failed: {e}" /></hierarchy>')
            except:
                pass  # If we can't even write the error, just continue

    def press_power(self):
        self.deviceV2.press("power")
        sleep(2)

    def is_screen_locked(self):
        # Check if device is properly initialized
        if not self.is_valid():
            logger.warning("Device not properly initialized, cannot check screen lock status")
            return False

        try:
            data = run(
                f"adb -s {self.deviceV2.serial} shell dumpsys window",
                encoding="utf-8",
                stdout=PIPE,
                stderr=PIPE,
                shell=True,
            )
            if data != "":
                flag = search("mDreamingLockscreen=(true|false)", data.stdout)
                return flag is not None and flag.group(1) == "true"
            else:
                logger.debug(
                    f"'adb -s {self.deviceV2.serial} shell dumpsys window' returns nothing!"
                )
                return None
        except Exception as e:
            logger.warning(f"Error checking screen lock status: {str(e)}")
            return False

    def _is_keyboard_show(self):
        data = run(
            f"adb -s {self.deviceV2.serial} shell dumpsys input_method",
            encoding="utf-8",
            stdout=PIPE,
            stderr=PIPE,
            shell=True,
        )
        if data != "":
            flag = search("mInputShown=(true|false)", data.stdout)
            return flag.group(1) == "true"
        else:
            logger.debug(
                f"'adb -s {self.deviceV2.serial} shell dumpsys input_method' returns nothing!"
            )
            return None

    def is_alive(self):
        try:
            # Try the newer uiautomator2 API first
            return self.deviceV2.alive
        except AttributeError:
            try:
                # Fallback to deprecated method
                return self.deviceV2._is_alive()
            except AttributeError:
                try:
                    # Another fallback for different versions
                    return self.deviceV2.server.alive
                except AttributeError:
                    # Final fallback - just check if device object exists and is responsive
                    try:
                        self.deviceV2.info
                        return True
                    except Exception:
                        return False

    def is_valid(self):
        """Check if DeviceFacade is properly initialized and ready to use."""
        try:
            return (
                hasattr(self, 'deviceV2') and
                self.deviceV2 is not None and
                hasattr(self.deviceV2, 'serial') and
                self.deviceV2.serial is not None
            )
        except Exception:
            return False

    def wake_up(self):
        """Make sure agent is alive or bring it back up before starting."""
        if not self.is_valid():
            logger.warning("Device not properly initialized, skipping wake_up")
            return

        if self.deviceV2 is not None:
            attempts = 0
            while not self.is_alive() and attempts < 5:
                try:
                    self.get_info()
                    attempts += 1
                except Exception as e:
                    logger.warning(f"Wake-up attempt {attempts + 1} failed: {str(e)}")
                    attempts += 1
                    if attempts < 5:
                        sleep(1)

    def unlock(self):
        self.swipe(Direction.UP, 0.8)
        sleep(2)
        logger.debug(f"Screen locked: {self.is_screen_locked()}")
        if self.is_screen_locked():
            self.swipe(Direction.RIGHT, 0.8)
            sleep(2)
            logger.debug(f"Screen locked: {self.is_screen_locked()}")

    def screen_off(self):
        self.deviceV2.screen_off()

    def get_orientation(self):
        try:
            return self.deviceV2._get_orientation()
        except uiautomator2.JSONRPCError as e:
            raise DeviceFacade.JsonRpcError(e)

    def window_size(self):
        """return (width, height)"""
        try:
            self.deviceV2.window_size()
        except uiautomator2.JSONRPCError as e:
            raise DeviceFacade.JsonRpcError(e)

    def swipe(self, direction: Direction, scale=0.5):
        """Swipe finger in the `direction`.
        Scale is the sliding distance. Default to 50% of the screen width
        """
        swipe_dir = ""
        if direction == Direction.UP:
            swipe_dir = "up"
        elif direction == Direction.RIGHT:
            swipe_dir = "right"
        elif direction == Direction.LEFT:
            swipe_dir = "left"
        elif direction == Direction.DOWN:
            swipe_dir = "down"

        logger.debug(f"Swipe {swipe_dir}, scale={scale}")

        try:
            self.deviceV2.swipe_ext(swipe_dir, scale=scale)
            DeviceFacade.sleep_mode(SleepTime.TINY)
        except uiautomator2.JSONRPCError as e:
            raise DeviceFacade.JsonRpcError(e)

    def swipe_points(self, sx, sy, ex, ey, random_x=True, random_y=True):
        if random_x:
            sx = int(sx * uniform(0.85, 1.15))
            ex = int(ex * uniform(0.85, 1.15))
        if random_y:
            ey = int(ey * uniform(0.98, 1.02))
        sy = int(sy)
        try:
            logger.debug(f"Swipe from: ({sx},{sy}) to ({ex},{ey}).")
            self.deviceV2.swipe_points([[sx, sy], [ex, ey]], uniform(0.2, 0.5))
            DeviceFacade.sleep_mode(SleepTime.TINY)
        except uiautomator2.JSONRPCError as e:
            raise DeviceFacade.JsonRpcError(e)

    def get_info(self):
        # {'currentPackageName': 'net.oneplus.launcher', 'displayHeight': 1920, 'displayRotation': 0, 'displaySizeDpX': 411,
        # 'displaySizeDpY': 731, 'displayWidth': 1080, 'productName': 'OnePlus5', '
        #  screenOn': True, 'sdkInt': 27, 'naturalOrientation': True}
        max_retries = 3
        for attempt in range(max_retries):
            try:
                return self.deviceV2.info
            except uiautomator2.JSONRPCError as e:
                raise DeviceFacade.JsonRpcError(e)
            except Exception as e:
                if "InvalidVersion" in str(e) or "packaging.version" in str(e):
                    logger.warning(f"Version parsing error on attempt {attempt+1}: {str(e)}")
                    if attempt < max_retries - 1:
                        logger.info("Attempting to restart UIAutomator2 service...")
                        try:
                            import subprocess
                            subprocess.run([
                                "adb", "-s", str(self.device_id), "shell", 
                                "am", "force-stop", "com.github.uiautomator"
                            ], capture_output=True, timeout=10)
                            subprocess.run([
                                "adb", "-s", str(self.device_id), "shell", 
                                "am", "force-stop", "com.github.uiautomator.test"
                            ], capture_output=True, timeout=10)
                            sleep(2)
                        except Exception as restart_error:
                            logger.warning(f"UIAutomator2 restart failed: {str(restart_error)}")
                        sleep(1)
                    else:
                        logger.error(f"Failed to get device info after {max_retries} attempts")
                        # Return minimal info to prevent complete failure
                        return {
                            'productName': 'Unknown',
                            'sdkInt': 28,
                            'displayWidth': 1080,
                            'displayHeight': 1920,
                            'displaySizeDpX': 411,
                            'displaySizeDpY': 731,
                            'currentPackageName': 'unknown',
                            'screenOn': True,
                            'naturalOrientation': True
                        }
                else:
                    raise e

    @staticmethod
    def sleep_mode(mode):
        mode = SleepTime.DEFAULT if mode is None else mode
        if mode == SleepTime.DEFAULT:
            random_sleep()
        elif mode == SleepTime.TINY:
            random_sleep(0, 1)
        elif mode == SleepTime.SHORT:
            random_sleep(1, 2)
        elif mode == SleepTime.ZERO:
            pass

    class View:
        deviceV2 = None  # uiautomator2
        viewV2 = None  # uiautomator2

        def __init__(self, view, device):
            self.viewV2 = view
            self.deviceV2 = device
        
        def recover_ui_element(self, selector_func, max_attempts=3):
            """Recover UI element with multiple fallback methods"""
            for attempt in range(max_attempts):
                try:
                    element = selector_func()
                    if element and element.exists():
                        return element
                except Exception as e:
                    logger.warning(f"UI element recovery attempt {attempt + 1} failed: {e}")
                    if attempt < max_attempts - 1:
                        sleep(1)
                        # Try to recover from gateway errors
                        if hasattr(self.deviceV2, 'recover_from_gateway_error'):
                            self.deviceV2.recover_from_gateway_error()
            return None

        def __iter__(self):
            children = []
            try:
                children.extend(
                    DeviceFacade.View(view=item, device=self.deviceV2)
                    for item in self.viewV2
                )
                return iter(children)
            except uiautomator2.JSONRPCError as e:
                raise DeviceFacade.JsonRpcError(e)

        def ui_info(self):
            try:
                return self.viewV2.info
            except uiautomator2.JSONRPCError as e:
                raise DeviceFacade.JsonRpcError(e)

        def get_desc(self):
            try:
                return self.viewV2.info["contentDescription"]
            except uiautomator2.JSONRPCError as e:
                raise DeviceFacade.JsonRpcError(e)

        def child(self, *args, **kwargs):
            try:
                view = self.viewV2.child(*args, **kwargs)
            except uiautomator2.JSONRPCError as e:
                raise DeviceFacade.JsonRpcError(e)
            return DeviceFacade.View(view=view, device=self.deviceV2)

        def sibling(self, *args, **kwargs):
            try:
                view = self.viewV2.sibling(*args, **kwargs)
            except uiautomator2.JSONRPCError as e:
                raise DeviceFacade.JsonRpcError(e)
            return DeviceFacade.View(view=view, device=self.deviceV2)

        def left(self, *args, **kwargs):
            try:
                view = self.viewV2.left(*args, **kwargs)
            except uiautomator2.JSONRPCError as e:
                raise DeviceFacade.JsonRpcError(e)
            return DeviceFacade.View(view=view, device=self.deviceV2)

        def right(self, *args, **kwargs):
            try:
                view = self.viewV2.right(*args, **kwargs)
            except uiautomator2.JSONRPCError as e:
                raise DeviceFacade.JsonRpcError(e)
            return DeviceFacade.View(view=view, device=self.deviceV2)

        def up(self, *args, **kwargs):
            try:
                view = self.viewV2.up(*args, **kwargs)
            except uiautomator2.JSONRPCError as e:
                raise DeviceFacade.JsonRpcError(e)
            return DeviceFacade.View(view=view, device=self.deviceV2)

        def down(self, *args, **kwargs):
            try:
                view = self.viewV2.down(*args, **kwargs)
            except uiautomator2.JSONRPCError as e:
                raise DeviceFacade.JsonRpcError(e)
            return DeviceFacade.View(view=view, device=self.deviceV2)

        def click_gone(self, maxretry=3, interval=1.0):
            try:
                self.viewV2.click_gone(maxretry, interval)
            except uiautomator2.JSONRPCError as e:
                raise DeviceFacade.JsonRpcError(e)

        def click(self, mode=None, sleep=None, coord=None, crash_report_if_fails=True):
            if coord is None:
                coord = []
            mode = Location.WHOLE if mode is None else mode
            if mode == Location.WHOLE:
                x_offset = uniform(0.15, 0.85)
                y_offset = uniform(0.15, 0.85)

            elif mode == Location.LEFT:
                x_offset = uniform(0.15, 0.4)
                y_offset = uniform(0.15, 0.85)

            elif mode == Location.LEFTEDGE:
                x_offset = uniform(0.1, 0.2)
                y_offset = uniform(0.40, 0.60)

            elif mode == Location.CENTER:
                x_offset = uniform(0.4, 0.6)
                y_offset = uniform(0.15, 0.85)

            elif mode == Location.RIGHT:
                x_offset = uniform(0.6, 0.85)
                y_offset = uniform(0.15, 0.85)

            elif mode == Location.RIGHTEDGE:
                x_offset = uniform(0.8, 0.9)
                y_offset = uniform(0.40, 0.60)

            elif mode == Location.BOTTOMRIGHT:
                x_offset = uniform(0.8, 0.9)
                y_offset = uniform(0.8, 0.9)

            elif mode == Location.TOPLEFT:
                x_offset = uniform(0.05, 0.15)
                y_offset = uniform(0.05, 0.25)
            elif mode == Location.CUSTOM:
                try:
                    logger.debug(f"Single click ({coord[0]},{coord[1]})")
                    self.deviceV2.click(coord[0], coord[1])
                    DeviceFacade.sleep_mode(sleep)
                    return
                except uiautomator2.JSONRPCError as e:
                    if crash_report_if_fails:
                        raise DeviceFacade.JsonRpcError(e)
                    else:
                        logger.debug("Trying to press on a obj which is gone.")

            else:
                x_offset = 0.5
                y_offset = 0.5

            try:
                visible_bounds = self.get_bounds()
                x_abs = int(
                    visible_bounds["left"]
                    + (visible_bounds["right"] - visible_bounds["left"]) * x_offset
                )
                y_abs = int(
                    visible_bounds["top"]
                    + (visible_bounds["bottom"] - visible_bounds["top"]) * y_offset
                )

                logger.debug(
                    f"Single click in ({x_abs},{y_abs}). Surface: ({visible_bounds['left']}-{visible_bounds['right']},{visible_bounds['top']}-{visible_bounds['bottom']})"
                )
                self.viewV2.click(
                    self.get_ui_timeout(Timeout.LONG),
                    offset=(x_offset, y_offset),
                )
                DeviceFacade.sleep_mode(sleep)

            except uiautomator2.JSONRPCError as e:
                if crash_report_if_fails:
                    raise DeviceFacade.JsonRpcError(e)
                else:
                    logger.debug("Trying to press on a obj which is gone.")
            except Exception as e:
                if "GatewayError" in str(e) or "OSError" in str(e) or "EnvironmentError" in str(e) or "Uiautomator started failed" in str(e):
                    logger.warning(f"UIAutomator2 gateway error during click: {str(e)}")
                    if crash_report_if_fails:
                        # Try fallback click using coordinates
                        try:
                            visible_bounds = self.get_bounds()
                            x_abs = int(
                                visible_bounds["left"]
                                + (visible_bounds["right"] - visible_bounds["left"]) * 0.5
                            )
                            y_abs = int(
                                visible_bounds["top"]
                                + (visible_bounds["bottom"] - visible_bounds["top"]) * 0.5
                            )
                            logger.info(f"Fallback: Using device click at ({x_abs},{y_abs})")
                            self.device.deviceV2.click(x_abs, y_abs)
                            DeviceFacade.sleep_mode(sleep)
                        except Exception as fallback_error:
                            logger.error(f"Fallback click also failed: {str(fallback_error)}")
                            raise DeviceFacade.JsonRpcError(e)
                    else:
                        logger.debug("Gateway error during click, but crash_report_if_fails=False")
                else:
                    raise e

        def click_retry(self, mode=None, sleep=None, coord=None, maxretry=2):
            """return True if successfully open the element, else False"""
            if coord is None:
                coord = []
            self.click(mode, sleep, coord)

            while maxretry > 0:
                # we wait a little more before try again
                random_sleep(2, 4, modulable=False)
                if not self.exists():
                    return True
                logger.debug("UI element didn't open! Try again..")
                self.click(mode, sleep, coord)
                maxretry -= 1
            if not self.exists():
                return True
            logger.warning("Failed to open the UI element!")
            return False

        def double_click(self, padding=0.3, obj_over=0):
            """Double click randomly in the selected view using padding
            padding: % of how far from the borders we want the double
                    click to happen.
            """
            visible_bounds = self.get_bounds()
            horizontal_len = visible_bounds["right"] - visible_bounds["left"]
            vertical_len = visible_bounds["bottom"] - max(
                visible_bounds["top"], obj_over
            )
            horizontal_padding = int(padding * horizontal_len)
            vertical_padding = int(padding * vertical_len)
            random_x = int(
                uniform(
                    visible_bounds["left"] + horizontal_padding,
                    visible_bounds["right"] - horizontal_padding,
                )
            )
            random_y = int(
                uniform(
                    visible_bounds["top"] + vertical_padding,
                    visible_bounds["bottom"] - vertical_padding,
                )
            )

            time_between_clicks = uniform(0.050, 0.140)

            try:
                logger.debug(
                    f"Double click in ({random_x},{random_y}) with t={int(time_between_clicks*1000)}ms. Surface: ({visible_bounds['left']}-{visible_bounds['right']},{visible_bounds['top']}-{visible_bounds['bottom']})."
                )
                self.deviceV2.double_click(
                    random_x, random_y, duration=time_between_clicks
                )
                DeviceFacade.sleep_mode(SleepTime.DEFAULT)
            except uiautomator2.JSONRPCError as e:
                raise DeviceFacade.JsonRpcError(e)

        def scroll(self, direction):
            max_retries = 3
            for attempt in range(max_retries):
                try:
                    if direction == Direction.UP:
                        self.viewV2.scroll.toBeginning(max_swipes=1)
                    else:
                        self.viewV2.scroll.toEnd(max_swipes=1)
                    return  # Success, exit the retry loop
                except uiautomator2.JSONRPCError as e:
                    if "UiObjectNotFoundException" in str(e) and attempt < max_retries - 1:
                        logger.debug(f"Scroll attempt {attempt+1} failed, UI element not found. Retrying...")
                        sleep(1)
                        continue
                    elif "UiObjectNotFoundException" in str(e):
                        logger.warning(f"Scroll failed after {max_retries} attempts - UI element not found. Using fallback swipe.")
                        # Fallback: use manual swipe instead of scroll
                        try:
                            if direction == Direction.UP:
                                self.device.swipe(540, 800, 540, 1200, 500)  # Swipe up
                            else:
                                self.device.swipe(540, 1200, 540, 800, 500)  # Swipe down
                            return
                        except Exception as swipe_error:
                            logger.warning(f"Fallback swipe also failed: {str(swipe_error)}")
                            return  # Don't crash, just continue
                    else:
                        raise DeviceFacade.JsonRpcError(e)
                except Exception as e:
                    if "UiObjectNotFoundException" in str(e) and attempt < max_retries - 1:
                        logger.debug(f"Scroll attempt {attempt+1} failed with general exception. Retrying...")
                        sleep(1)
                        continue
                    else:
                        logger.warning(f"Scroll failed with unexpected error: {str(e)}")
                        return  # Don't crash, just continue

        def fling(self, direction):
            max_retries = 3
            for attempt in range(max_retries):
                try:
                    if direction == Direction.UP:
                        self.viewV2.fling.toBeginning(max_swipes=5)
                    else:
                        self.viewV2.fling.toEnd(max_swipes=5)
                    return  # Success, exit the retry loop
                except uiautomator2.JSONRPCError as e:
                    if "UiObjectNotFoundException" in str(e) and attempt < max_retries - 1:
                        logger.debug(f"Fling attempt {attempt+1} failed, UI element not found. Retrying...")
                        sleep(1)
                        continue
                    elif "UiObjectNotFoundException" in str(e):
                        logger.warning(f"Fling failed after {max_retries} attempts - UI element not found. Using fallback swipe.")
                        # Fallback: use manual swipe instead of fling
                        try:
                            if direction == Direction.UP:
                                self.device.swipe(540, 600, 540, 1400, 200)  # Fast swipe up
                            else:
                                self.device.swipe(540, 1400, 540, 600, 200)  # Fast swipe down
                            return
                        except Exception as swipe_error:
                            logger.warning(f"Fallback swipe also failed: {str(swipe_error)}")
                            return  # Don't crash, just continue
                    else:
                        raise DeviceFacade.JsonRpcError(e)
                except Exception as e:
                    if "UiObjectNotFoundException" in str(e) and attempt < max_retries - 1:
                        logger.debug(f"Fling attempt {attempt+1} failed with general exception. Retrying...")
                        sleep(1)
                        continue
                    else:
                        logger.warning(f"Fling failed with unexpected error: {str(e)}")
                        return  # Don't crash, just continue

        def exists(self, ui_timeout=None, ignore_bug: bool = False) -> bool:
            max_retries = 3
            for attempt in range(max_retries):
                try:
                    # Currently, the methods left, right, up and down from
                    # uiautomator2 return None when a Selector does not exist.
                    # All other selectors return an UiObject with exists() == False.
                    # We will open a ticket to uiautomator2 to fix this inconsistency.
                    if self.viewV2 is None:
                        return False
                    exists: bool = self.viewV2.exists(self.get_ui_timeout(ui_timeout))
                    if (
                        hasattr(self.viewV2, "count")
                        and not exists
                        and self.viewV2.count >= 1
                    ):
                        logger.debug(
                            f"UIA2 BUG: exists return False, but there is/are {self.viewV2.count} element(s)!"
                        )
                        if ignore_bug:
                            return "BUG!"
                        # More info about that: https://github.com/openatx/uiautomator2/issues/689"
                        return False
                    return exists
                except uiautomator2.JSONRPCError as e:
                    raise DeviceFacade.JsonRpcError(e)
                except Exception as e:
                    if "GatewayError" in str(e) or "OSError" in str(e) or "EnvironmentError" in str(e) or "Uiautomator started failed" in str(e):
                        if attempt < max_retries - 1:
                            logger.warning(f"UIAutomator2 gateway error on exists() attempt {attempt+1}, retrying: {str(e)}")
                            # Try to recover the connection
                            if self.deviceV2.recover_from_gateway_error():
                                logger.info("Gateway recovery successful, retrying exists() check")
                                sleep(1)
                                continue
                            else:
                                logger.warning("Gateway recovery failed, waiting before retry")
                                sleep(3)
                                continue
                        else:
                            logger.error(f"UIAutomator2 gateway error persisted after {max_retries} attempts: {str(e)}")
                            # Return False instead of crashing - assume element doesn't exist
                            return False
                    else:
                        # Re-raise other exceptions
                        raise e

        def count_items(self) -> int:
            try:
                return self.viewV2.count
            except uiautomator2.JSONRPCError as e:
                raise DeviceFacade.JsonRpcError(e)

        def wait(self, ui_timeout=Timeout.MEDIUM):
            try:
                return self.viewV2.wait(timeout=self.get_ui_timeout(ui_timeout))
            except uiautomator2.JSONRPCError as e:
                raise DeviceFacade.JsonRpcError(e)

        def wait_gone(self, ui_timeout=None):
            try:
                return self.viewV2.wait_gone(timeout=self.get_ui_timeout(ui_timeout))
            except uiautomator2.JSONRPCError as e:
                raise DeviceFacade.JsonRpcError(e)

        def is_above_this(self, obj2) -> Optional[bool]:
            obj1 = self.viewV2
            obj2 = obj2.viewV2
            try:
                if obj1.exists() and obj2.exists():
                    return obj1.info["bounds"]["top"] < obj2.info["bounds"]["top"]
                else:
                    return None
            except uiautomator2.JSONRPCError as e:
                raise DeviceFacade.JsonRpcError(e)

        def get_bounds(self) -> dict:
            max_retries = 3
            for attempt in range(max_retries):
                try:
                    return self.viewV2.info["bounds"]
                except uiautomator2.JSONRPCError as e:
                    if attempt < max_retries - 1:
                        logger.debug(f"get_bounds attempt {attempt+1} failed, retrying: {str(e)}")
                        sleep(0.5)
                    else:
                        logger.warning(f"get_bounds failed after {max_retries} attempts: {str(e)}")
                        raise DeviceFacade.JsonRpcError(e)
                except Exception as e:
                    if "UiObjectNotFoundException" in str(e) or "objInfo" in str(e):
                        logger.debug(f"UI element no longer exists for bounds check: {str(e)}")
                        # Return default bounds to prevent crash
                        return {"top": 0, "bottom": 100, "left": 0, "right": 100}
                    elif "RemoteDisconnected" in str(e) or "ConnectionError" in str(e) or "Connection aborted" in str(e):
                        if attempt < max_retries - 1:
                            logger.warning(f"Network connection error on get_bounds attempt {attempt+1}, retrying: {str(e)}")
                            # Try to recover the connection
                            if self.deviceV2.recover_from_gateway_error():
                                logger.info("Connection recovery successful, retrying get_bounds")
                                sleep(1)
                                continue
                            else:
                                logger.warning("Connection recovery failed, waiting before retry")
                                sleep(2)
                                continue
                        else:
                            logger.error(f"Network connection error persisted after {max_retries} attempts: {str(e)}")
                            # Return default bounds to prevent crash
                            return {"top": 0, "bottom": 100, "left": 0, "right": 100}
                    else:
                        raise DeviceFacade.JsonRpcError(e)

        def get_height(self) -> int:
            try:
                bounds = self.get_bounds()
                return bounds["bottom"] - bounds["top"]
            except DeviceFacade.JsonRpcError as e:
                if "UiObjectNotFoundException" in str(e):
                    logger.debug("UI element no longer exists for height check, returning default height")
                    return 100  # Return default height to prevent crash
                else:
                    raise e

        def get_width(self):
            try:
                bounds = self.get_bounds()
                return bounds["right"] - bounds["left"]
            except DeviceFacade.JsonRpcError as e:
                if "UiObjectNotFoundException" in str(e):
                    logger.debug("UI element no longer exists for width check, returning default width")
                    return 100  # Return default width to prevent crash
                else:
                    raise e

        def get_property(self, prop: str):
            max_retries = 3
            for attempt in range(max_retries):
                try:
                    return self.viewV2.info[prop]
                except uiautomator2.JSONRPCError as e:
                    raise DeviceFacade.JsonRpcError(e)
                except Exception as e:
                    if "RemoteDisconnected" in str(e) or "ConnectionError" in str(e) or "Connection aborted" in str(e):
                        if attempt < max_retries - 1:
                            logger.warning(f"Network connection error on get_property attempt {attempt+1}, retrying: {str(e)}")
                            sleep(1)
                            continue
                        else:
                            logger.error(f"Network connection error persisted after {max_retries} attempts: {str(e)}")
                            return None  # Return None instead of crashing
                    else:
                        raise DeviceFacade.JsonRpcError(e)

        def is_scrollable(self):
            try:
                if self.viewV2.exists():
                    return self.viewV2.info["scrollable"]
            except uiautomator2.JSONRPCError as e:
                raise DeviceFacade.JsonRpcError(e)

        @staticmethod
        def get_ui_timeout(ui_timeout: Timeout) -> int:
            ui_timeout = Timeout.ZERO if ui_timeout is None else ui_timeout
            if ui_timeout == Timeout.ZERO:
                ui_timeout = 0
            elif ui_timeout == Timeout.TINY:
                ui_timeout = 1
            elif ui_timeout == Timeout.SHORT:
                ui_timeout = 3
            elif ui_timeout == Timeout.MEDIUM:
                ui_timeout = 5
            elif ui_timeout == Timeout.LONG:
                ui_timeout = 8
            return ui_timeout

        def get_text(self, error=True, index=None):
            max_retries = 3
            for attempt in range(max_retries):
                try:
                    text = (
                        self.viewV2.info["text"]
                        if index is None
                        else self.viewV2[index].info["text"]
                    )
                    if text is not None:
                        return text
                except uiautomator2.JSONRPCError as e:
                    if "UiObjectNotFoundException" in str(e):
                        if attempt < max_retries - 1:
                            logger.debug(f"UI element not found for get_text attempt {attempt+1}, retrying...")
                            sleep(1)
                            continue
                        else:
                            logger.warning("UI element not found after retries in get_text, returning empty string")
                            return ""
                    elif error:
                        raise DeviceFacade.JsonRpcError(e)
                    else:
                        return ""
                except Exception as e:
                    if "GatewayError" in str(e) or "OSError" in str(e) or "EnvironmentError" in str(e):
                        if attempt < max_retries - 1:
                            logger.warning(f"Gateway error on get_text attempt {attempt+1}, retrying: {str(e)}")
                            if self.deviceV2.recover_from_gateway_error():
                                logger.info("Gateway recovery successful, retrying get_text")
                                sleep(1)
                                continue
                            else:
                                logger.warning("Gateway recovery failed, waiting before retry")
                                sleep(3)
                                continue
                        else:
                            logger.error(f"Gateway error persisted after {max_retries} attempts in get_text: {str(e)}")
                            if error:
                                raise DeviceFacade.JsonRpcError(e)
                            else:
                                return ""
                    else:
                        if error:
                            raise DeviceFacade.JsonRpcError(e)
                        else:
                            return ""
            logger.debug("Object exists but doesn't contain any text.")
            return ""

        def get_selected(self) -> bool:
            try:
                if self.viewV2.exists():
                    return self.viewV2.info["selected"]
                logger.debug(
                    "Object has disappeared! Probably too short video which has been liked!"
                )
                return True
            except uiautomator2.JSONRPCError as e:
                raise DeviceFacade.JsonRpcError(e)

        def set_text(self, text: str, mode: Mode = Mode.TYPE) -> None:
            punct_list = string.punctuation
            try:
                if mode == Mode.PASTE:
                    self.viewV2.set_text(text)
                else:
                    self.click(sleep=SleepTime.SHORT)
                    self.deviceV2.clear_text()
                    random_sleep(0.3, 1, modulable=False)
                    start = datetime.now()
                    sentences = text.splitlines()
                    for j, sentence in enumerate(sentences, start=1):
                        word_list = sentence.split()
                        n_words = len(word_list)
                        for n, word in enumerate(word_list, start=1):
                            i = 0
                            n_single_letters = randint(1, 3)
                            for char in word:
                                if i < n_single_letters:
                                    self.deviceV2.send_keys(char, clear=False)
                                    # random_sleep(0.01, 0.1, modulable=False, logging=False)
                                    i += 1
                                else:
                                    if word[-1] in punct_list:
                                        self.deviceV2.send_keys(word[i:-1], clear=False)
                                        # random_sleep(0.01, 0.1, modulable=False, logging=False)
                                        self.deviceV2.send_keys(word[-1], clear=False)
                                    else:
                                        self.deviceV2.send_keys(word[i:], clear=False)
                                    # random_sleep(0.01, 0.1, modulable=False, logging=False)
                                    break
                            if n < n_words:
                                self.deviceV2.send_keys(" ", clear=False)
                                # random_sleep(0.01, 0.1, modulable=False, logging=False)
                        if j < len(sentences):
                            self.deviceV2.send_keys("\n")

                    typed_text = self.viewV2.get_text()
                    if typed_text != text:
                        logger.warning(
                            "Failed to write in text field, let's try in the old way.."
                        )
                        self.viewV2.set_text(text)
                    else:
                        logger.debug(
                            f"Text typed in: {(datetime.now()-start).total_seconds():.2f}s"
                        )
                DeviceFacade.sleep_mode(SleepTime.SHORT)
            except uiautomator2.JSONRPCError as e:
                raise DeviceFacade.JsonRpcError(e)

    class JsonRpcError(Exception):
        pass

    class AppHasCrashed(Exception):
        pass
