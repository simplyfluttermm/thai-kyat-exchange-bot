# Thai-Myanmar Currency Exchange Telegram Bot

ဤ Bot သည် ထိုင်းဘတ် နှင့် မြန်မာကျပ် ငွေလဲလှယ်နှုန်းများကို နေ့စဉ်တင်ပေးနိုင်ပြီး User များမှ ငွေလဲလှယ်ရန် တောင်းဆိုမှုများကို Admin မှ စစ်ဆေးအတည်ပြုပေးနိုင်သော Bot ဖြစ်ပါသည်။

## Features
- Admin မှ နေ့စဉ် ငွေလဲနှုန်းများ သတ်မှတ်နိုင်ခြင်း။
- Admin မှ ငွေလွှဲလက်ခံမည့် ဘဏ်အကောင့်များ ထည့်သွင်းနိုင်ခြင်း။
- User မှ ငွေလဲလှယ်လိုသော ပမာဏနှင့် Screenshot Proof တင်နိုင်ခြင်း။
- Admin မှ စစ်ဆေးပြီး Approve လုပ်ပါက User ထံသို့ Admin ၏ ငွေလွှဲ Screenshot ပြန်လည်ပေးပို့ပေးခြင်း။

## Setup Instructions

### 1. Bot Token ရယူခြင်း
- Telegram တွင် [@BotFather](https://t.me/botfather) ထံသွားပါ။
- `/newbot` ကိုနှိပ်ပြီး Bot အသစ်ဆောက်ပါ။
- ရရှိလာသော **API Token** ကို သိမ်းထားပါ။

### 2. Admin ID ရယူခြင်း
- Telegram တွင် [@userinfobot](https://t.me/userinfobot) ထံသွားပါ။
- မိမိ၏ **User ID** (နံပါတ်စဉ်) ကို သိမ်းထားပါ။

### 3. Deployment (Render.com တွင် တင်နည်း)
1. GitHub တွင် Repository အသစ်တစ်ခုဆောက်ပြီး ဤ Code များကို တင်ပါ။
2. [Render.com](https://render.com) တွင် အကောင့်ဖွင့်ပါ။
3. **New +** -> **Background Worker** ကိုရွေးပါ။
4. မိမိ၏ GitHub Repo ကို Connect လုပ်ပါ။
5. **Environment Variables** တွင် အောက်ပါတို့ထည့်ပါ -
   - `BOT_TOKEN`: သင်၏ Bot Token
   - `ADMIN_ID`: သင်၏ User ID
6. **Build Command** တွင် `pip install -r requirements.txt` ဟုရေးပါ။
7. **Start Command** တွင် `python bot.py` ဟုရေးပါ။
8. Deploy လုပ်ပါ။

## Local Run
```bash
pip install -r requirements.txt
export BOT_TOKEN="your_token"
export ADMIN_ID="your_id"
python bot.py
```

## Developer
Created by Manus AI.
