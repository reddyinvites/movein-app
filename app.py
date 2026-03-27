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

    name = st.text_input("Name", placeholder="Enter your name")
    phone = st.text_input("Phone", placeholder="+91XXXXXXXXXX")

    selected_pg = st.selectbox(
        "Select PG",
        pg_data,
        format_func=lambda x: f"{x['name']} - {x['location']}"
    )

    if st.button("📍 I reached PG"):
        st.session_state.arrived = True

    if st.session_state.get("arrived"):

        st.success("Choose your essentials 👇")

        cart = st.session_state.cart

        # PRODUCTS
        products = {
            "basic": {"name": "Basic Kit", "price": 249, "items": "Bedsheet + Pillow"},
            "utility": {"name": "Utility Kit", "price": 199, "items": "Bucket + Mug"},
            "hygiene": {"name": "Hygiene Kit", "price": 129, "items": "Soap + Toothpaste"},
            "combo": {"name": "Combo Kit", "price": 499, "items": "All items included"}  # UPDATED
        }

        combo_selected = "combo" in cart
        others_selected = any(k in cart for k in ["basic","utility","hygiene"])

        # -----------------------
        # NORMAL ITEMS
        # -----------------------
        for key in ["basic","utility","hygiene"]:

            p = products[key]

            st.markdown(f"### {p['name']}")
            st.write(p["items"])
            st.write(f"₹{p['price']}")

            if combo_selected:
                st.button(f"Add {p['name']}", disabled=True, key=f"d_{key}")

            else:
                if key in cart:
                    if st.button(f"❌ Remove {p['name']}", key=f"r_{key}"):
                        del cart[key]
                else:
                    if st.button(f"Add {p['name']}", key=f"a_{key}"):
                        cart[key] = p

        # -----------------------
        # COMBO
        # -----------------------
        p = products["combo"]

        st.markdown(f"### 🎁 {p['name']}")
        st.write(p["items"])
        st.write(f"₹{p['price']}")

        if "combo" in cart:

            if st.button("❌ Remove Combo"):
                del cart["combo"]

        else:
            if others_selected:
                st.button("Add Combo", disabled=True)
            else:
                if st.button("Add Combo"):
                    cart.clear()
                    cart["combo"] = p

        st.divider()

        # -----------------------
        # CART
        # -----------------------
        if cart:

            total = sum(i["price"] for i in cart.values())

            st.subheader("🛒 Selected Items")

            for i in cart.values():
                st.write(f"{i['name']} - ₹{i['price']}")

            st.write(f"### Total: ₹{total}")

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

        # -----------------------
        # PAYMENT
        # -----------------------
        if st.session_state.get("order_done"):

            total = st.session_state.total
            upi = f"upi://pay?pa=reddyinvites@okicici&pn=MoveIn&am={total}"

            st.success("Order placed!")

            st.markdown(f"[💰 Pay Now]({upi})")

            file = st.file_uploader("Upload Payment Screenshot")

            if file:
                st.image(file)
                st.success("Uploaded!")

                st.info("⏳ We will confirm on WhatsApp in few seconds...")

                # RESET
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
        st.stop()

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

            msg = f"Hello {o['name']}, your payment is confirmed!"
            wa = f"https://wa.me/{o['phone']}?text={msg.replace(' ','%20')}"

            st.success("Marked Paid")
            st.markdown(f"[📲 Send WhatsApp]({wa})")

        st.divider()