# Discord Setup Guide for Ostium Trading Bot

This guide will help you set up Discord notifications and bot commands for your trading bot.

## 1. Discord Webhook Setup (for Notifications)

### Step 1: Create a Discord Server
1. Open Discord and create a new server or use an existing one
2. Create a dedicated channel for trading notifications (e.g., #trading-alerts)

### Step 2: Create a Webhook
1. Right-click on the channel you want to send notifications to
2. Select "Edit Channel"
3. Go to "Integrations" tab
4. Click "Create Webhook"
5. Give it a name (e.g., "Trading Bot")
6. Copy the webhook URL
7. Click "Save"

### Step 3: Configure Environment Variable
Add the webhook URL to your `.env` file:
```env
DISCORD_WEBHOOK_URL=https://discord.com/api/webhooks/your_webhook_url_here
```

## 2. Discord Bot Setup (for Commands)

### Step 1: Create a Discord Application
1. Go to [Discord Developer Portal](https://discord.com/developers/applications)
2. Click "New Application"
3. Give it a name (e.g., "Ostium Trading Bot")
4. Click "Create"

### Step 2: Create a Bot
1. In your application, go to the "Bot" section
2. Click "Add Bot"
3. Give your bot a username
4. Copy the bot token (you'll need this later)
5. Under "Privileged Gateway Intents", enable:
   - Message Content Intent
   - Server Members Intent

### Step 3: Generate Invite Link
1. Go to the "OAuth2" section
2. Click "URL Generator"
3. Under "Scopes", select:
   - `bot`
   - `applications.commands`
4. Under "Bot Permissions", select:
   - Send Messages
   - Use Slash Commands
   - Embed Links
   - Read Message History
5. Copy the generated URL and open it in your browser
6. Select your server and authorize the bot

### Step 4: Configure Environment Variable
Add the bot token to your `.env` file:
```env
DISCORD_BOT_TOKEN=your_bot_token_here
```

## 3. Available Discord Commands

Once the bot is running, you can use these slash commands in Discord:

### `/portfolio`
- Shows your current portfolio balance
- Displays total balance, available funds, and funds in positions
- Shows number of open positions

### `/positions`
- Lists all your current open positions
- Shows pair, side, size, leverage, entry price, and P&L
- Limited to 10 positions per message

### `/history`
- Shows your recent trading history
- Displays last 5 closed trades with P&L
- Shows entry/exit prices and trade status

### `/trades`
- Lists all open trades with their IDs
- Use this to see which trades you can close
- Shows trade ID format for closing

### `/closetrade <trade_id>`
- Closes a specific trade
- Use the trade ID from `/trades` command
- Format: `pair_id_index` (e.g., `1_0`)

## 4. Discord Notifications

The bot will automatically send notifications for:

### Trade Opened
- Symbol and side (Long/Short)
- Position size and entry price
- Leverage and transaction hash
- Stop loss and take profit levels

### Trade Closed
- Symbol and side
- Entry and exit prices
- P&L and P&L percentage
- Transaction hash

### Signal Received
- Symbol and signal ID
- Signal type (Entry/Exit)
- Position size and entry price

### Errors
- Error messages with context
- Helps with debugging issues

### Balance Updates
- Total balance
- Available funds
- Funds in positions

## 5. Running the Discord Bot

### Option 1: Run as Separate Process
```bash
python discord_bot.py
```

### Option 2: Integrate with Main Bot
You can modify the main trading bot to also run the Discord bot:

```python
# In trading_bot.py, add to main():
if __name__ == '__main__':
    # Initialize the bot
    asyncio.run(initialize_bot())
    
    # Start Discord bot in background
    discord_token = os.getenv('DISCORD_BOT_TOKEN')
    if discord_token:
        import threading
        discord_thread = threading.Thread(
            target=lambda: asyncio.run(run_discord_bot(trading_bot, discord_token))
        )
        discord_thread.daemon = True
        discord_thread.start()
    
    # Run the Flask app
    port = int(os.getenv('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=False)
```

## 6. Heroku Deployment

For Heroku deployment, add these environment variables:

```bash
heroku config:set DISCORD_WEBHOOK_URL=your_webhook_url
heroku config:set DISCORD_BOT_TOKEN=your_bot_token
```

## 7. Testing

### Test Webhook Notifications
1. Start your trading bot
2. Send a test signal to the webhook endpoint
3. Check if notifications appear in Discord

### Test Bot Commands
1. Start the Discord bot
2. Invite the bot to your server
3. Try the slash commands in Discord

## 8. Troubleshooting

### Bot Not Responding
- Check if the bot token is correct
- Ensure the bot has proper permissions
- Check the bot is online in your server

### No Notifications
- Verify the webhook URL is correct
- Check if the webhook is still active
- Look for errors in the bot logs

### Commands Not Working
- Make sure the bot has the required permissions
- Check if slash commands are synced
- Restart the bot if needed

## 9. Security Notes

- Never share your bot token publicly
- Use environment variables for sensitive data
- Regularly rotate your bot token
- Monitor bot permissions

## 10. Example Configuration

Your `.env` file should look like this:

```env
# Network Configuration
NETWORK_TYPE=testnet
PRIVATE_KEY=your_private_key
RPC_URL=your_rpc_url

# Bot Configuration
PORT=5000
DEFAULT_LEVERAGE=10
MAX_LEVERAGE=100
MIN_COLLATERAL=10
MAX_COLLATERAL=10000
SLIPPAGE_PERCENTAGE=2

# Discord Configuration
DISCORD_WEBHOOK_URL=https://discord.com/api/webhooks/your_webhook_url
DISCORD_BOT_TOKEN=your_bot_token
```

## 11. Advanced Features

### Custom Notifications
You can modify the `discord_notifier.py` file to add custom notifications for specific events.

### Multiple Channels
You can create multiple webhooks for different types of notifications (trades, errors, balance updates).

### Role-based Access
You can modify the bot to only allow certain roles to use trading commands.

## Support

If you encounter issues:
1. Check the bot logs for error messages
2. Verify all environment variables are set correctly
3. Test the webhook URL manually
4. Ensure the bot has proper permissions 