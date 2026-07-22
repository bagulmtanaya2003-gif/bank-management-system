import streamlit as st
import mysql.connector
import pandas as pd

# function to connect with mysql
def get_connection():
    return mysql.connector.connect(
        host="localhost",
        user="root",
        password="YOUR_MYSQL_PASSWORD",
        database="bankdb"
    )

# function to log every transaction
def log_transaction(acc_no, txn_type, amount):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("INSERT INTO transactions (acc_no,txn_type,amount) VALUES (%s,%s,%s)", (acc_no, txn_type, amount))
    conn.commit()
    cursor.close()
    conn.close()

# function to create new account with a security answer for password recovery
def create_account(name, password, balance, security_answer):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("INSERT INTO accounts (name,password,balance,security_answer) VALUES (%s,%s,%s,%s)", (name, password, balance, security_answer))
    conn.commit()
    acc_no = cursor.lastrowid
    cursor.close()
    conn.close()
    log_transaction(acc_no, "OPENING", balance)
    return acc_no

# function to verify account
def get_account(acc_no, password):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM accounts WHERE acc_no=%s AND password=%s", (acc_no, password))
    result = cursor.fetchone()
    cursor.close()
    conn.close()
    return result

# function to verify account using security answer instead of password
def verify_security_answer(acc_no, security_answer):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM accounts WHERE acc_no=%s AND security_answer=%s", (acc_no, security_answer))
    result = cursor.fetchone()
    cursor.close()
    conn.close()
    return result

# function to reset password after security answer is verified
def reset_password(acc_no, new_password):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("UPDATE accounts SET password=%s WHERE acc_no=%s", (new_password, acc_no))
    conn.commit()
    cursor.close()
    conn.close()

# function to deposit money
def deposit_money(acc_no, amount):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("UPDATE accounts SET balance = balance + %s WHERE acc_no=%s", (amount, acc_no))
    conn.commit()
    cursor.close()
    conn.close()
    log_transaction(acc_no, "DEPOSIT", amount)

# function to withdraw money
def withdraw_money(acc_no, amount):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT balance FROM accounts WHERE acc_no=%s", (acc_no,))
    balance = cursor.fetchone()[0]
    if balance >= amount:
        cursor.execute("UPDATE accounts SET balance = balance - %s WHERE acc_no=%s", (amount, acc_no))
        conn.commit()
        cursor.close()
        conn.close()
        log_transaction(acc_no, "WITHDRAW", amount)
        return True
    cursor.close()
    conn.close()
    return False

# function to check balance
def get_balance(acc_no):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT balance FROM accounts WHERE acc_no=%s", (acc_no,))
    balance = cursor.fetchone()[0]
    cursor.close()
    conn.close()
    return balance

# function to fetch full transaction history of one account
def get_history(acc_no):
    conn = get_connection()
    df = pd.read_sql("SELECT txn_type, amount, txn_date FROM transactions WHERE acc_no=%s ORDER BY txn_date DESC" % acc_no, conn)
    conn.close()
    return df

# function to fetch list of all users
def get_all_users():
    conn = get_connection()
    df = pd.read_sql("SELECT acc_no, name, balance FROM accounts", conn)
    conn.close()
    return df

# function to fetch full bank history of every customer joined with their name
def get_all_transactions():
    conn = get_connection()
    query = "SELECT t.acc_no, a.name, t.txn_type, t.amount, t.txn_date FROM transactions t JOIN accounts a ON t.acc_no=a.acc_no ORDER BY t.txn_date DESC"
    df = pd.read_sql(query, conn)
    conn.close()
    return df

# function to close account
def delete_account(acc_no):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM transactions WHERE acc_no=%s", (acc_no,))
    cursor.execute("DELETE FROM accounts WHERE acc_no=%s", (acc_no,))
    conn.commit()
    cursor.close()
    conn.close()

# streamlit page setup
st.set_page_config(page_title="Banking Management System", layout="wide")
st.title("🏦 Banking Management System")

# session state so the last created account number stays visible on screen
if "last_created_acc" not in st.session_state:
    st.session_state.last_created_acc = None

# creating a separate tab for every operation
tab1, tab2, tab3, tab4, tab5, tab6, tab7, tab8 = st.tabs(
    ["Create Account", "Deposit", "Withdraw", "Check Balance", "My Statement", "All Users", "Close Account", "Forgot Password"]
)

