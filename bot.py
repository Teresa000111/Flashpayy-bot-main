
from keep_alive import keep_alive
import json
import os
from telegram import (
    Update, InlineKeyboardButton, InlineKeyboardMarkup,
    ReplyKeyboardMarkup, KeyboardButton
)
from telegram.ext import (
    ApplicationBuilder, CommandHandler, MessageHandler,
    CallbackQueryHandler, ContextTypes, filters
)

# Load from environment or fallback
TOKEN = "8121739214:AAEK80VGwuS09y_exayUS6PRDryAldvbmkg"
ADMIN_ID = 6806039390
DATA_FILE = "users.json"
WITHDRAWALS_FILE = "withdrawals.json"

REQUIRED_CHANNELS = [
    {"name": "Main Channel", "url": "https://t.me/flashpayyofficial"},
    {"name": "Community", "url": "https://t.me/kdfub1QqG79jNDU0"},
    {"name": "Partnership", "url": "https://t.me/Dark_toolz51"},
    {"name": "Withdraw Channel", "url": "https://t.me/flashpayybot"},
]

MIN_WITHDRAW = 20000
MAX_WITHDRAW = 500000
REQUIRED_REFERRALS = 20

def load_json(path):
    if not os.path.exists(path):
        with open(path, "w") as f:
            json.dump({}, f)
    with open(path, "r") as f:
        return json.load(f)

def save_json(path, data):
    with open(path, "w") as f:
        json.dump(data, f, indent=2)

def init_user(user_id):
    data = load_json(DATA_FILE)
    if str(user_id) not in data:
        data[str(user_id)] = {"balance": 0, "referrals": [], "invited_by": None}
        save_json(DATA_FILE, data)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    user_id = str(user.id)
    init_user(user_id)

    if context.args:
        ref_id = context.args[0]
        if ref_id != user_id:
            data = load_json(DATA_FILE)
            if ref_id in data and user_id not in data[ref_id]["referrals"]:
                data[ref_id]["referrals"].append(user_id)
                data[ref_id]["balance"] += 3000
                save_json(DATA_FILE, data)
                await context.bot.send_message(chat_id=ref_id, text="🎉 Someone joined with your referral link!")

    buttons = [[InlineKeyboardButton(ch["name"], url=ch["url"])] for ch in REQUIRED_CHANNELS]
    buttons.append([InlineKeyboardButton("✅ I've Joined", callback_data="joined")])
    await update.message.reply_text("📢 Please join all required channels:", reply_markup=InlineKeyboardMarkup(buttons))

