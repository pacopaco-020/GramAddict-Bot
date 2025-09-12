"""Human-like Instagram bot powered by UIAutomator2"""

__version__ = "3.2.12"
__tested_ig_version__ = "330.0.0.40.92"

from Instamatic.core.bot_flow import start_bot


def run(**kwargs):
    start_bot(**kwargs)
