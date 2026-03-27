import streamlit as st
import gspread
from google.oauth2.service_account import Credentials
from datetime import datetime

# -----------------------
# APP MODE SWITCH
# -----------------------
mode = st.sidebar.selectbox("Select Mode", ["User App", "Admin Dashboard"])

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
# 👤 USER APP
# =====================
if mode == "User App":

    st.title("🏠 Move-in Assistant")

    name = st.text_input("👤 Name")
    phone = st.text_input("📞 Phone")

    selected_pg = st.selectbox(
        "🏢 Select PG",
        pg_data,
        format_func=lambda x: f"{x['name']} - {x['location']}"
    )

    if st.button("📍 I reached PG"):
        st.success("Welcome!")

    kits = [
        {"name": "Basic Kit", "price": 249},
        {"name": "Utility Kit", "price": 199},
        {"name": "Hygiene Kit", "price": 129}
    ]

    cart = []

    for kit in kits:
        if st.button(f"Add {kit['name']}"):
            cart.append(kit)

    if cart:
        total = sum(k["price"] for k in cart)
        st.write(f"Total: ₹{total}")

        if st.button("Place Order"):

            items = ", ".join([k["name"] for k in cart])

            order_sheet.append_row([
                name,
                phone,
                selected_pg["name"],
                items,
                total,
                "Pending",
                str(datetime.now())
            ])

            upi = f"upi://pay?pa=reddyinvites@okicici&pn=MoveIn&am={total}"

            st.markdown(f"[💰 Pay Now]({upi})")

            file = st.file_uploader("📸 Upload Screenshot")

            if file:
                st.success("✅ Payment screenshot uploaded!")
                
                st.info("""
⏳ We will verify your payment.

Please stay here...
We will confirm shortly.
""")

# =====================
# 👨‍💼 ADMIN DASHBOARD
# =====================
elif mode == "Admin Dashboard":

    st.title("👨‍💼 Admin Dashboard")

    password = st.text_input("Enter Password", type="password")

    if password != "1234":
        st.warning("Enter correct password")
        st.stop()

    orders = order_sheet.get_all_records()

    for i, o in enumerate(orders):

        st.write(f"👤 {o['name']}")
        st.write(f"📞 {o['phone']}")
        st.write(f"🛒 {o['items']}")
        st.write(f"💰 ₹{o['total']}")
        st.write(f"📌 {o['status']}")

        col1, col2 = st.columns(2)

        if col1.button("Approve", key=f"a{i}"):
            order_sheet.update_cell(i+2, 6, "Approved")

        if col2.button("Reject", key=f"r{i}"):
            order_sheet.update_cell(i+2, 6, "Rejected")

        # WhatsApp only in admin
        msg = f"Hello {o['name']}, your order is {o['status']}"
        wa = f"https://wa.me/{o['phone']}?text={msg.replace(' ','%20')}"

        st.markdown(f"[📲 Message User]({wa})")

        st.divider()