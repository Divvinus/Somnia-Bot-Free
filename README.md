# Singularity Finance Bot

A multi-functional bot for automating interactions with Singularity Finance Testnet. Supports Zealy tasks completion, faucet operations, Oracle tasks, liquidity management, and staking.

## 🚀 Key Features

- Automatic execution of all tasks (Auto Bot)
- Zealy tasks completion
- Obtaining test tokens through faucet
- Oracle tasks execution
- Token swaps via Citizens Swap
- Liquidity management (add/remove)
- WSFI staking (stake/unstake/claim rewards)

## 📋 Requirements

- Python 3.10+
- Windows/Linux
- Zealy.io account

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

### 🔧 Detailed settings.yaml Configuration

#### Common Parameters for All Token Modules:

```yaml
full_balance: true/false          # If true - uses 95% of balance
percentage_amount_flag: true/false # If true - uses percentage of balance
percentage_amount: 30             # Percentage of balance (works if percentage_amount_flag: true)
```

#### Swap Configuration (swap_config):
```yaml
swap_config:
  # Use only one selected pair
  active_pair_use: false
  
  # Selected pair (works if active_pair_use: true)
  active_pair:
    input: SFI
    output: AIMM
    
  # Available pairs for swapping
  available_pairs:
    - [SFI, WSFI]   # Swap SFI to WSFI
    - [SFI, USDC]   # Swap SFI to USDC
    - [SFI, AIMM]   # Swap SFI to AIMM
    - [WSFI, SFI]   # Reverse swap WSFI to SFI
    - [AIMM, SFI]   # Reverse swap AIMM to SFI
    - [USDC, SFI]   # Reverse swap USDC to SFI
    
  # Token amount settings for swaps
  full_balance: false            # Use 95% of balance
  percentage_amount_flag: true   # Use percentage of balance
  percentage_amount: 30          # Use 30% of balance
```

#### Add Liquidity Configuration (add_liquidity_config):
```yaml
add_liquidity_config:
  # Available pairs for adding liquidity
  available_pairs:
    - [SFI, AIMM]   # Add liquidity to SFI-AIMM pair
    - [SFI, USDC]   # Add liquidity to SFI-USDC pair
    - [WSFI, AIMM]  # Add liquidity to WSFI-AIMM pair
    - [WSFI, USDC]  # Add liquidity to WSFI-USDC pair
    - [AIMM, USDC]  # Add liquidity to AIMM-USDC pair
    
  # Token amount settings
  full_balance: false            # Use 95% of balance
  percentage_amount_flag: true   # Use percentage of balance
  percentage_amount: 10          # Use 10% of balance
```

#### Remove Liquidity Configuration (remove_liquidity_config):
```yaml
remove_liquidity_config:
  # Available pairs for removing liquidity
  available_pairs:
    - [SFI, AIMM]   # Remove liquidity from SFI-AIMM pair
    - [SFI, USDC]   # Remove liquidity from SFI-USDC pair
    - [WSFI, AIMM]  # Remove liquidity from WSFI-AIMM pair
    - [WSFI, USDC]  # Remove liquidity from WSFI-USDC pair
    - [AIMM, USDC]  # Remove liquidity from AIMM-USDC pair
    
  # Token amount settings
  full_balance: true             # Use 95% of balance
  percentage_amount_flag: false  # Don't use percentage of balance
  percentage_amount: 20          # Not used since percentage_amount_flag: false
```

#### Staking Configuration (staking_config):
```yaml
staking_config:
  available_token: WSFI          # Token for staking
  full_balance: false           # Don't use full balance
  percentage_amount_flag: true  # Use percentage of balance
  percentage_amount: 25         # Use 25% of balance
```

#### Unstaking Configuration (unstaking_config):
```yaml
unstaking_config:
  available_token: WSFI          # Token for unstaking
  full_balance: false           # Don't use full balance
  percentage_amount_flag: true  # Use percentage of balance
  percentage_amount: 10         # Use 10% of balance
  min_available_amount: 5       # Minimum amount of tokens for unstaking
```

### Configuration Notes:

1. If `full_balance: true` is set, then `percentage_amount_flag` and `percentage_amount` are ignored
2. Each operation can have its own balance usage percentage
3. When working with pairs, the bot will use the first available pair from the list
4. For swaps with `active_pair_use: false`, the bot will automatically select the most liquid pair

### 1. Configuration Files

Create the following files in the `config/` directory:

#### wallets.txt
```
private_key_or_mnemonic
private_key_or_mnemonic
...
```

#### proxies.txt
```
http://user:pass@ip:port
http://ip:port:user:pass
...
```

### 2. Zealy Setup

1. Log in to Zealy.io
2. Open browser console (F12)
3. Insert the following code:
```javascript
const links = document.querySelectorAll('a');
let accessToken = '';
let userMetadata = '';
let userId = '';

links.forEach(function(link) {
  if (link.href && link.href.includes('/users/')) {
    const match = link.href.match(/\/users\/([a-f0-9\-]{36})/);
    if (match && match[1]) {
      userId = match[1];
    }
  }
});

const cookies = document.cookie.split(';');
cookies.forEach(function(cookie) {
  const cookieArray = cookie.split('=');
  const name = cookieArray[0].trim();
  const value = cookieArray[1]?.trim() || '';

  if (name === 'access_token') {
    accessToken = value;
  } else if (name === 'user_metadata') {
    userMetadata = value;
  }
});

console.log(userId + ':' + accessToken + ':' + userMetadata);
```
4. Copy the result to `config/cookies.txt`

### 3. Twitter Setup

1. Open Twitter.com (X)
2. Go to Developer Tools (F12) -> Application -> Cookies
3. Find and copy the `auth_token` value
4. Paste it into `config/auth_tokens.txt`

### 4. settings.yaml Configuration

Basic configuration parameters:

```yaml
# Number of threads
threads: 10

# Delay before start (seconds)
delay_before_start:
    min: 10
    max: 1000

# API keys for captcha solving
cap_monster: ""
two_captcha: ""
capsolver: ""
```

## 🚀 Launch

```bash
python run.py
```

## ⚠️ Important Notes

1. All private keys/mnemonics should be in one line = one key format
2. Proxies must be working and follow the correct format
3. Valid auth_token is required for Twitter functionality
4. Correct access_token and user_metadata are required for Zealy

## 🔍 Troubleshooting

1. "24 hours have not yet passed since the last token request" - wait 24 hours before next faucet request
2. "Failed to obtain the address to send the transaction" - Oracle API issues
3. "Task failed: returned None" - error in Zealy tasks execution, check cookies

## 📚 Available Commands

After launching the bot, the following options are available:
1. 🤖 SINGULARITY AUTO BOT (ALL TASKS)
2. 📝 Zealy
3. 💸 Requesting tokens from the faucet
4. 🔍 Oracle tasks
5. 🔄 Swap token swap
6. 💧 Add Liquidity
7. 🔙 Remove Liquidity
8. 🔓 Stake WSFI
9. 🔐 Unstake WSFI
10. 💰 Claim staking rewards