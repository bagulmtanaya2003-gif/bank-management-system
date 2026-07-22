import streamlit as st
import mysql.connector
import pandas as pd

# function to connect with mysql
def get_connection():
    return mysql.connector.connect(
        host="localhost",
        user="root",
        password="Tanaya@2003",
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

# function to create new account
def create_account(name, password, balance):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("INSERT INTO accounts (name,password,balance) VALUES (%s,%s,%s)", (name, password, balance))
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

# streamlit ui start
st.set_page_config(page_title="Banking Management System")
st.title("🏦 Banking Management System")

# session state so the last created account number stays visible on screen
if "last_created_acc" not in st.session_state:
    st.session_state.last_created_acc = None

menu = ["Create Account", "Deposit", "Withdraw", "Check Balance", "My Statement", "All Users", "Close Account"]
choice = st.sidebar.selectbox("Select Operation", menu)

# create account section
if choice == "Create Account":
    st.subheader("Open New Account")
    name = st.text_input("Enter Name")
    password = st.text_input("Set Password", type="password")
    balance = st.number_input("Initial Deposit", min_value=0.0)
    if st.button("Create Account"):
        acc_no = create_account(name, password, balance)
        st.session_state.last_created_acc = acc_no
        st.success("Account Created Successfully!")
    if st.session_state.last_created_acc:
        st.info(f"Your Account Number is: **{st.session_state.last_created_acc}**  (please save this number)")

# deposit section
elif choice == "Deposit":
    st.subheader("Deposit Money")
    acc_no = st.number_input("Account Number", step=1)
    password = st.text_input("Password", type="password")
    amount = st.number_input("Amount to Deposit", min_value=0.0)
    if st.button("Deposit"):
        account = get_account(acc_no, password)
        if account:
            deposit_money(acc_no, amount)
            st.success(f"Rs.{amount} Deposited! New Balance: Rs.{get_balance(acc_no)}")
        else:
            st.error("Invalid Account Number or Password")

# withdraw section
elif choice == "Withdraw":
    st.subheader("Withdraw Money")
    acc_no = st.number_input("Account Number", step=1)
    password = st.text_input("Password", type="password")
    amount = st.number_input("Amount to Withdraw", min_value=0.0)
    if st.button("Withdraw"):
        account = get_account(acc_no, password)
        if account:
            success = withdraw_money(acc_no, amount)
            if success:
                st.success(f"Rs.{amount} Withdrawn! New Balance: Rs.{get_balance(acc_no)}")
            else:
                st.error("Insufficient Balance")
        else:
            st.error("Invalid Account Number or Password")

# balance check section
elif choice == "Check Balance":
    st.subheader("Check Balance")
    acc_no = st.number_input("Account Number", step=1)
    password = st.text_input("Password", type="password")
    if st.button("Check Balance"):
        account = get_account(acc_no, password)
        if account:
            st.info(f"Account Holder: **{account[1]}**  |  Balance: **Rs.{get_balance(acc_no)}**")
        else:
            st.error("Invalid Account Number or Password")

# section to show one user full details and history
elif choice == "My Statement":
    st.subheader("My Account Statement")
    acc_no = st.number_input("Account Number", step=1)
    password = st.text_input("Password", type="password")
    if st.button("Show Statement"):
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

# section to show all users and the full bank history together
elif choice == "All Users":
    st.subheader("All Bank Users")
    users = get_all_users()
    st.dataframe(users, use_container_width=True)
    st.subheader("Full Bank Transaction History")
    all_txns = get_all_transactions()
    st.dataframe(all_txns, use_container_width=True)

# close account section
elif choice == "Close Account":
    st.subheader("Close Account")
    acc_no = st.number_input("Account Number", step=1)
    password = st.text_input("Password", type="password")
    if st.button("Close Account"):
        account = get_account(acc_no, password)
        if account:
            delete_account(acc_no)
            st.success("Account Closed Successfully!")
        else:
            st.error("Invalid Account Number or Password")