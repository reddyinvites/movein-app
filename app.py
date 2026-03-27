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

if "arrived" not in st.session_state:
    st.session_state.arrived = False

# -----------------------
# GOOGLE SHEETS
# -----------------------
scope = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive"
]

try:
    creds = Credentials.from_service_account_info(
        st.secrets["gcp_service_account"],
        scopes=scope
    )

    client = gspread.authorize(creds)

    sheet = client.open_by_key("1y60dTYBKgkOi7J37jtGK4BkkmUoZF8yD4P5J3xA5q6Q")

    pg_sheet = sheet.sheet1
    order_sheet = sheet.worksheet("orders")

    pg_data = pg_sheet.get_all_records()

except:
    st.error("❌ Google Sheets connection failed")
    st.stop()

# -----------------------
# HOME
# -----------------------
if st.session_state.page == "home":

    st.title("🏠 Move-in Assistant")

    col1, col2 = st.columns(2)

    if col1.button("👤 User"):
        st.session_state.page = "user"
        st.rerun()

    if col2.button("👨‍💼 Admin"):
        st.session_state.page = "admin"
        st.rerun()

# -----------------------
# USER
# -----------------------
elif st.session_state.page == "user":

    st.title("👤 User Dashboard")

    name = st.text_input("Name")
    phone = st.text_input("Phone")

    if not pg_data:
        st.warning("No PG data")
        st.stop()

    selected_pg = st.selectbox(
        "Select PG",
        pg_data,
        format_func=lambda x: f"{x['name']} - {x['location']}"
    )

    if st.button("📍 I reached PG"):
        st.session_state.arrived = True
        st.rerun()

    if st.session_state.arrived:

        st.success("Choose your essentials 👇")

        cart = st.session_state.cart

        products = {
            "basic": {"name": "Basic Kit", "price": 249},
            "utility": {"name": "Utility Kit", "price": 199},
            "hygiene": {"name": "Hygiene Kit", "price": 129},
            "combo": {"name": "Combo Kit", "price": 499}
        }

        combo_selected = "combo" in cart
        others_selected = any(k in cart for k in ["basic","utility","hygiene"])

        # NORMAL ITEMS
        for key in ["basic","utility","hygiene"]:
            p = products[key]

            st.write(f"{p['name']} - ₹{p['price']}")

            if combo_selected:
                st.button("Add", disabled=True, key=f"d{key}")
            else:
                if key in cart:
                    if st.button(f"❌ Remove {p['name']}", key=f"r{key}"):
                        del cart[key]
                        st.rerun()
                else:
                    if st.button(f"Add {p['name']}", key=f"a{key}"):
                        cart[key] = p
                        st.rerun()

        # COMBO
        st.write("🎁 Combo Kit - ₹499")

        if "combo" in cart:
            if st.button("❌ Remove Combo"):
                del cart["combo"]
                st.rerun()
        else:
            if others_selected:
                st.button("Add Combo", disabled=True)
            else:
                if st.button("Add Combo"):
                    cart.clear()
                    cart["combo"] = products["combo"]
                    st.rerun()

        st.divider()

        # CART
        if cart:
            total = sum(i["price"] for i in cart.values())

            st.write("🛒 Selected Items:")
            for i in cart.values():
                st.write(i["name"])

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
                st.rerun()

        # PAYMENT
        if st.session_state.get("order_done"):

            total = st.session_state.total
            upi = f"upi://pay?pa=reddyinvites@okicici&pn=MoveIn&am={total}"

            st.success("Order placed!")
            st.markdown(f"[💰 Pay Now]({upi})")

            file = st.file_uploader("Upload Payment Screenshot")

            if file:
                st.image(file)
                st.success("Uploaded!")
                st.info("⏳ We will confirm on WhatsApp shortly...")

                st.session_state.clear()
                st.session_state.page = "home"
                st.rerun()

# -----------------------
# ADMIN
# -----------------------
elif st.session_state.page == "admin":

    st.title("👨‍💼 Admin Dashboard")

    password = st.text_input("Password", type="password")

    if password != "1234":
        st.stop()

    if st.button("🚪 Logout"):
        st.session_state.clear()
        st.session_state.page = "home"
        st.rerun()

    st.divider()

    data = order_sheet.get_all_values()
    headers = data[0]
    rows = data[1:]

    for i in reversed(range(len(rows))):

        row_index = i + 2
        o = dict(zip(headers, rows[i]))

        st.write(f"👤 {o['name']} | 📞 {o['phone']}")
        st.write(f"🛒 {o['items']} | ₹{o['total']}")

        # STATUS
        if o["status"] == "Pending":
            st.warning("Pending")
        else:
            st.success("Paid")

        col1, col2 = st.columns(2)

        # APPROVE ONLY IF PENDING
        if o["status"] == "Pending":
            if col1.button("Approve", key=f"a{i}"):

                order_sheet.update_cell(row_index, 6, "Paid")

                st.success("Marked as Paid ✅")
                st.rerun()

        # WHATSAPP ONLY IF PAID
        else:
            msg = f"Hello {o['name']}, your payment is confirmed!"
            wa = f"https://wa.me/{o['phone']}?text={msg.replace(' ','%20')}"

            st.markdown(f"""
                <a href="{wa}" target="_blank">
                    <button style="
                        background-color:#25D366;
                        color:white;
                        padding:10px;
                        border:none;
                        border-radius:6px;">
                        📲 Send WhatsApp
                    </button>
                </a>
            """, unsafe_allow_html=True)

        # CANCEL (ALWAYS)
        if col2.button("Cancel", key=f"c{i}"):

            order_sheet.delete_rows(row_index)

            st.error("Order Deleted")
            st.rerun()

        st.divider()