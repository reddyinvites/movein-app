import streamlit as st
import gspread
from google.oauth2.service_account import Credentials
from datetime import datetime

# -----------------------
# SESSION
# -----------------------
if "page" not in st.session_state:
    st.session_state.page = "home"

# -----------------------
# GOOGLE SHEETS
# -----------------------
scope = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive"
]

creds = Credentials.from_service_account_info(
    st.secrets["gcp_service_account"],
    scopes=scope
)

client = gspread.authorize(creds)
sheet = client.open_by_key("1y60dTYBKgkOi7J37jtGK4BkkmUoZF8yD4P5J3xA5q6Q")

pg_sheet = sheet.sheet1
order_sheet = sheet.worksheet("orders")

pg_data = pg_sheet.get_all_records()

# =====================
# 🏠 HOME PAGE
# =====================
if st.session_state.page == "home":

    st.title("🏠 Move-in Assistant")

    col1, col2 = st.columns(2)

    if col1.button("👤 User"):
        st.session_state.page = "user"
        st.rerun()

    if col2.button("👨‍💼 Admin"):
        st.session_state.page = "admin"
        st.rerun()

# =====================
# 👤 USER PAGE
# =====================
elif st.session_state.page == "user":

    st.title("👤 User Dashboard")

    # DEFAULT VALUES
    name = st.text_input("Name", value="Guest")
    phone = st.text_input("Phone", value="+919618557269")

    selected_pg = st.selectbox(
        "Select PG",
        pg_data,
        format_func=lambda x: f"{x['name']} - {x['location']}"
    )

    # SESSION
    if "cart" not in st.session_state:
        st.session_state.cart = {}

    if "arrived" not in st.session_state:
        st.session_state.arrived = False

    if st.button("📍 I reached PG"):
        st.session_state.arrived = True

    if st.session_state.arrived:

        st.success("Welcome! Choose your essentials 👇")

        cart = st.session_state.cart

        basic = {"name": "Basic Kit", "price": 249}
        utility = {"name": "Utility Kit", "price": 199}
        hygiene = {"name": "Hygiene Kit", "price": 129}
        combo = {"name": "Combo Kit", "price": 449}

        combo_selected = "combo" in cart
        others_selected = any(k in cart for k in ["basic","utility","hygiene"])

        col1, col2 = st.columns(2)

        with col1:
            if st.button("Basic Kit", disabled=combo_selected):
                cart["basic"] = basic

            if st.button("Utility Kit", disabled=combo_selected):
                cart["utility"] = utility

            if st.button("Hygiene Kit", disabled=combo_selected):
                cart["hygiene"] = hygiene

        with col2:
            if st.button("Combo Kit", disabled=others_selected):
                cart.clear()
                cart["combo"] = combo

        st.divider()

        if cart:
            total = sum(i["price"] for i in cart.values())

            st.write(f"Total: ₹{total}")

            if st.button("Place Order"):

                items = ", ".join([i["name"] for i in cart.values()])

                order_sheet.append_row([
                    name,
                    phone,
                    selected_pg["name"],
                    items,
                    total,
                    "Pending",
                    str(datetime.now())
                ])

                st.session_state.order_done = True
                st.session_state.total = total

    # PAYMENT
    if st.session_state.get("order_done"):

        total = st.session_state.total

        upi = f"upi://pay?pa=reddyinvites@okicici&pn=MoveIn&am={total}"

        st.success("Order placed!")

        st.markdown(f"[💰 Pay Now]({upi})")

        file = st.file_uploader("Upload Screenshot")

        if file:
            st.success("✅ Uploaded!")

            st.info("""
⏳ Payment received.

We will confirm on WhatsApp shortly.
Please wait...
""")

            # RESET EVERYTHING (AUTO LOGOUT)
            st.session_state.clear()
            st.session_state.page = "home"
            st.rerun()

    # LOGOUT BUTTON
    if st.button("🚪 Logout"):
        st.session_state.clear()
        st.session_state.page = "home"
        st.rerun()

# =====================
# 👨‍💼 ADMIN PAGE
# =====================
elif st.session_state.page == "admin":

    st.title("👨‍💼 Admin Login")

    password = st.text_input("Password", type="password")

    if password == "1234":

        st.success("Login Success")

        orders = order_sheet.get_all_records()

        for i, o in enumerate(orders):

            st.write(f"{o['name']} | {o['phone']}")
            st.write(f"{o['items']} | ₹{o['total']}")

            if o["status"] == "Pending":
                st.warning("Pending")
            elif o["status"] == "Paid":
                st.success("Paid")

            if st.button("Approve", key=f"a{i}"):
                order_sheet.update_cell(i+2, 6, "Paid")
                st.success("Marked Paid")

            st.divider()

    else:
        st.warning("Enter correct password")

    # LOGOUT
    if st.button("🚪 Logout"):
        st.session_state.clear()
        st.session_state.page = "home"
        st.rerun()