# create account tab, now also asks a security answer for password recovery
with tab1:
    st.subheader("Open New Account")
    name = st.text_input("Enter Customer Name", key="ca_name")
    password = st.text_input("Set Password", type="password", key="ca_pass")
    security_question = st.selectbox("Choose a Security Question", ["What is your pet's name?", "What is your mother's maiden name?", "What was the name of your first school?", "Which city were you born in?"], key="ca_secq")
    security_answer = st.text_input("Answer to the Security Question", key="ca_sec")
    balance = st.number_input("Initial Deposit", min_value=0.0, key="ca_bal")
    if st.button("Create Account", key="ca_btn"):
        acc_no = create_account(name, password, balance, security_answer)
        st.session_state.last_created_acc = acc_no
        st.success("Account Created Successfully!")
    if st.session_state.last_created_acc:
        st.info(f"Your Account Number is: **{st.session_state.last_created_acc}**  (please save this number)")

# deposit tab
with tab2:
    st.subheader("Deposit Money")
    acc_no = st.number_input("Account Number", step=1, key="dep_acc")
    password = st.text_input("Password", type="password", key="dep_pass")
    amount = st.number_input("Amount to Deposit", min_value=0.0, key="dep_amt")
    if st.button("Deposit", key="dep_btn"):
        account = get_account(acc_no, password)
        if account:
            deposit_money(acc_no, amount)
            st.success(f"Rs.{amount} Deposited! New Balance: Rs.{get_balance(acc_no)}")
        else:
            st.error("Invalid Account Number or Password")

# withdraw tab
with tab3:
    st.subheader("Withdraw Money")
    acc_no = st.number_input("Account Number", step=1, key="wd_acc")
    password = st.text_input("Password", type="password", key="wd_pass")
    amount = st.number_input("Amount to Withdraw", min_value=0.0, key="wd_amt")
    if st.button("Withdraw", key="wd_btn"):
        account = get_account(acc_no, password)
        if account:
            success = withdraw_money(acc_no, amount)
            if success:
                st.success(f"Rs.{amount} Withdrawn! New Balance: Rs.{get_balance(acc_no)}")
            else:
                st.error("Insufficient Balance")
        else:
            st.error("Invalid Account Number or Password")

# check balance tab
with tab4:
    st.subheader("Check Balance")
    acc_no = st.number_input("Account Number", step=1, key="bal_acc")
    password = st.text_input("Password", type="password", key="bal_pass")
    if st.button("Check Balance", key="bal_btn"):
        account = get_account(acc_no, password)
        if account:
            st.info(f"Account Holder: **{account[1]}**  |  Balance: **Rs.{get_balance(acc_no)}**")
        else:
            st.error("Invalid Account Number or Password")

# my statement tab, shows one user full details and history
with tab5:
    st.subheader("My Account Statement")
    acc_no = st.number_input("Account Number", step=1, key="st_acc")
    password = st.text_input("Password", type="password", key="st_pass")
    if st.button("Show Statement", key="st_btn"):
        account = get_account(acc_no, password)
        if account:
            st.write(f"**Account Number:** {account[0]}")
            st.write(f"**Name:** {account[1]}")
            st.write(f"**Current Balance:** Rs.{account[3]}")
            st.write("**Transaction History:**")
            history = get_history(acc_no)
            st.dataframe(history, use_container_width=True)
        else:
            st.error("Invalid Account Number or Password")

# all users tab, shows every user and the full bank ledger
with tab6:
    st.subheader("All Bank Users")
    users = get_all_users()
    st.dataframe(users, use_container_width=True)
    st.subheader("Full Bank Transaction History")
    all_txns = get_all_transactions()
    st.dataframe(all_txns, use_container_width=True)

# close account tab
with tab7:
    st.subheader("Close Account")
    acc_no = st.number_input("Account Number", step=1, key="cl_acc")
    password = st.text_input("Password", type="password", key="cl_pass")
    if st.button("Close Account", key="cl_btn"):
        account = get_account(acc_no, password)
        if account:
            delete_account(acc_no)
            st.success("Account Closed Successfully!")
        else:
            st.error("Invalid Account Number or Password")

# forgot password tab, verifies security answer then lets user set a new password
with tab8:
    st.subheader("Forgot Password")
    acc_no = st.number_input("Account Number", step=1, key="fp_acc")
    security_question = st.selectbox("Your Security Question", ["What is your pet's name?", "What is your mother's maiden name?", "What was the name of your first school?", "Which city were you born in?"], key="fp_secq")
    security_answer = st.text_input("Enter your Answer", key="fp_sec")
    new_password = st.text_input("Set New Password", type="password", key="fp_newpass")
    if st.button("Reset Password", key="fp_btn"):
        account = verify_security_answer(acc_no, security_answer)
        if account:
            reset_password(acc_no, new_password)
            st.success("Password Reset Successfully! You can now login with your new password.")
        else:
            st.error("Invalid Account Number or Security Answer")