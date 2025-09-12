# Instamatic

<p align="center">
  <img src="https://github.com/Instamatic/bot/raw/master/res/logo.png" alt="Instamatic Logo">
  <br />
  <h1 align="center">Instamatic</h1>
  <br />
  <p align="center">Professional Instagram automation tool for Android devices. Grow your following and engagement with human-like interactions - <b>100% free and open source</b>. <b>No root required.</b></p>
  <p align="center">
    <a href="https://github.com/Instamatic/bot/blob/master/LICENSE">
      <img src="https://img.shields.io/github/license/Instamatic/bot?style=flat" alt="License"/>
    </a>
    <a href="https://www.python.org/">
      <img src="https://img.shields.io/badge/built%20with-Python3-red.svg?style=flat" alt="Python"/>
    </a>
    <a href="https://github.com/Instamatic/bot/pulls">
      <img src="https://img.shields.io/badge/PRs-welcome-brightgreen.svg?style=flat" alt="PRs Welcome"/>
    </a>
    <a href="https://github.com/Instamatic/bot/issues">
      <img src="https://img.shields.io/github/issues/Instamatic/bot?style=flat" alt="Issues"/>
    </a>
    <a href="https://github.com/Instamatic/bot/stargazers">
      <img src="https://img.shields.io/github/stars/Instamatic/bot?style=flat" alt="Stars"/>
    </a>
    <a href="https://img.shields.io/github/last-commit/Instamatic/bot/master?style=flat">
      <img src="https://img.shields.io/github/last-commit/Instamatic/bot/master?style=flat" alt="Last Commit"/>
    </a>
    <img src="https://img.shields.io/badge/tested_with_instagram-330.0.0.40.92-green" alt="Tested with Instagram 330.0.0.40.92"/>
  </p>
</p>

---

## ⚡ Quick Start - Multi-Account Automation

**Want to run multiple Instagram accounts? It's super easy!**

```bash
# 1. Create multiple accounts
python run.py init account1
python run.py init account2
python run.py init account3

# 2. Configure each account (edit config.yml files)

# 3. Run ALL accounts automatically
./scripts/auto_run_managed.sh
```

**That's it!** Instamatic will automatically cycle through all your accounts, running each one with its own settings and limits. No manual intervention needed!

---

## 🚀 What is Instamatic?

Instamatic is a professional-grade Instagram automation tool designed for Android devices. It simulates human-like interactions to help grow your Instagram following and engagement organically. Unlike API-based bots that risk account suspension, Instamatic uses Android's UI automation framework to interact with Instagram naturally.

### ✨ Key Features

- **🤖 Human-like Automation**: Realistic delays, typing patterns, and interaction behaviors
- **📱 No Root Required**: Works on any Android device or emulator
- **🔒 Account Safe**: Uses UI automation instead of risky API calls
- **⚙️ Highly Configurable**: Extensive customization options for every action
- **📊 Detailed Analytics**: Comprehensive reporting and statistics
- **🔄 Multi-Account Support**: Manage unlimited Instagram accounts with automated scripts
- **⚡ Auto-Run Scripts**: Run multiple accounts automatically with `./auto_run_managed.sh`
- **📱 Cross-Platform**: Works on Windows, macOS, and Linux
- **🎯 Smart Filtering**: Advanced targeting and filtering options

---

## 🎯 Why Choose Instamatic?

### Traditional Instagram Bots vs Instamatic

| Feature | Traditional API Bots | Instamatic |
|---------|---------------------|------------|
| **Account Safety** | ❌ High ban risk (1-30 days) | ✅ Very low risk |
| **Detection** | ❌ Easily detected | ✅ Human-like behavior |
| **Cost** | ❌ Often paid/subscription | ✅ 100% Free & Open Source |
| **Transparency** | ❌ Encrypted/closed source | ✅ Fully open source |
| **Customization** | ❌ Limited options | ✅ Extensive configuration |
| **Reliability** | ❌ Breaks with Instagram updates | ✅ Auto-adapts to UI changes |

### 🛡️ Safety First

Instamatic is designed with account safety as the top priority:

- **Human-like behavior patterns** prevent detection
- **Realistic delays** between actions
- **Smart limits** to avoid Instagram's anti-bot measures
- **Gradual scaling** to build organic-looking activity
- **No API usage** - works through the official Instagram app

---

## 🚀 Quick Start Guide

### Prerequisites

- **Computer**: Windows, macOS, or Linux
- **Python**: Version 3.6-3.9 (3.10+ not supported)
- **Android Device**: Physical device or emulator (Android 4.4+)
- **ADB Tools**: Android Debug Bridge installed
- **Instagram**: Latest version installed and logged in

### Installation

#### 1. Clone the Repository

```bash
git clone https://github.com/Instamatic/bot.git
cd bot
```

