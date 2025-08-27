import json
import logging
import os
from datetime import datetime, timedelta
from typing import Optional, Dict, List, Set, Tuple
from pathlib import Path

import requests
import yaml
from colorama import Fore, Style

from GramAddict.core.plugin_loader import Plugin

logger = logging.getLogger(__name__)


def load_sessions(username) -> Optional[dict]:
    try:
        sessions_path = Path(f"accounts/{username}/sessions.json")
        if not sessions_path.exists():
            logger.error(f"No sessions data found for {username}.")
            return []

        with open(sessions_path, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception as e:
        logger.error(f"Error loading sessions: {e}")
        return []


def load_telegram_config(username) -> Optional[dict]:
    try:
        telegram_config_path = os.path.join("accounts", username, "telegram.yml")
        if not os.path.exists(telegram_config_path):
            logger.error(
                f"No telegram configuration found at {telegram_config_path}. "
                "Please create one using the example in the docs."
            )
            return None

        with open(telegram_config_path, "r", encoding="utf-8") as stream:
            return yaml.safe_load(stream)
    except Exception as e:
        logger.error(f"Error loading telegram config: {e}")
        return None


def load_interacted_users(username) -> Optional[dict]:
    try:
        with open(f"accounts/{username}/interacted_users.json", encoding="utf-8") as json_file:
            return json.load(json_file)
    except FileNotFoundError:
        logger.error("No interacted users data found.")
        return {}


def telegram_bot_send_text(bot_token, bot_chatID, bot_message):
    try:
        # Ensure bot_message is a string
        if isinstance(bot_message, list):
            bot_message = "\n".join(str(item) for item in bot_message)
        elif not isinstance(bot_message, str):
            bot_message = str(bot_message)

        # Ensure bot_token and bot_chatID are strings
        bot_token = str(bot_token)
        bot_chatID = str(bot_chatID)
        
        send_text = (
            "https://api.telegram.org/bot"
            + bot_token
            + "/sendMessage?chat_id="
            + bot_chatID
            + "&parse_mode=Markdown&text="
            + bot_message
        )
        response = requests.get(send_text)
        return response.json()
    except ImportError:
        logger.error(
            "The Telegrm plugin need additional dependencies, please install requirements.txt"
        )
        return None
    except Exception as e:
        logger.error(f"Error sending telegram message: {e}")
        return None


def _initialize_aggregated_data():
    return {
        "total_likes": 0,
        "total_watched": 0,
        "total_followed": 0,
        "total_unfollowed": 0,
        "total_comments": 0,
        "total_pm": 0,
        "duration": 0,
        "followers": float("inf"),
        "following": float("inf"),
        "followers_gained": 0,
        "followers_gained_from_bot": 0,  # New field for tracking followers from bot actions
        "followers_gained_from_follows": 0,  # From follow actions specifically
        "followers_gained_from_other": 0,   # From other interactions (likes, comments, etc.)
    }


def _calculate_session_duration(session):
    try:
        start_datetime = datetime.strptime(
            session["start_time"], "%Y-%m-%d %H:%M:%S.%f"
        )
        finish_datetime = datetime.strptime(
            session["finish_time"], "%Y-%m-%d %H:%M:%S.%f"
        )
        return int((finish_datetime - start_datetime).total_seconds() / 60)
    except ValueError:
        logger.debug(
            f"{session['id']} has no finish_time. Skipping duration calculation."
        )
        return 0


def daily_summary(sessions, username):
    daily_aggregated_data = {}
    interacted_users = load_interacted_users(username)
    
    for session in sessions:
        date = session["start_time"][:10]
        daily_aggregated_data.setdefault(date, _initialize_aggregated_data())
        duration = _calculate_session_duration(session)
        daily_aggregated_data[date]["duration"] += duration

        for key in [
            "total_likes",
            "total_watched",
            "total_followed",
            "total_unfollowed",
            "total_comments",
            "total_pm",
        ]:
            daily_aggregated_data[date][key] += session.get(key, 0)

        followers = session.get("profile", {}).get("followers")
        if followers is not None:
            daily_aggregated_data[date]["followers"] = min(
                followers, daily_aggregated_data[date]["followers"]
            )

        following = session.get("profile", {}).get("following")
        if following is not None:
            daily_aggregated_data[date]["following"] = min(
                following, daily_aggregated_data[date]["following"]
            )

    # Calculate followers gained from bot actions
    if interacted_users:
        daily_aggregated_data = _calculate_followers_gained_from_bot(daily_aggregated_data, interacted_users, sessions)

    return _calculate_followers_gained(daily_aggregated_data)


def _calculate_followers_gained_from_bot(aggregated_data, interacted_users, sessions):
    """
    Calculate the number of followers gained from bot actions.
    This looks at users who interacted with the bot in any way and then followed back.
    """
    if not interacted_users:
        return aggregated_data
    
    # Get session dates and their IDs for reference
    session_dates: Dict[str, List[str]] = {}
    for session in sessions:
        date = session["start_time"][:10]
        if date not in session_dates:
            session_dates[date] = []
        session_dates[date].append(session["id"])
    
    # For each date, find users who interacted with our bot and then followed us back
    for date, session_ids in session_dates.items():
        if date not in aggregated_data:
            continue
            
        bot_followed_users: Set[str] = set()
        bot_interacted_users: Set[str] = set()
        users_who_followed_back_follows: Set[str] = set()
        users_who_followed_back_other: Set[str] = set()
        
        for username, data in interacted_users.items():
            # Check if this user was interacted with on this date
            if "session_id" in data and data["session_id"] in session_ids:
                # Check if the bot followed this user
                if data.get("followed", False):
                    bot_followed_users.add(username)
                
                # Check if the bot interacted with this user in any other way
                if (data.get("liked", 0) > 0 or 
                    data.get("watched", 0) > 0 or 
                    data.get("commented", 0) > 0 or 
                    data.get("pm_sent", False)):
                    bot_interacted_users.add(username)
                
                # User is now following us (either through a "FOLLOWED" or "NONE" status but not "UNFOLLOWED")
                following_status = data.get("following_status", "").lower()
                if following_status in ["followed", "none"] and not following_status == "unfollowed":
                    # If we followed them and they followed back
                    if data.get("followed", False):
                        users_who_followed_back_follows.add(username)
                    # If we interacted with them in any other way and they followed back
                    elif username in bot_interacted_users:
                        users_who_followed_back_other.add(username)
        
        # Set the count of users who followed back from bot actions
        aggregated_data[date]["followers_gained_from_follows"] = len(users_who_followed_back_follows)
        aggregated_data[date]["followers_gained_from_other"] = len(users_who_followed_back_other)
        aggregated_data[date]["followers_gained_from_bot"] = (
            len(users_who_followed_back_follows) + len(users_who_followed_back_other)
        )
    
    return aggregated_data


def _calculate_followers_gained(aggregated_data):
    dates_sorted = sorted(aggregated_data.keys())
    previous_followers = None
    for date in dates_sorted:
        current_followers = aggregated_data[date]["followers"]
        if previous_followers is not None and previous_followers != float("inf"):
            followers_gained = current_followers - previous_followers if current_followers != float("inf") else 0
            aggregated_data[date]["followers_gained"] = followers_gained
            
            # Make sure followers_gained_from_bot doesn't exceed total followers_gained
            if "followers_gained_from_bot" in aggregated_data[date]:
                if followers_gained > 0:
                    # Ensure bot-attributed followers don't exceed actual follower gain
                    aggregated_data[date]["followers_gained_from_bot"] = min(
                        aggregated_data[date]["followers_gained_from_bot"],
                        followers_gained
                    )
                else:
                    # If no followers gained or lost followers, don't attribute any to bot actions
                    aggregated_data[date]["followers_gained_from_bot"] = 0
                    aggregated_data[date]["followers_gained_from_follows"] = 0
                    aggregated_data[date]["followers_gained_from_other"] = 0
                    
        previous_followers = current_followers
    return aggregated_data


def check_source_accounts(username):
    """Check the number of blogger-post-likers in config.yml and return a warning if below 6"""
    try:
        config_path = os.path.join("accounts", username, "config.yml")
        warning = ""
        
        if os.path.exists(config_path):
            with open(config_path, "r") as f:
                config = yaml.safe_load(f)
                
            if "blogger-post-likers" in config:
                source_count = len(config["blogger-post-likers"])
                if source_count < 6:
                    warning = f"\n\n⚠️ *WARNING: Only {source_count} source accounts remaining!*\nPlease add more blogger-post-likers accounts soon."
        
        return warning
    except Exception as e:
        logger.warning(f"Error checking source accounts: {e}")
        return ""


def generate_report(
    username,
    last_session,
    daily_aggregated_data,
    weekly_average_data,
    followers_now,
    following_now,
):
    # Get followers gained from bot actions
    followers_gained_from_bot = daily_aggregated_data.get("followers_gained_from_bot", 0)
    followers_from_follows = daily_aggregated_data.get("followers_gained_from_follows", 0)
    followers_from_other = daily_aggregated_data.get("followers_gained_from_other", 0)
    
    weekly_bot_followers = weekly_average_data.get("followers_gained_from_bot", 0)
    weekly_follows_followers = weekly_average_data.get("followers_gained_from_follows", 0)
    weekly_other_followers = weekly_average_data.get("followers_gained_from_other", 0)
    
    # Check source accounts and get warning if needed
    source_warning = check_source_accounts(username)

    return f"""
            *Stats for {username}*:{source_warning}

            *✨Overview after last activity*
            • {followers_now} followers
            • {following_now} following

            *🤖 Last session actions*
            • {last_session["duration"]} minutes of botting
            • {last_session["total_likes"]} likes
            • {last_session["total_followed"]} follows
            • {last_session["total_unfollowed"]} unfollows
            • {last_session["total_watched"]} stories watched
            • {last_session["total_comments"]} comments done
            • {last_session["total_pm"]} PM sent

            *📅 Today's total actions*
            • {daily_aggregated_data["duration"]} minutes of botting
            • {daily_aggregated_data["total_likes"]} likes
            • {daily_aggregated_data["total_followed"]} follows
            • {daily_aggregated_data["total_unfollowed"]} unfollows
            • {daily_aggregated_data["total_watched"]} stories watched
            • {daily_aggregated_data["total_comments"]} comments done
            • {daily_aggregated_data["total_pm"]} PM sent

            *📈 Trends*
            • {int(daily_aggregated_data["followers_gained"])} new followers today ({int(followers_gained_from_bot)} from bot actions)
            • {int(weekly_average_data["followers_gained"])} new followers this week ({int(weekly_bot_followers)} from bot actions)

            *🗓 7-Day Average*
            • {int(weekly_average_data["duration"] / 7)} minutes of botting
            • {int(weekly_average_data["total_likes"] / 7)} likes
            • {int(weekly_average_data["total_followed"] / 7)} follows
            • {int(weekly_average_data["total_unfollowed"] / 7)} unfollows
            • {int(weekly_average_data["total_watched"] / 7)} stories watched
            • {int(weekly_average_data["total_comments"] / 7)} comments done
            • {int(weekly_average_data["total_pm"] / 7)} PM sent
        """


def weekly_average(daily_aggregated_data, today) -> dict:
    weekly_average_data = _initialize_aggregated_data()

    for date in daily_aggregated_data:
        if (today - datetime.strptime(date, "%Y-%m-%d")).days > 7:
            continue
        for key in [
            "total_likes",
            "total_watched",
            "total_followed",
            "total_unfollowed",
            "total_comments",
            "total_pm",
            "duration",
            "followers_gained",
            "followers_gained_from_bot",
            "followers_gained_from_follows",
            "followers_gained_from_other",
        ]:
            weekly_average_data[key] += daily_aggregated_data[date].get(key, 0)
    return weekly_average_data


class TelegramReports(Plugin):
    """Generate reports at the end of the session and send them using telegram"""

    def __init__(self):
        super().__init__()
        self.description = "Generate reports at the end of the session and send them using telegram. You have to configure 'telegram.yml' in your account folder"
        self.arguments = [
            {
                "arg": "--telegram-reports",
                "help": "at the end of every session send a report to your telegram account",
                "action": "store_true",
                "operation": True,
            }
        ]

    def run(self, config, plugin, followers_now, following_now, time_left):
        username = config.args.username
        if username is None:
            logger.error("You have to specify a username for getting reports!")
            return

        sessions = load_sessions(username)
        if not sessions:
            logger.error(
                f"No session data found for {username}. Skipping report generation."
            )
            return

        last_session = sessions[-1]
        last_session["duration"] = _calculate_session_duration(last_session)

        telegram_config = load_telegram_config(username)
        if not telegram_config:
            logger.error(
                f"No telegram configuration found for {username}. Skipping report generation."
            )
            return

        daily_aggregated_data = daily_summary(sessions, username)
        today_data = daily_aggregated_data.get(last_session["start_time"][:10], {})
        today = datetime.now()
        weekly_average_data = weekly_average(daily_aggregated_data, today)
        report = generate_report(
            username,
            last_session,
            today_data,
            weekly_average_data,
            followers_now,
            following_now,
        )
        response = telegram_bot_send_text(
            telegram_config.get("telegram-api-token"),
            telegram_config.get("telegram-chat-id"),
            report,
        )
        if response and response.get("ok"):
            logger.info(
                "Telegram message sent successfully.",
                extra={"color": f"{Style.BRIGHT}{Fore.BLUE}"},
            )
        else:
            error = response.get("description") if response else "Unknown error"
            logger.error(f"Failed to send Telegram message: {error}")
