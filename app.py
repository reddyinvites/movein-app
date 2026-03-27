import streamlit as st
import gspread
from google.oauth2.service_account import Credentials
from datetime import datetime

# -----------------------
# SESSION INIT
# -----------------------
if "page" not in st.session_state:
    st.session_state.page = "home"

if "cart" not in st.session_state:
    st.session_state.cart = {}

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
# 🏠 HOME
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
# 👤 USER
# =====================
elif st.session_state.page == "user":

    st.title("👤 User Dashboard")

    # WATERMARK INPUTS
    name = st.text_input("Name", placeholder="Enter your name")
    phone = st.text_input("Phone", placeholder="+91XXXXXXXXXX")

    selected_pg = st.selectbox(
        "Select PG",
        pg_data,
        format_func=lambda x: f"{x['name']} - {x['location']}"
    )

    if "arrived" not in st.session_state:
        st.session_state.arrived = False

    if st.button("📍 I reached PG"):
        st.session_state.arrived = True

    if st.session_state.arrived:

        st.success("Welcome! Choose your essentials 👇")

        cart = st.session_state.cart

        # PRODUCTS
        basic = {"name": "Basic Kit", "price": 249, "items": "Bedsheet + Pillow"}
        utility = {"name": "Utility Kit", "price": 199, "items": "Bucket + Mug"}
        hygiene = {"name": "Hygiene Kit", "price": 129, "items": "Soap + Toothpaste + Detergent"}
        combo = {"name": "Combo Kit", "price": 449, "items": "All items included"}

        # LOGIC
        combo_selected = "combo" in cart
        others_selected = ("basic" in cart or "utility" in cart or "hygiene" in cart)

        # FIX MIXING
        if combo_selected:
            cart.pop("basic", None)
            cart.pop("utility", None)
            cart.pop("hygiene", None)

        if others_selected:
            cart.pop("combo", None)

        col1, col2 = st.columns(2)

        # LEFT SIDE
        with col1:

            st.markdown("### 🛏️ Basic Kit")
            st.write("Bedsheet + Pillow")
            st.write("₹249")
            if st.button("Add Basic", disabled=combo_selected):
                cart["basic"] = basic

            st.markdown("### 🪣 Utility Kit")
            st.write("Bucket + Mug")
            st.write("₹199")
            if st.button("Add Utility", disabled=combo_selected):
                cart["utility"] = utility

            st.markdown("### 🧼 Hygiene Kit")
            st.write("Soap + Toothpaste + Detergent")
            st.write("₹129")
            if st.button("Add Hygiene", disabled=combo_selected):
                cart["hygiene"] = hygiene

        # RIGHT SIDE
        with col2:

            st.markdown("### 🎁 Combo Kit")
            st.write("All items included")
            st.write("₹449")
            if st.button("Add Combo", disabled=others_selected):
                cart.clear()
                cart["combo"] = combo

        st.divider()

        # CART
        if cart:
            total = sum(item["price"] for item in cart.values())

            st.subheader("🛒 Selected Items")
            for item in cart.values():
                st.write(f"{item['name']} - ₹{item['price']}")

            st.write(f"### Total: ₹{total}")

            if st.button("✅ Place Order"):

                items_text = ", ".join([i["name"] for i in cart.values()])

                order_sheet.append_row([
                    name,
                    phone,
                    selected_pg["name"],
                    items_text,
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

            st.success("🧾 Order placed!")

            st.markdown(f"[💰 Pay Now]({upi})")

            st.warning("⚠️ After payment, upload screenshot")

            file = st.file_uploader("📸 Upload Screenshot", type=["png","jpg","jpeg"])

            if file:
                st.image(file)
                st.success("✅ Uploaded!")

                st.info("""
⏳ We will verify your payment.

We will confirm on WhatsApp shortly.
""")

                # RESET + LOGOUT
                st.session_state.clear()
                st.session_state.page = "home"
                st.rerun()

    if st.button("🚪 Logout"):
        st.session_state.clear()
        st.session_state.page = "home"
        st.rerun()

# =====================
# 👨‍💼 ADMIN
# =====================
elif st.session_state.page == "admin":

    st.title("👨‍💼 Admin Dashboard")

    password = st.text_input("Password", type="password")

    if password != "1234":
        st.warning("Enter correct password")
        st.stop()

    orders = order_sheet.get_all_records()

    for i, o in enumerate(orders):

        st.write(f"👤 {o['name']} | 📞 {o['phone']}")
        st.write(f"🛒 {o['items']}")
        st.write(f"💰 ₹{o['total']}")

        status = o["status"]

        if status == "Pending":
            st.warning("Pending")
        elif status == "Paid":
            st.success("Paid")

        if st.button("✅ Approve Payment", key=f"a{i}"):
            order_sheet.update_cell(i+2, 6, "Paid")
            st.success("Updated to PAID")

        st.divider()

    if st.button("🚪 Logout"):
        st.session_state.clear()
        st.session_state.page = "home"
        st.rerun()