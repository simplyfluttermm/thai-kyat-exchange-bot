import logging
import os
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, ReplyKeyboardRemove
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    CallbackQueryHandler,
    ConversationHandler,
    ContextTypes,
    filters,
)
from flask import Flask
import threading
from database import (
    init_db, get_rates, update_rates, get_bank_accounts, 
    add_bank_account, clear_bank_accounts, create_transaction, 
    get_transaction, update_transaction_status, is_admin, add_admin, get_all_admins
)
from config import BOT_TOKEN, INITIAL_ADMIN_ID

# Enable logging
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)
logger = logging.getLogger(__name__)

# Conversation states
SET_RATES = 1
ADD_BANK_NAME, ADD_BANK_ACC, ADD_BANK_OWNER = range(2, 5)
EXCHANGE_AMOUNT, EXCHANGE_PAYMENT_INFO, EXCHANGE_PROOF = range(5, 8)
ADMIN_APPROVE_PROOF = 8

# Burmese Messages
MSG_START = "မင်္ဂလာပါ! ထိုင်း-မြန်မာ ငွေလဲ Bot မှ ကြိုဆိုပါတယ်။\n\nအောက်ပါ Menu များမှ ရွေးချယ်နိုင်ပါတယ် -"
MSG_RATES = "📊 ယနေ့ ငွေလဲနှုန်းများ\n\n🇹🇭 1 Baht = {baht_to_kyat} Kyats\n🇲🇲 100,000 Kyats = {kyat_to_baht} Baht\n\nနောက်ဆုံးပြင်ဆင်ချိန် - {time}"
MSG_NO_RATES = "ငွေလဲနှုန်းများ မသတ်မှတ်ရသေးပါ။"
MSG_ADMIN_ONLY = "ဤနေရာသည် Admin များသာ အသုံးပြုနိုင်ပါသည်။"
MSG_CHOOSE_TYPE = "ဘယ်လို ငွေလဲချင်ပါသလဲ?"
MSG_INPUT_AMOUNT = "လဲလှယ်လိုသော ပမာဏကို ရိုက်ထည့်ပေးပါ -"
MSG_INPUT_PAYMENT = "ငွေလက်ခံမည့် Kpay သို့မဟုတ် Wavepay ဖုန်းနံပါတ်ကို ရိုက်ထည့်ပေးပါ -"
MSG_SEND_PROOF = "ငွေလွှဲထားသော Screenshot Proof ကို ပို့ပေးပါ -"
MSG_WAIT_APPROVE = "လူကြီးမင်း၏ ငွေလဲလှယ်မှုအား Admin ဆီ ပို့ဆောင်လိုက်ပါပြီ။ Admin မှ စစ်ဆေးပြီးပါက အကြောင်းကြားပေးပါမည်။ ခေတ္တစောင့်ဆိုင်းပေးပါရန်။"
MSG_NEW_TX = "🔔 ငွေလဲလှယ်မှုအသစ် ရောက်ရှိလာပါသည်!\n\nUser: {user}\nအမျိုးအစား: {type}\nပမာဏ: {amount}\nလက်ခံမည့်နံပါတ်: {info}\n\nစစ်ဆေးပြီးပါက Approve သို့မဟုတ် Reject လုပ်ပေးပါ။"

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if user_id == INITIAL_ADMIN_ID:
        add_admin(user_id)
    
    keyboard = [
        [InlineKeyboardButton("📊 ငွေလဲနှုန်းကြည့်ရန်", callback_query_data="view_rates")],
        [InlineKeyboardButton("🔄 ငွေလဲလှယ်ရန်", callback_query_data="exchange")],
    ]
    
    if is_admin(user_id):
        keyboard.append([InlineKeyboardButton("⚙️ Admin Panel", callback_query_data="admin_panel")])
        
    reply_markup = InlineKeyboardMarkup(keyboard)
    if update.message:
        await update.message.reply_text(MSG_START, reply_markup=reply_markup)
    elif update.callback_query:
        await update.callback_query.message.edit_text(MSG_START, reply_markup=reply_markup)

