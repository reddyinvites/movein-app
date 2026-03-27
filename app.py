import streamlit as st   # ✅ MUST BE FIRST
import gspread
from google.oauth2.service_account import Credentials
from datetime import datetime

# -----------------------
# SESSION STATE
# -----------------------
if "arrived" not in st.session_state:
    st.session_state.arrived = False

if "selected_categories" not in st.session_state:
    st.session_state.selected_categories = {}

if "payment_done" not in st.session_state:
    st.session_state.payment_done = False

# -----------------------
# ADMIN LOGIN
# -----------------------
st.sidebar.title("🔐 Admin Panel")
admin_password = st.sidebar.text_input("Enter Password", type="password")
is_admin = admin_password == "1234"   # 🔥 change this

# -----------------------
# GOOGLE SHEETS CONNECT
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

spreadsheet = client.open_by_key("1y60dTYBKgkOi7J37jtGK4BkkmUoZF8yD4P5J3xA5q6Q")

pg_sheet = spreadsheet.sheet1
pg_data = pg_sheet.get_all_records()

order_sheet = spreadsheet.worksheet("orders")

# -----------------------
# HEADER
# -----------------------
st.title("🏠 Move-in Assistant")
st.write("Move in → Get essentials → Explore nearby")

# -----------------------
# USER INPUT
# -----------------------
user_name = st.text_input("👤 Your Name")
user_phone = st.text_input("📞 Phone Number")

# -----------------------
# PREVENT MULTIPLE ORDERS
# -----------------------
orders = order_sheet.get_all_records()
existing_orders = [o for o in orders if o["phone"] == user_phone and o["status"] != "Cancelled"]

if existing_orders and not is_admin:
    st.warning("⚠️ You already placed an order. Wait for confirmation.")
    st.stop()

# -----------------------
# SELECT PG
# -----------------------
selected_pg = st.selectbox(
    "🏢 Select Your PG",
    pg_data,
    format_func=lambda x: f"{x['name']} - {x['location']} - ₹{x.get('price','N/A')}"
)

selected_location = selected_pg["location"].lower()

# -----------------------
# ARRIVAL BUTTON
# -----------------------
if not st.session_state.arrived:
    if st.button("📍 I reached PG"):
        st.session_state.arrived = True
        st.success("Welcome! Let's get you settled 👇")

# -----------------------
# USER APP
# -----------------------
if st.session_state.arrived and not is_admin:

    tab1, tab2 = st.tabs(["🛍️ Essentials", "📍 Nearby"])

    # =====================
    # ESSENTIALS
    # =====================
    with tab1:

        kits = [
            {"name": "🛏️ Basic Kit", "price": 249, "category": "basic"},
            {"name": "🪣 Utility Kit", "price": 199, "category": "utility"},
            {"name": "🧼 Hygiene Kit", "price": 129, "category": "hygiene"},
            {"name": "🎁 Combo Kit", "price": 449, "category": "combo"}
        ]

        for kit in kits:
            col1, col2 = st.columns([3,1])
            with col1:
                st.write(f"{kit['name']} - ₹{kit['price']}")
            with col2:
                if st.button("Add", key=kit["name"]):
                    st.session_state.selected_categories[kit["category"]] = kit

        st.divider()

        cart = list(st.session_state.selected_categories.values())

        if cart:
            total = sum(item["price"] for item in cart)

            for item in cart:
                st.write(f"{item['name']} - ₹{item['price']}")

            st.write(f"### Total: ₹{total}")

            if st.button("✅ Place Order"):
                if user_name and user_phone:

                    items_text = ", ".join([i["name"] for i in cart])

                    order_sheet.append_row([
                        user_name,
                        user_phone,
                        selected_pg["name"],
                        items_text,
                        total,
                        "Pending",
                        str(datetime.now())
                    ])

                    st.session_state.current_order = {
                        "items": items_text,
                        "total": total
                    }

                    st.session_state.payment_done = False

        # PAYMENT FLOW
        if "current_order" in st.session_state:

            total = st.session_state.current_order["total"]
            items_text = st.session_state.current_order["items"]

            upi_link = f"upi://pay?pa=reddyinvites@okicici&pn=MoveIn&am={total}&cu=INR"

            st.success("🧾 Order placed!")

            st.markdown(
                f"""
                <a href="{upi_link}">
                    <button style="background-color:#28a745;color:white;padding:12px;border-radius:8px;">
                    💰 Pay Now
                    </button>
                </a>
                """,
                unsafe_allow_html=True
            )

            st.warning("⚠️ After payment, upload screenshot")

            file = st.file_uploader("📸 Upload Screenshot", type=["png","jpg","jpeg"])

            if file:
                st.image(file)
                st.success("✅ Uploaded! We will verify your payment.")
                st.info("⏳ Please wait... we will confirm via WhatsApp shortly")

                st.session_state.payment_done = True
                st.session_state.selected_categories = {}

            if st.session_state.payment_done:
                msg = f"Hello {user_name}, I have paid ₹{total} for {items_text}"
                wa = f"https://wa.me/{user_phone}?text={msg.replace(' ','%20')}"

                if st.button("📲 Confirm on WhatsApp"):
                    st.markdown(f"<meta http-equiv='refresh' content='0; url={wa}'>", unsafe_allow_html=True)

    # =====================
    # NEARBY
    # =====================
    with tab2:
        st.subheader(f"Nearby in {selected_location.title()}")

        for item in ["tiffins","medical","gym","grocery"]:
            url = f"https://www.google.com/maps/search/{item}+near+{selected_location}"
            st.markdown(f"🔎 [{item.title()}]({url})")

# =====================
# ADMIN DASHBOARD
# =====================
if is_admin:

    st.title("👨‍💼 Admin Dashboard")

    orders = order_sheet.get_all_records()

    for i, o in enumerate(orders):

        st.write(f"👤 {o['name']} | 📞 {o['phone']}")
        st.write(f"🏢 {o['pg']}")
        st.write(f"🛒 {o['items']}")
        st.write(f"💰 ₹{o['total']}")
        st.write(f"📌 {o['status']}")

        col1, col2 = st.columns(2)

        if col1.button("✅ Approve", key=f"a{i}"):
            order_sheet.update_cell(i+2,6,"Approved")
            st.success("Approved")

        if col2.button("❌ Reject", key=f"r{i}"):
            order_sheet.update_cell(i+2,6,"Rejected")
            st.error("Rejected")

        msg = f"Hello {o['name']}, your order is {o['status']}"
        wa = f"https://wa.me/{o['phone']}?text={msg.replace(' ','%20')}"

        if st.button("📲 WhatsApp User", key=f"w{i}"):
            st.markdown(f"<meta http-equiv='refresh' content='0; url={wa}'>", unsafe_allow_html=True)

        st.divider()