import streamlit as st
import gspread
from google.oauth2.service_account import Credentials
from datetime import datetime

# -----------------------
# MODE SELECT
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

    # SESSION
    if "arrived" not in st.session_state:
        st.session_state.arrived = False

    if "cart" not in st.session_state:
        st.session_state.cart = {}

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
            if st.button("🛏️ Basic Kit - ₹249", disabled=combo_selected):
                cart["basic"] = basic

            if st.button("🪣 Utility Kit - ₹199", disabled=combo_selected):
                cart["utility"] = utility

            if st.button("🧼 Hygiene Kit - ₹129", disabled=combo_selected):
                cart["hygiene"] = hygiene

        with col2:
            if st.button("🎁 Combo Kit - ₹449", disabled=others_selected):
                cart.clear()
                cart["combo"] = combo

        st.divider()

        if cart:
            total = sum(i["price"] for i in cart.values())

            st.subheader("🛒 Selected Items")
            for i in cart.values():
                st.write(f"{i['name']} - ₹{i['price']}")

            st.write(f"### Total: ₹{total}")

            if st.button("✅ Place Order"):

                items_text = ", ".join([i["name"] for i in cart.values()])

                order_sheet.append_row([
                    name,
                    phone,
                    selected_pg["name"],
                    items_text,
                    total,
                    "Pending",   # ✅ STATUS
                    str(datetime.now())
                ])

                st.session_state.current_order = {
                    "items": items_text,
                    "total": total
                }

        # PAYMENT FLOW
        if "current_order" in st.session_state:

            total = st.session_state.current_order["total"]

            upi = f"upi://pay?pa=reddyinvites@okicici&pn=MoveIn&am={total}"

            st.success("🧾 Order placed!")

            st.markdown(f"[💰 Pay Now]({upi})")

            st.warning("⚠️ After payment, upload screenshot")

            file = st.file_uploader("📸 Upload Screenshot", type=["png","jpg","jpeg"])

            if file:
                st.image(file)
                st.success("✅ Uploaded!")

                st.info("""
⏳ We will verify your payment.

Please stay here...
We will confirm shortly.
""")

                # RESET
                st.session_state.cart = {}
                del st.session_state.current_order


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

        # STATUS COLOR
        status = o["status"]

        if status == "Paid":
            st.success(f"📌 {status}")
        elif status == "Pending":
            st.warning(f"📌 {status}")
        else:
            st.error(f"📌 {status}")

        col1, col2 = st.columns(2)

        # APPROVE → PAID
        if col1.button("✅ Approve Payment", key=f"a{i}"):
            order_sheet.update_cell(i+2, 6, "Paid")
            st.success("Updated to PAID")

        # REJECT
        if col2.button("❌ Reject", key=f"r{i}"):
            order_sheet.update_cell(i+2, 6, "Rejected")
            st.error("Rejected")

        st.divider()