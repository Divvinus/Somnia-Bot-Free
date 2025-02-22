# Somnia Quest Bot

A multi-functional bot for automating interactions with Somnia Network Testnet. Supports account registration, social network linking, quest completion, and token management.

## 🚀 Key Features

- Automatic Account Registration and Setup
  - Username creation and binding
  - Discord and Twitter connection
  - Referral code activation
- Socials Quests 1 Completion
  - Social networks connection
  - Referral tasks completion
- Token Management
  - Obtaining test tokens via faucet
  - STT token transfers
- Advanced Features
  - Automatic referral recruitment
  - Account statistics monitoring

## 📋 Requirements

- Python 3.10+
- Windows/Linux
- Discord account
- Twitter account

## 🛠️ Installation

1. Clone the repository:
```bash
git clone [repository URL]
```

2. Create and activate virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # Linux
.\venv\Scripts\activate   # Windows
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

## ⚙️ Configuration

### 1. Configuration Files

Create the following files in the `config/data/` directory:

#### wallets.txt
```
private_key_or_mnemonic
private_key_or_mnemonic
...
```

#### auth_tokens.txt (for Twitter)
```
auth_token1
auth_token2
...
```

#### token_discord.txt
```
discord_token1
discord_token2
...
```

#### proxies.txt (optional)
```
login:password@ip:port
ip:port:login:password
...
```

#### referral_codes.txt (for referral recruitment)
```
# Format: referral_code:number_of_referrals
47DBF064:10
B52ZX891:5
...
```

Note: One code per line. After the code, add a colon and specify the required number of referrals for this code.

### 2. Twitter Setup

1. Open Twitter.com
2. Go to Developer Tools (F12) -> Application -> Cookies
3. Find and copy the `auth_token` value
4. Paste it into `config/data/auth_tokens.txt`

### 3. Discord Setup

1. Get Discord token (found in request headers as "authorization")
2. Token should either start with "mfa." or contain alphanumeric token
3. Add it to `config/data/token_discord.txt`

### 4. settings.yaml Configuration

```yaml
# Number of threads
threads: 10

# Delay before start (seconds)
delay_before_start:
    min: 1
    max: 100

# API keys for captcha solving
cap_monster: ""
two_captcha: ""
capsolver: ""

# Referral code for registration
referral_code: "YOUR_CODE"
```

## 🚀 Launch

```bash
python run.py
```

## 📚 Available Commands

After launching the bot, the following options are available:
1. 👤 Profile - Setup profile and link social networks
2. 💰 Faucet - Get test tokens
3. 💸 Transfer STT - Transfer tokens
4. 🎯 Socials Quests 1 - Complete social quests
5. 📊 Account Statistics - View account statistics
6. 👥 Recruiting Referrals - Referral recruitment

## 🔍 Troubleshooting

1. "Failed to authorize on Somnia" - check private key validity
2. "Failed to connect Discord/Twitter" - verify token validity
3. "Please wait 24 hours between requests" - wait 24 hours between faucet requests
4. "Not enough balance" - insufficient tokens for transfer

## ⚠️ Important Notes

1. All private keys/mnemonics should be in one line = one key format
2. Proxies must be working and follow the correct format
3. Valid auth_token is required for Twitter functionality
4. Valid Discord token is required for Discord operations
5. It's recommended to configure delays to avoid blocks

## ⚠️ Disclaimer

Use the bot at your own risk. The author is not responsible for any consequences of using the bot, including account blocks or loss of funds.