async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user_id = query.from_user.id
    
    if query.data == "view_rates":
        b2k, k2b = get_rates()
        if b2k == 0:
            text = MSG_NO_RATES
        else:
            text = MSG_RATES.format(baht_to_kyat=b2k, kyat_to_baht=k2b, time="ယနေ့")
        keyboard = [[InlineKeyboardButton("⬅️ နောက်သို့", callback_query_data="back_to_main")]]
        await query.edit_message_text(text, reply_markup=InlineKeyboardMarkup(keyboard))

    elif query.data == "back_to_main":
        await start(update, context)

    elif query.data == "admin_panel":
        if not is_admin(user_id):
            await query.answer(MSG_ADMIN_ONLY, show_alert=True)
            return
        keyboard = [
            [InlineKeyboardButton("📈 ငွေလဲနှုန်း ပြင်ရန်", callback_query_data="set_rates")],
            [InlineKeyboardButton("🏦 ဘဏ်အကောင့် ပြင်ရန်", callback_query_data="set_banks")],
            [InlineKeyboardButton("⬅️ နောက်သို့", callback_query_data="back_to_main")],
        ]
        await query.edit_message_text("Admin Panel မှ ကြိုဆိုပါတယ်။ ဘာလုပ်ချင်ပါသလဲ?", reply_markup=InlineKeyboardMarkup(keyboard))

    elif query.data == "exchange":
        keyboard = [
            [InlineKeyboardButton("🇹🇭 Baht to Kyat 🇲🇲", callback_query_data="ex_b2k")],
            [InlineKeyboardButton("🇲🇲 Kyat to Baht 🇹🇭", callback_query_data="ex_k2b")],
            [InlineKeyboardButton("⬅️ နောက်သို့", callback_query_data="back_to_main")],
        ]
        await query.edit_message_text(MSG_CHOOSE_TYPE, reply_markup=InlineKeyboardMarkup(keyboard))

    elif query.data.startswith("ex_"):
        ex_type = "Baht to Kyat" if query.data == "ex_b2k" else "Kyat to Baht"
        context.user_data['ex_type'] = ex_type
        
        banks = get_bank_accounts()
        bank_text = "🏦 ငွေလွှဲရမည့် ဘဏ်အကောင့်များ -\n\n"
        if not banks:
            bank_text += "ဘဏ်အကောင့်များ မရှိသေးပါ။ Admin အား ဆက်သွယ်ပါ။"
            await query.edit_message_text(bank_text)
            return
            
        for b in banks:
            bank_text += f"ဘဏ်: {b[0]}\nနံပါတ်: `{b[1]}` (Copy ကူးရန် နှိပ်ပါ)\nအမည်: {b[2]}\n\n"
        
        bank_text += "ငွေလွှဲပြီးပါက 'ဆက်လုပ်မည်' ကို နှိပ်ပါ -"
        keyboard = [[InlineKeyboardButton("✅ ဆက်လုပ်မည်", callback_query_data="start_exchange_flow")]]
        await query.edit_message_text(bank_text, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode="Markdown")

