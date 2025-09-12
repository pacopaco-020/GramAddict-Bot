import logging
from functools import partial
from random import seed
import ruamel.yaml

from colorama import Style

from Instamatic.core.decorators import run_safely
from Instamatic.core.handle_sources import handle_likers
from Instamatic.core.interaction import (
    interact_with_user,
    is_follow_limit_reached_for_source,
)
from Instamatic.core.plugin_loader import Plugin
from Instamatic.core.scroll_end_detector import ScrollEndDetector
from Instamatic.core.utils import get_value, init_on_things, sample_sources

logger = logging.getLogger(__name__)

# Script Initialization
seed()


class InteractBloggerPostLikers(Plugin):
    """Handles the functionality of interacting with a blogger post likers"""

    def __init__(self):
        super().__init__()
        self.description = (
            "Handles the functionality of interacting with a blogger post likers"
        )
        self.arguments = [
            {
                "arg": "--blogger-post-likers",
                "nargs": "+",
                "help": "interact with likers of post for a specified blogger",
                "metavar": ("blogger1", "blogger2"),
                "default": None,
                "operation": True,
            },
            {
                "arg": "--blogger-post-limits",
                "nargs": None,
                "help": "limit the posts you're looking for likers",
                "metavar": "2",
                "default": 0,
            },
        ]

    def run(self, device, configs, storage, sessions, profile_filter, plugin):
        self.args = configs.args
        self.device_id = configs.args.device
        self.session_state = sessions[-1]
        self.sessions = sessions
        self.current_mode = plugin
        self.profile_filter = profile_filter
        self.configs = configs  # Add this

        (
            on_interaction,
            stories_percentage,
            likes_percentage,
            follow_percentage,
            comment_percentage,
            pm_percentage,
            interact_percentage,
        ) = init_on_things(
            None,  # Change to None instead of blogger
            self.args, self.sessions, self.session_state
        )

        # Set as instance attributes
        self.stories_percentage = stories_percentage
        self.likes_percentage = likes_percentage
        self.follow_percentage = follow_percentage
        self.comment_percentage = comment_percentage
        self.pm_percentage = pm_percentage
        self.interact_percentage = interact_percentage

        # Create proper interaction function
        interaction = partial(
            interact_with_user,
            my_username=self.session_state.my_username,
            likes_count=self.args.likes_count,
            likes_percentage=likes_percentage,
            stories_percentage=stories_percentage,
            follow_percentage=follow_percentage,
            comment_percentage=comment_percentage,
            pm_percentage=pm_percentage,
            profile_filter=profile_filter,
            args=self.args,
            session_state=self.session_state,
            scraping_file=getattr(self.args, 'scrape_to_file', None),
            current_mode=self.current_mode,
        )

        @run_safely(
            device=device,
            device_id=self.device_id,
            sessions=self.sessions,
            session_state=self.session_state,
            screen_record=self.args.screen_record,
            configs=configs,
        )
        def job():
            self.handle_blogger_from_file(
                device,
                self.args.blogger_post_likers,
                self.current_mode,
                storage,
                on_interaction,
                interaction,
                partial(is_follow_limit_reached_for_source, self.session_state, None, None),
            )

        job()

    def handle_blogger_from_file(
        self,
        device,
        parameter_passed,
        current_job,
        storage,
        on_interaction,
        interaction,
        is_follow_limit_reached,
    ):
        source = parameter_passed
        bloggers = sample_sources(source, self.args.truncate_sources)
        skipped_list_limit = get_value(self.args.skipped_list_limit, None, 15)
        skipped_fling_limit = get_value(self.args.fling_when_skipped, None, 0)

        posts_end_detector = ScrollEndDetector(
            repeats_to_end=2,
            skipped_list_limit=skipped_list_limit,
            skipped_fling_limit=skipped_fling_limit,
        )

        for blogger in bloggers:
            # Handle the blogger
            result = handle_likers(
                self,
                device,
                self.session_state,
                blogger,
                current_job,
                storage,
                self.profile_filter,
                posts_end_detector,
                on_interaction,
                interaction,
                is_follow_limit_reached,
            )

            # Check if blogger was depleted and remove from config
            if result == "DEPLETED":
                logger.info(f"Blogger '{blogger}' depleted - removing from config")
                try:
                    self.remove_depleted_blogger(self.configs.args.config, blogger)  # Use self.configs
                    logger.info(f"Successfully removed depleted blogger '{blogger}' from config")
                except Exception as e:
                    logger.warning(f"Failed to remove blogger '{blogger}' from config: {str(e)}")

            logger.info(f"Completed handling blogger '{blogger}'")

    def remove_depleted_blogger(self, config_path, blogger):
        """
        Surgically remove a blogger from the config file while preserving ALL formatting.
        Uses regex to find and remove only the specific blogger name from the list.
        Handles YAML files with duplicate keys or other parsing issues.
        """
        import re
        
        try:
            # Read the entire file as text
            with open(config_path, 'r') as f:
                content = f.read()
            
            # Find the blogger-post-likers line using regex
            pattern = r'(blogger-post-likers:\s*\[)([^\]]+)(\])'
            match = re.search(pattern, content)
            
            if not match:
                logger.warning(f"Could not find blogger-post-likers list in {config_path}")
                return
            
            prefix = match.group(1)  # "blogger-post-likers: ["
            bloggers_part = match.group(2)  # the list content
            suffix = match.group(3)  # "]"
            
            # Split the bloggers, strip whitespace, and check if our blogger exists
            bloggers = [b.strip() for b in bloggers_part.split(',')]
            
            if blogger not in bloggers:
                logger.warning(f"Blogger '{blogger}' not found in blogger-post-likers list")
                return
            
            # Remove the blogger while preserving exact spacing
            new_bloggers = [b for b in bloggers if b != blogger]
            
            if not new_bloggers:
                logger.warning(f"Cannot remove '{blogger}' - it's the last blogger in the list")
                return
            
            # Reconstruct the list with original spacing style
            new_bloggers_part = ', '.join(new_bloggers)
            
            # Replace just the blogger list part, keeping everything else identical
            new_line = prefix + new_bloggers_part + suffix
            new_content = content.replace(match.group(0), new_line)
            
            # Write back the file with minimal changes
            with open(config_path, 'w') as f:
                f.write(new_content)
            
            logger.info(f"Surgically removed '{blogger}' from blogger-post-likers in {config_path}")
            
        except Exception as e:
            logger.warning(f"Failed to surgically remove blogger '{blogger}': {str(e)}")
            logger.info("Continuing without removing blogger from config due to YAML parsing issues")
            # Don't raise - just log and continue since this is not critical for bot operation