async def joined(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    keyboard = [
        ["📥Withdraw", "📢Channels"],
        ["🧑‍🤝‍🧑Invite", "💰Balance"],
        ["Earn more ⚡"]
    ]
    await query.message.reply_text("✅ Access granted!", reply_markup=ReplyKeyboardMarkup(keyboard, resize_keyboard=True))

async def balance(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = str(update.effective_user.id)
    init_user(user_id)
    data = load_json(DATA_FILE)
    user = data[user_id]
    bal = user["balance"]
    refs = len(user["referrals"])

    leaderboard = sorted(data.items(), key=lambda x: len(x[1]["referrals"]), reverse=True)
    rank = "\n".join([f"{i+1}. User {uid}: {len(info['referrals'])} invites" for i, (uid, info) in enumerate(leaderboard[:5])])

    await update.message.reply_text(f"""ℹ️ Information

💰 Balance: ₦{bal:,}
👤 Total Invites: {refs}

💳 Withdrawal requires 20 invites
💸 Min: ₦20,000 | Max: ₦500,000

🏆 Top Referrers:
{rank}

👥 Invite more to earn more!
""")

async def invite(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = str(update.effective_user.id)
    bot_name = context.bot.username
    link = f"https://t.me/{bot_name}?start={user_id}"
    await update.message.reply_text(f"👥 Invite Friends with this link:\n{link}\n\n💰 You earn ₦3,000 per referral!")

async def channels(update: Update, context: ContextTypes.DEFAULT_TYPE):
    buttons = [[InlineKeyboardButton(ch["name"], url=ch["url"])] for ch in REQUIRED_CHANNELS]
    await update.message.reply_text("📢 Join all channels:", reply_markup=InlineKeyboardMarkup(buttons))

withdraw_stage = {}

async def withdraw(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = str(update.effective_user.id)
    data = load_json(DATA_FILE)
    user = data[user_id]
    bal = user["balance"]
    refs = len(user["referrals"])

    if bal < MIN_WITHDRAW:
        return await update.message.reply_text(f"❌ Minimum withdrawal is ₦{MIN_WITHDRAW:,}\n👤 Referrals: {refs}")
    if bal > MAX_WITHDRAW:
        return await update.message.reply_text(f"❌ Max withdrawal is ₦{MAX_WITHDRAW:,}")
    if refs < REQUIRED_REFERRALS:
        return await update.message.reply_text(f"❌ You need {REQUIRED_REFERRALS} referrals to withdraw.\n👤 Referrals: {refs}")

    withdraw_stage[user_id] = {"step": 1}
    await update.message.reply_text("💳 Enter your *Account Number*:", parse_mode="Markdown")

async def process_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = str(update.effective_user.id)
    if user_id not in withdraw_stage:
        return
    stage = withdraw_stage[user_id]

    if stage["step"] == 1:
        stage["account_number"] = update.message.text
        stage["step"] = 2
        await update.message.reply_text("🧑 Enter *Account Holder Name*:", parse_mode="Markdown")

    elif stage["step"] == 2:
        stage["account_name"] = update.message.text
        stage["step"] = 3
        banks = [
            ["Opay", "Palmpay"], ["Access Bank Plc", "Zenith Bank Plc"],
            ["First Bank", "UBA Plc"], ["GTBank", "Fidelity Bank"],
            ["Union Bank", "Stanbic IBTC"], ["Ecobank", "Polaris Bank"],
            ["Wema Bank", "Sterling Bank"], ["FCMB", "Keystone Bank"],
            ["Unity Bank", "Providus Bank"], ["Globus Bank", "Titan Trust Bank"],
            ["Parallex Bank", "SunTrust Bank"]
        ]
        buttons = [[KeyboardButton(name) for name in row] for row in banks]
        await update.message.reply_text("🏦 Select your *Bank*:", reply_markup=ReplyKeyboardMarkup(buttons, resize_keyboard=True), parse_mode="Markdown")

    elif stage["step"] == 3:
        stage["bank"] = update.message.text
        stage["step"] = 4

        withdrawals = load_json(WITHDRAWALS_FILE)
        withdrawals[user_id] = {
            "account_number": stage["account_number"],
            "account_name": stage["account_name"],
            "bank": stage["bank"],
            "status": "pending_payment"
        }
        save_json(WITHDRAWALS_FILE, withdrawals)

        await update.message.reply_text(f"""💸 *Withdrawal Fee Required*
DEAR USER, WE HAVE RECEIVED YOUR WITHDRAWAL REQUEST.
DUE TO ELECTRONIC TRANSFER LEVY, PAY ₦2,000 TO:

🧾 *7040488044*
🏦 *Moniepoint MFB*
👤 *CHINEDU PETER*

After payment, click below:
✅ *I Have Paid*
""", parse_mode="Markdown", reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("✅ I Have Paid", callback_data="paid_confirm")]
        ]))

async def paid_confirm(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    user_id = str(query.from_user.id)
    await query.answer()
    context_data = load_json(WITHDRAWALS_FILE).get(user_id, {})

    text = f"""💳 *New Withdrawal Request*
👤 User: `{user_id}`
🏦 Bank: {context_data.get('bank')}
👤 Name: {context_data.get('account_name')}
💳 Account: {context_data.get('account_number')}

Approve?"""
    await context.bot.send_message(chat_id=ADMIN_ID, text=text, parse_mode="Markdown", reply_markup=InlineKeyboardMarkup([
        [InlineKeyboardButton("✅ Approve", callback_data=f"approve_{user_id}"),
         InlineKeyboardButton("🚫 Decline", callback_data=f"decline_{user_id}")]
    ]))
    await query.message.reply_text("✅ Payment under review!")

async def handle_admin_action(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    data = query.data

    withdrawals = load_json(WITHDRAWALS_FILE)
    uid = data.split("_")[1]

    if uid in withdrawals:
        if data.startswith("approve_"):
            withdrawals[uid]["status"] = "pending"
            await context.bot.send_message(chat_id=uid, text="✅ Your withdrawal has been approved and is pending.")
        elif data.startswith("decline_"):
            withdrawals[uid]["status"] = "declined"
            await context.bot.send_message(chat_id=uid, text="❌ Your payment was not confirmed. Withdrawal declined.")
        save_json(WITHDRAWALS_FILE, withdrawals)
        await query.message.reply_text(f"✅ Admin responded to {uid}")

async def unknown(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("❓ Use the buttons to navigate the bot.")

# Setup
app = ApplicationBuilder().token(TOKEN).build()
app.add_handler(CommandHandler("start", start))
app.add_handler(CallbackQueryHandler(joined, pattern="joined"))
app.add_handler(CallbackQueryHandler(paid_confirm, pattern="paid_confirm"))
app.add_handler(CallbackQueryHandler(handle_admin_action, pattern="^(approve_|decline_).+"))
app.add_handler(MessageHandler(filters.Text("💰Balance"), balance))
app.add_handler(MessageHandler(filters.Text("🧑‍🤝‍🧑Invite"), invite))
app.add_handler(MessageHandler(filters.Text("📥Withdraw"), withdraw))
app.add_handler(MessageHandler(filters.Text("📢Channels"), channels))
app.add_handler(MessageHandler(filters.TEXT, process_message))
app.add_handler(MessageHandler(filters.ALL, unknown))

if __name__ == "__main__":
    print("✅ Bot is running...")
    keep_alive()
    app.run_polling()