# --- Exchange Conversation ---
async def start_exchange_flow(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    await query.message.reply_text(MSG_INPUT_AMOUNT)
    return EXCHANGE_AMOUNT

async def exchange_amount(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['amount'] = update.message.text
    await update.message.reply_text(MSG_INPUT_PAYMENT)
    return EXCHANGE_PAYMENT_INFO

async def exchange_payment_info(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['payment_info'] = update.message.text
    await update.message.reply_text(MSG_SEND_PROOF)
    return EXCHANGE_PROOF

async def exchange_proof(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message.photo:
        await update.message.reply_text("ကျေးဇူးပြု၍ Screenshot ပုံ ပို့ပေးပါ -")
        return EXCHANGE_PROOF
        
    photo_id = update.message.photo[-1].file_id
    user = update.effective_user
    
    tx_id = create_transaction(
        user.id, user.full_name, 
        context.user_data['amount'], 
        context.user_data['ex_type'],
        context.user_data['payment_info'],
        photo_id
    )
    
    await update.message.reply_text(MSG_WAIT_APPROVE)
    
    admin_msg = MSG_NEW_TX.format(
        user=user.full_name,
        type=context.user_data['ex_type'],
        amount=context.user_data['amount'],
        info=context.user_data['payment_info']
    )
    
    keyboard = [
        [InlineKeyboardButton("✅ Approve", callback_query_data=f"approve_{tx_id}")],
        [InlineKeyboardButton("❌ Reject", callback_query_data=f"reject_{tx_id}")]
    ]
    
    admins = get_all_admins()
    for admin_id in admins:
        try:
            await context.bot.send_photo(
                chat_id=admin_id,
                photo=photo_id,
                caption=admin_msg,
                reply_markup=InlineKeyboardMarkup(keyboard)
            )
        except Exception as e:
            logger.error(f"Error notifying admin {admin_id}: {e}")
            
    return ConversationHandler.END

# --- Admin Approval Flow ---
async def admin_tx_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    data = query.data.split("_")
    action = data[0]
    tx_id = int(data[1])
    
    if action == "approve":
        context.user_data['pending_tx_id'] = tx_id
        await query.message.reply_text("Approve လုပ်ရန်အတွက် ငွေလွှဲပြီးကြောင်း Screenshot ပုံ ပို့ပေးပါ -")
        return ADMIN_APPROVE_PROOF
    elif action == "reject":
        tx = get_transaction(tx_id)
        update_transaction_status(tx_id, "rejected")
        await context.bot.send_message(chat_id=tx[1], text="❌ လူကြီးမင်း၏ ငွေလဲလှယ်မှုအား Admin မှ ငြင်းပယ်လိုက်ပါသည်။")
        await query.edit_message_caption(caption=query.message.caption + "\n\n❌ Rejected")
        return ConversationHandler.END

async def admin_approve_proof(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message.photo:
        await update.message.reply_text("ကျေးဇူးပြု၍ Screenshot ပုံ ပို့ပေးပါ -")
        return ADMIN_APPROVE_PROOF
        
    photo_id = update.message.photo[-1].file_id
    tx_id = context.user_data.get('pending_tx_id')
    
    tx = get_transaction(tx_id)
    update_transaction_status(tx_id, "approved", photo_id)
    
    await context.bot.send_photo(
        chat_id=tx[1],
        photo=photo_id,
        caption=f"✅ လူကြီးမင်း၏ ငွေလဲလှယ်မှု အောင်မြင်ပါသည်။\n\nပမာဏ: {tx[3]} {tx[4]}\nAdmin မှ ငွေလွှဲပြီးကြောင်း အထောက်အထား ပူးတွဲပေးလိုက်ပါသည်။"
    )
    
    await update.message.reply_text("✅ User ထံသို့ အကြောင်းကြားစာ ပို့ပြီးပါပြီ။")
    return ConversationHandler.END

# --- Admin Settings Flow ---
async def set_rates_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    await query.message.reply_text("ငွေလဲနှုန်းကို အောက်ပါအတိုင်း ရိုက်ထည့်ပေးပါ (ဥပမာ - 100 2800) \n(1 Baht = ? Kyat နှင့် 100,000 Kyat = ? Baht)")
    return SET_RATES

async def set_rates_save(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        text = update.message.text.split()
        b2k = float(text[0])
        k2b = float(text[1])
        update_rates(b2k, k2b)
        await update.message.reply_text(f"✅ ငွေလဲနှုန်း ပြင်ဆင်ပြီးပါပြီ!\n1 Baht = {b2k} Kyat\n100,000 Kyat = {k2b} Baht")
    except:
        await update.message.reply_text("❌ မှားယွင်းနေပါသည်။ '100 2800' ပုံစံအတိုင်း ပြန်ရိုက်ပေးပါ။")
        return SET_RATES
    return ConversationHandler.END

async def set_banks_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    clear_bank_accounts()
    await query.message.reply_text("ဘဏ်အမည်ကို ရိုက်ထည့်ပေးပါ (ဥပမာ - Kpay) -")
    return ADD_BANK_NAME

async def add_bank_name(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['temp_bank_name'] = update.message.text
    await update.message.reply_text("ဘဏ်အကောင့်နံပါတ်ကို ရိုက်ထည့်ပေးပါ -")
    return ADD_BANK_ACC

async def add_bank_acc(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['temp_bank_acc'] = update.message.text
    await update.message.reply_text("အကောင့်ပိုင်ရှင်အမည်ကို ရိုက်ထည့်ပေးပါ -")
    return ADD_BANK_OWNER

async def add_bank_owner(update: Update, context: ContextTypes.DEFAULT_TYPE):
    add_bank_account(
        context.user_data['temp_bank_name'],
        context.user_data['temp_bank_acc'],
        update.message.text
    )
    keyboard = [
        [InlineKeyboardButton("➕ နောက်ထပ်ထည့်မည်", callback_query_data="set_banks")],
        [InlineKeyboardButton("✅ ပြီးပြီ", callback_query_data="admin_panel")]
    ]
    await update.message.reply_text("✅ ဘဏ်အကောင့် ထည့်သွင်းပြီးပါပြီ။", reply_markup=InlineKeyboardMarkup(keyboard))
    return ConversationHandler.END

async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("လုပ်ဆောင်ချက်ကို ပယ်ဖျက်လိုက်ပါပြီ။", reply_markup=ReplyKeyboardRemove())
    return ConversationHandler.END

# Simple Flask server to keep Render happy
app = Flask(__name__)

@app.route('/')
def index():
    return "Bot is running!"

def run_flask():
    port = int(os.environ.get("PORT", 10000))
    app.run(host='0.0.0.0', port=port)

def main():
    init_db()
    
    # Start Flask in a separate thread
    threading.Thread(target=run_flask, daemon=True).start()
    
    application = Application.builder().token(BOT_TOKEN).build()

    # Admin Settings
    application.add_handler(ConversationHandler(
        entry_points=[CallbackQueryHandler(set_rates_start, pattern="^set_rates$")],
        states={SET_RATES: [MessageHandler(filters.TEXT & ~filters.COMMAND, set_rates_save)]},
        fallbacks=[CommandHandler("cancel", cancel)],
        per_message=False
    ))
    
    application.add_handler(ConversationHandler(
        entry_points=[CallbackQueryHandler(set_banks_start, pattern="^set_banks$")],
        states={
            ADD_BANK_NAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, add_bank_name)],
            ADD_BANK_ACC: [MessageHandler(filters.TEXT & ~filters.COMMAND, add_bank_acc)],
            ADD_BANK_OWNER: [MessageHandler(filters.TEXT & ~filters.COMMAND, add_bank_owner)],
        },
        fallbacks=[CommandHandler("cancel", cancel)],
        per_message=False
    ))

    # User Exchange Flow
    application.add_handler(ConversationHandler(
        entry_points=[CallbackQueryHandler(start_exchange_flow, pattern="^start_exchange_flow$")],
        states={
            EXCHANGE_AMOUNT: [MessageHandler(filters.TEXT & ~filters.COMMAND, exchange_amount)],
            EXCHANGE_PAYMENT_INFO: [MessageHandler(filters.TEXT & ~filters.COMMAND, exchange_payment_info)],
            EXCHANGE_PROOF: [MessageHandler(filters.PHOTO, exchange_proof)],
        },
        fallbacks=[CommandHandler("cancel", cancel)],
        per_message=False
    ))
    
    # Admin Approval Flow
    application.add_handler(ConversationHandler(
        entry_points=[CallbackQueryHandler(admin_tx_handler, pattern="^(approve|reject)_")],
        states={ADMIN_APPROVE_PROOF: [MessageHandler(filters.PHOTO, admin_approve_proof)]},
        fallbacks=[CommandHandler("cancel", cancel)],
        per_message=False
    ))

    application.add_handler(CommandHandler("start", start))
    application.add_handler(CallbackQueryHandler(button_handler))

    application.run_polling()

if __name__ == "__main__":
    main()
