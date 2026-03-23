import sqlite3

def init_db():
    conn = sqlite3.connect('exchange.db')
    cursor = conn.cursor()
    
    # Table for exchange rates
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS rates (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            baht_to_kyat REAL,
            kyat_to_baht REAL,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # Table for admin bank accounts
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS bank_accounts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            bank_name TEXT,
            account_number TEXT,
            account_name TEXT
        )
    ''')
    
    # Table for transactions
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS transactions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            user_name TEXT,
            amount REAL,
            exchange_type TEXT, -- 'baht_to_kyat' or 'kyat_to_baht'
            user_payment_info TEXT, -- Kpay/Wavepay number
            user_proof_file_id TEXT,
            admin_proof_file_id TEXT,
            status TEXT DEFAULT 'pending', -- 'pending', 'approved', 'rejected'
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # Table for admins
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS admins (
            user_id INTEGER PRIMARY KEY
        )
    ''')
    
    conn.commit()
    conn.close()

def get_rates():
    conn = sqlite3.connect('exchange.db')
    cursor = conn.cursor()
    cursor.execute('SELECT baht_to_kyat, kyat_to_baht FROM rates ORDER BY id DESC LIMIT 1')
    rate = cursor.fetchone()
    conn.close()
    return rate if rate else (0.0, 0.0)

def update_rates(baht_to_kyat, kyat_to_baht):
    conn = sqlite3.connect('exchange.db')
    cursor = conn.cursor()
    cursor.execute('INSERT INTO rates (baht_to_kyat, kyat_to_baht) VALUES (?, ?)', (baht_to_kyat, kyat_to_baht))
    conn.commit()
    conn.close()

def get_bank_accounts():
    conn = sqlite3.connect('exchange.db')
    cursor = conn.cursor()
    cursor.execute('SELECT bank_name, account_number, account_name FROM bank_accounts')
    accounts = cursor.fetchall()
    conn.close()
    return accounts

def add_bank_account(bank_name, account_number, account_name):
    conn = sqlite3.connect('exchange.db')
    cursor = conn.cursor()
    cursor.execute('INSERT INTO bank_accounts (bank_name, account_number, account_name) VALUES (?, ?, ?)', 
                   (bank_name, account_number, account_name))
    conn.commit()
    conn.close()

def clear_bank_accounts():
    conn = sqlite3.connect('exchange.db')
    cursor = conn.cursor()
    cursor.execute('DELETE FROM bank_accounts')
    conn.commit()
    conn.close()

def create_transaction(user_id, user_name, amount, exchange_type, user_payment_info, user_proof_file_id):
    conn = sqlite3.connect('exchange.db')
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO transactions (user_id, user_name, amount, exchange_type, user_payment_info, user_proof_file_id)
        VALUES (?, ?, ?, ?, ?, ?)
    ''', (user_id, user_name, amount, exchange_type, user_payment_info, user_proof_file_id))
    transaction_id = cursor.lastrowid
    conn.commit()
    conn.close()
    return transaction_id

def get_transaction(transaction_id):
    conn = sqlite3.connect('exchange.db')
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM transactions WHERE id = ?', (transaction_id,))
    transaction = cursor.fetchone()
    conn.close()
    return transaction

def update_transaction_status(transaction_id, status, admin_proof_file_id=None):
    conn = sqlite3.connect('exchange.db')
    cursor = conn.cursor()
    if admin_proof_file_id:
        cursor.execute('UPDATE transactions SET status = ?, admin_proof_file_id = ? WHERE id = ?', 
                       (status, admin_proof_file_id, transaction_id))
    else:
        cursor.execute('UPDATE transactions SET status = ? WHERE id = ?', (status, transaction_id))
    conn.commit()
    conn.close()

def is_admin(user_id):
    conn = sqlite3.connect('exchange.db')
    cursor = conn.cursor()
    cursor.execute('SELECT 1 FROM admins WHERE user_id = ?', (user_id,))
    admin = cursor.fetchone()
    conn.close()
    return admin is not None

def add_admin(user_id):
    conn = sqlite3.connect('exchange.db')
    cursor = conn.cursor()
    cursor.execute('INSERT OR IGNORE INTO admins (user_id) VALUES (?)', (user_id,))
    conn.commit()
    conn.close()

def get_all_admins():
    conn = sqlite3.connect('exchange.db')
    cursor = conn.cursor()
    cursor.execute('SELECT user_id FROM admins')
    admins = [row[0] for row in cursor.fetchall()]
    conn.close()
    return admins