#### 2. Create Virtual Environment

```bash
# Create virtual environment
python3 -m venv venv

# Activate virtual environment
# On Windows:
venv\Scripts\activate
# On macOS/Linux:
source venv/bin/activate
```

#### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

#### 4. Install ADB Tools

**Windows:**
1. Download [Android Platform Tools](https://developer.android.com/studio/releases/platform-tools)
2. Extract to a permanent location (e.g., `C:\platform-tools`)
3. Add to PATH environment variable

**macOS:**
```bash
brew install android-platform-tools
```

**Linux:**
```bash
sudo apt-get install android-tools-adb
```

#### 5. Set Up Android Device

**Physical Device:**
1. Enable Developer Options and USB Debugging
2. Connect via USB cable
3. Allow USB debugging when prompted

**Emulator:**
- Use Android Studio's AVD Manager
- Recommended: Pixel 2 API 28 or newer

#### 6. Verify Setup

```bash
# Check ADB connection
adb devices

# Should show your device:
# List of devices attached
# A0B1CD2345678901    device
```

### First Run

#### 1. Initialize Instamatic

```bash
python run.py init your_username
```

This creates your account configuration folder at `accounts/your_username/`

#### 2. Configure Your Account

Edit `accounts/your_username/config.yml`:

```yaml
# Basic Configuration
device: "your_device_id"  # From 'adb devices'
app-id: "com.instagram.android"
username: "your_username"
password: "your_password"

# Safety Settings
follow-limit: 10-15
like-limit: 50-80
comment-limit: 5-10

# Actions to perform
actions:
  - interact_blogger:
      username: "target_account"
      amount: 20
      randomize: true
```

#### 3. Start Botting

```bash
python run.py run --config accounts/your_username/config.yml
```

---

## 🚀 Multi-Account Automation (Auto-Run Scripts)

**Instamatic's most powerful feature: Run unlimited Instagram accounts automatically!**

### Why Use Auto-Run Scripts?

- **🔄 Unlimited Accounts**: Run as many Instagram accounts as you want
- **⏰ Automated Scheduling**: Set up accounts to run at different times
- **🛡️ Account Safety**: Each account runs independently with its own limits
- **📊 Centralized Management**: Monitor all accounts from one place
- **🔄 Round-Robin**: Automatically cycle through accounts
- **⚡ Easy Setup**: One-time configuration, runs forever

### Quick Multi-Account Setup

#### 1. Initialize Multiple Accounts

```bash
# Create accounts for different purposes
python run.py init business_account
python run.py init personal_account  
python run.py init niche_account
python run.py init backup_account
```

#### 2. Configure Each Account

Edit each account's `config.yml` with different settings:

```yaml
# accounts/business_account/config.yml
device: "your_device_id"
username: "business_account"
follow-limit: 20-30
like-limit: 100-150

# accounts/personal_account/config.yml  
device: "your_device_id"
username: "personal_account"
follow-limit: 10-15
like-limit: 50-80
```

#### 3. Use Auto-Run Scripts

**Option A: Managed Auto-Run (Recommended)**
```bash
# Runs all accounts with smart management
./scripts/auto_run_managed.sh
```

**Option B: Individual Auto-Run Scripts**
```bash
# Run specific accounts
./scripts/auto_run_2.sh  # Account 1
./scripts/auto_run_3.sh  # Account 2  
./scripts/auto_run_4.sh  # Account 3
./scripts/auto_run_5.sh  # Account 4
```

### Auto-Run Script Features

#### 🔄 **Round-Robin Execution**
- Automatically cycles through all configured accounts
- Each account runs for its configured session length
- Built-in delays between account switches
- Prevents account overlap and conflicts

#### ⏰ **Smart Scheduling**
- Configurable session lengths per account
- Automatic pause between sessions
- Error handling and recovery
- Logging for each account

#### 🛡️ **Account Safety**
- Each account has independent limits
- No cross-account interference
- Individual error tracking
- Automatic restart on failures

#### 📊 **Monitoring & Logs**
- Separate log files for each account
- Real-time status monitoring
- Performance tracking
- Error reporting

### Advanced Multi-Account Configuration

#### Custom Auto-Run Script

Create your own auto-run script:

```bash
#!/bin/bash
# custom_auto_run.sh

ACCOUNTS=("account1" "account2" "account3" "account4")
DEVICE_ID="your_device_id"

for account in "${ACCOUNTS[@]}"; do
    echo "Starting $account..."
    python run.py run --config "accounts/$account/config.yml" --device "$DEVICE_ID"
    
    # Wait between accounts
    sleep 300  # 5 minutes
done
```

#### Scheduled Multi-Account Execution

Set up cron jobs for different accounts:

```bash
# Edit crontab
crontab -e

# Run different accounts at different times
0 9 * * * cd /path/to/Instamatic && ./auto_run_2.sh    # 9 AM
0 14 * * * cd /path/to/Instamatic && ./auto_run_3.sh   # 2 PM  
0 19 * * * cd /path/to/Instamatic && ./auto_run_4.sh   # 7 PM
0 22 * * * cd /path/to/Instamatic && ./auto_run_5.sh   # 10 PM
```

### Multi-Account Best Practices

#### 🎯 **Account Segmentation**
- **Business Accounts**: Higher limits, professional targeting
- **Personal Accounts**: Lower limits, casual interactions
- **Niche Accounts**: Specific hashtag/location targeting
- **Backup Accounts**: Spare accounts for testing

#### ⚙️ **Configuration Strategy**
```yaml
# High-volume business account
follow-limit: 30-50
like-limit: 200-300
session-length: 60-90

# Conservative personal account  
follow-limit: 5-10
like-limit: 20-40
session-length: 20-30
```

#### 🛡️ **Safety Guidelines**
- **Different Devices**: Use different devices for different account types
- **Time Separation**: Run accounts at different times of day
- **Content Variation**: Use different content strategies per account
- **Limit Variation**: Vary limits and patterns between accounts

### Monitoring Multiple Accounts

#### Real-Time Monitoring
```bash
# Monitor all account logs
tail -f logs/*.log

# Monitor specific account
tail -f logs/business_account.log

# Check account status
ps aux | grep "run.py"
```

#### Performance Tracking
```bash
# Check account performance
ls -la logs/
grep "Session finished" logs/*.log
grep "Error" logs/*.log
```

---

## 📋 Complete Feature List

### 🔄 Core Actions

- **Follow Users**: Follow followers/following of target accounts
- **Unfollow Users**: Smart unfollowing with various strategies
- **Like Posts**: Like posts from hashtags, locations, or users
- **Comment**: Human-like commenting with emoji support
- **Send DMs**: Direct message users with personalized content
- **Watch Stories**: View and interact with stories
- **Watch Videos**: Watch videos for realistic durations

### 🎯 Targeting Options

- **Hashtag Targeting**: Target specific hashtags (top/recent posts)
- **Location Targeting**: Target specific locations
- **User Targeting**: Target specific users' followers/following
- **Feed Interaction**: Interact with your own feed
- **List-based Targeting**: Use custom user/post lists

### 🛡️ Safety Features

- **Smart Limits**: Configurable daily/hourly limits
- **Human Delays**: Realistic delays between actions
- **Randomization**: Random action patterns
- **Blacklist/Whitelist**: User filtering
- **Profile Filtering**: Advanced user profile filtering
- **Session Management**: Smart session handling

### 📊 Analytics & Reporting

- **Real-time Stats**: Live statistics during operation
- **Detailed Reports**: Comprehensive activity reports
- **Telegram Integration**: Get reports via Telegram
- **Data Export**: Export data for analysis
- **Performance Metrics**: Track growth and engagement

---

## 📖 Detailed Configuration

### Account Configuration (`config.yml`)

```yaml
# Device Settings
device: "your_device_id"
app-id: "com.instagram.android"

# Account Credentials
username: "your_username"
password: "your_password"

# Safety Limits (per session)
follow-limit: 10-15
like-limit: 50-80
comment-limit: 5-10
unfollow-limit: 20-30

# Session Settings
session-length: 30-60  # minutes
session-pause: 10-20   # minutes between sessions

# Actions Configuration
actions:
  - interact_blogger:
      username: "target_account"
      amount: 20
      randomize: true
      follow: true
      like: true
      comment: true
      comment-probability: 0.3
      
  - interact_hashtag:
      hashtag: "photography"
      amount: 30
      randomize: true
      follow: true
      like: true
      
  - unfollow_non_followers:
      amount: 20
      only_not_follow_me: true
```

---

## 🔧 Advanced Usage

### Multi-Account Management

**Instamatic supports unlimited Instagram accounts with automated management!**

```bash
# Initialize multiple accounts
python run.py init business_account
python run.py init personal_account
python run.py init niche_account

# Run specific account manually
python run.py run --config accounts/business_account/config.yml

# Run ALL accounts automatically (RECOMMENDED)
./scripts/auto_run_managed.sh

# Or use individual auto-run scripts
./scripts/auto_run_2.sh  # Runs account 1
./scripts/auto_run_3.sh  # Runs account 2
./scripts/auto_run_4.sh  # Runs account 3
./scripts/auto_run_5.sh  # Runs account 4
```

**Key Benefits:**
- 🔄 **Unlimited Accounts**: Run as many as you want
- ⏰ **Automated Scheduling**: Set and forget
- 🛡️ **Account Safety**: Each account runs independently
- 📊 **Centralized Logging**: Monitor all accounts from one place

### Custom Actions

Create custom interaction patterns:

```yaml
actions:
  - interact_blogger:
      username: "influencer_account"
      amount: 50
      follow: true
      like: true
      comment: true
      comment-probability: 0.2
      stories: true
      
  - interact_hashtag:
      hashtag: "yourniche"
      amount: 100
      follow: true
      like: true
      stories: true
      
  - unfollow_non_followers:
      amount: 30
      only_not_follow_me: true
      skip_whitelist: true
```

---

## 📊 Monitoring and Analytics

### Real-time Monitoring

```bash
# Monitor bot activity
tail -f logs/your_account.log

# Check device status
python uiautomator2_monitor.py
```

### Telegram Reports

Set up Telegram bot for automated reports:

1. Create bot with [@BotFather](https://t.me/botfather)
2. Get bot token
3. Get your chat ID
4. Configure `telegram.yml`
5. Receive automated reports

---

## 🛠️ Troubleshooting

### Common Issues

**Device Not Found:**
```bash
# Check ADB connection
adb devices

# Restart ADB server
adb kill-server
adb start-server
```

**Instagram Not Responding:**
```bash
# Check Instagram app
adb shell am start -n com.instagram.android/.MainActivity

# Clear Instagram cache
adb shell pm clear com.instagram.android
```

**Bot Crashes:**
```bash
# Check logs
tail -f logs/your_account.log

# Restart with debug mode
python run.py run --config accounts/your_account/config.yml --debug
```

---

## 🔒 Safety Guidelines

### Account Protection

1. **Start Slow**: Begin with minimal activity
2. **Be Realistic**: Use human-like patterns
3. **Monitor Closely**: Watch for Instagram warnings
4. **Take Breaks**: Don't run 24/7
5. **Quality Content**: Ensure your content is engaging

### Best Practices

- **Follow Limits**: 10-20 follows per session maximum
- **Like Limits**: 50-100 likes per session maximum
- **Comment Limits**: 5-10 comments per session maximum
- **Session Length**: 30-60 minutes maximum
- **Break Time**: 2-4 hours between sessions

### Warning Signs

- Instagram asking for phone verification
- Reduced reach on posts
- Account temporarily restricted
- Unusual login notifications

If you see these signs, **STOP** and take a break for 24-48 hours.

---

## 🤝 Contributing

We welcome contributions! Here's how you can help:

### Development Setup

```bash
# Fork the repository
git clone https://github.com/yourusername/Instamatic.git
cd Instamatic

# Create development environment
python3 -m venv dev_env
source dev_env/bin/activate  # On Windows: dev_env\Scripts\activate

# Install development dependencies
pip install -r requirements.txt
pip install -r requirements-dev.txt

# Run tests
python -m pytest test/
```

### Areas for Contribution

- **Bug Fixes**: Report and fix bugs
- **New Features**: Add new functionality
- **Documentation**: Improve documentation
- **Testing**: Add test coverage
- **UI Improvements**: Enhance user experience

---

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

---

## ⚠️ Disclaimer

**Important**: This tool is for educational and research purposes only. Users are responsible for complying with Instagram's Terms of Service and applicable laws. The developers are not responsible for any account suspensions or other consequences resulting from the use of this tool.

**Use at your own risk**: While Instamatic is designed to be safe, Instagram's policies and detection methods can change. Always use realistic settings and monitor your account closely.

---

## 🆘 Support

### Getting Help

- **Documentation**: Check this README and configuration files
- **Issues**: Open an issue on GitHub
- **Discussions**: Use GitHub Discussions for questions
- **Community**: Join our community for support

### Reporting Issues

When reporting issues, please include:

1. **System Information**: OS, Python version, device type
2. **Configuration**: Your config files (remove sensitive data)
3. **Logs**: Relevant log files
4. **Steps to Reproduce**: Clear steps to reproduce the issue
5. **Expected vs Actual**: What you expected vs what happened

---

## 🎉 Acknowledgments

- **Original Developers**: Based on the original GramAddict project
- **Community**: All contributors and users
- **Open Source**: Built on amazing open source libraries
- **Android Community**: For UIAutomator2 and related tools

---

## 📈 Roadmap

### Upcoming Features

- **Web Dashboard**: Browser-based control panel
- **AI-Powered Targeting**: Smart user targeting
- **Advanced Analytics**: Detailed growth analytics
- **Mobile App**: Native mobile application
- **Cloud Deployment**: Easy cloud hosting options

### Version History

- **v3.2.12**: Current stable version
- **Tested with**: Instagram 330.0.0.40.92
- **Next**: v3.3.0 with enhanced features

---

**Made with ❤️ for the Instagram automation community**

*Instamatic - Professional Instagram automation, simplified.*
