import streamlit as st
import gspread
from google.oauth2.service_account import Credentials
from datetime import datetime
import cloudinary
import cloudinary.uploader

# ---------------- CLOUDINARY ----------------
try:
    cloudinary.config(
        cloud_name=st.secrets["cloudinary"]["cloud_name"],
        api_key=st.secrets["cloudinary"]["api_key"],
        api_secret=st.secrets["cloudinary"]["api_secret"]
    )
    CLOUDINARY_ENABLED = True
except:
    CLOUDINARY_ENABLED = False

# ---------------- SESSION ----------------
if "page" not in st.session_state:
    st.session_state.page = "home"

if "cart" not in st.session_state:
    st.session_state.cart = {}

if "arrived" not in st.session_state:
    st.session_state.arrived = False

# ---------------- GOOGLE SHEETS ----------------
scope = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive"
]

gcp_info = dict(st.secrets["gcp_service_account"])
gcp_info["private_key"] = gcp_info["private_key"].replace("\\n", "\n")

creds = Credentials.from_service_account_info(gcp_info, scopes=scope)
client = gspread.authorize(creds)

sheet = client.open_by_key("1y60dTYBKgkOi7J37jtGK4BkkmUoZF8yD4P5J3xA5q6Q")

pg_sheet = sheet.sheet1
order_sheet = sheet.worksheet("orders")

# ---------------- LOAD PG ----------------
pg_raw = pg_sheet.get_all_records()

pg_data = []
for row in pg_raw:
    val = row.get("pg_name") or row.get("pg")
    if val:
        pg_data.append(val)

pg_data = sorted(list(set(pg_data)))

# ================= HOME =================
if st.session_state.page == "home":

    st.title("🏠 Move-in Assistant")

    col1, col2 = st.columns(2)

    if col1.button("👤 User"):
        st.session_state.page = "user"
        st.rerun()

    if col2.button("👨‍💼 Admin"):
        st.session_state.page = "admin"
        st.rerun()

# ================= USER =================
elif st.session_state.page == "user":

    col1, col2 = st.columns([8,2])
    col1.title("👤 User Dashboard")

    if col2.button("🚪 Logout"):
        st.session_state.clear()
        st.rerun()

    name = st.text_input("👤 Name")
    phone = st.text_input("📞 Phone (+91XXXXXXXXXX)")

    # VALIDATION
    valid_phone = False
    if phone:
        if phone.startswith("+91") and len(phone) == 13 and phone[3:].isdigit():
            valid_phone = True
        else:
            st.error("Enter valid phone number ❌")

    if not name:
        st.warning("Name is required ⚠️")

    selected_pg = st.selectbox("🏠 Select PG", pg_data)

    if st.button("📍 I reached PG", disabled=not (name and valid_phone)):
        st.session_state.arrived = True
        st.rerun()

    if st.session_state.arrived:

        cart = st.session_state.cart

        products = {
            "basic": {"name": "Basic Kit", "price": 249, "items": "Bucket, Mug, Pillow, Bedsheet"},
            "utility": {"name": "Utility Kit", "price": 199, "items": "Cleaning Brush, Washing Powder, Cloth Clips"},
            "hygiene": {"name": "Hygiene Kit", "price": 129, "items": "Soap, Shampoo, Toothpaste, Sanitizer"},
            "combo": {"name": "Combo Kit", "price": 499, "items": "All items combined"}
        }

        st.subheader("🛍️ Select Your Kits")

        combo_selected = "combo" in cart
        single_selected = any(k in cart for k in ["basic","utility","hygiene"])

        for key in products:
            p = products[key]

            col1, col2 = st.columns([3,1])

            with col1:
                st.markdown(f"**{p['name']}**  \n💰 ₹{p['price']}  \n📦 {p['items']}")

            with col2:
                disabled = False
                if key == "combo" and single_selected:
                    disabled = True
                if key in ["basic","utility","hygiene"] and combo_selected:
                    disabled = True

                if key in cart:
                    if st.button("❌ Remove", key=f"r{key}"):
                        del cart[key]
                        st.rerun()
                else:
                    if st.button("➕ Add", key=f"a{key}", disabled=disabled):
                        cart[key] = p
                        st.rerun()

            st.divider()

        if cart:
            total = sum(i["price"] for i in cart.values())
            st.markdown(f"## 💳 Total: ₹{total}")

            if st.button("🚀 Place Order"):

                if not name:
                    st.error("Name required ❌")
                    st.stop()

                existing = order_sheet.get_all_records()
                phones = [str(x.get("phone_number")).strip() for x in existing]

                if phone.strip() in phones:
                    st.error("❌ Only one order allowed per number")
                    st.stop()

                items = ", ".join([i["name"] for i in cart.values()])

                order_sheet.append_row([
                    name, phone, selected_pg, items,
                    total, "Pending", str(datetime.now()), ""
                ])

                st.session_state.order_done = True
                st.session_state.total = total
                st.rerun()

        if st.session_state.get("order_done"):

            total = st.session_state.total
            st.success("✅ Order placed!")

            upi_link = f"upi://pay?pa=reddyinvites@okicici&pn=MoveIn&am={total}"

            st.markdown(f"""
            <a href="{upi_link}">
            <button style="background:#28a745;color:white;padding:10px;border:none;border-radius:8px;">
            💰 Pay Now</button></a>
            """, unsafe_allow_html=True)

            st.info("Upload screenshot 👇")

            file = st.file_uploader("📤 Upload Screenshot")

            if file:
                st.image(file, width=200)

                if CLOUDINARY_ENABLED:
                    result = cloudinary.uploader.upload(file)
                    image_url = result["secure_url"]

                    last_row = len(order_sheet.get_all_values())
                    order_sheet.update_cell(last_row, 8, image_url)

                    st.success("✅ Uploaded!")
                    st.success("📲 We will confirm on WhatsApp")
                    st.warning("Click logout after confirmation")

    st.markdown("---")
    if st.button("🚪 Logout (Exit)"):
        st.session_state.clear()
        st.rerun()

# ================= ADMIN =================
elif st.session_state.page == "admin":

    st.title("👨‍💼 Admin Dashboard")

    password = st.text_input("Password", type="password")

    if password != "1234":
        st.stop()

    data = order_sheet.get_all_values()
    headers = data[0]
    rows = data[1:]

    for i in reversed(range(len(rows))):

        o = dict(zip(headers, rows[i]))

        name = o.get("Owner_name") or ""
        if not name or name.lower() == "none":
            name = "❌ Missing Name"

        phone = o.get("phone_number") or ""
        pg = o.get("pg_name") or ""
        items = o.get("items") or ""
        status = o.get("status") or ""

        st.write(f"👤 {name} | 📞 {phone}")
        st.write(f"🏠 {pg} | 🛒 {items}")

        if o.get("screenshot"):
            st.success("📸 Screenshot Uploaded")
            st.image(o["screenshot"], width=150)

        col1, col2, col3 = st.columns(3)

        if status == "Approved":
            col1.success("✅ Approved")
        else:
            if col1.button("✅ Approve", key=f"approve{i}"):
                order_sheet.update_cell(i+2, 6, "Approved")
                st.rerun()

        if col2.button("❌ Delete", key=f"delete{i}"):
            order_sheet.delete_rows(i+2)
            st.rerun()

        if phone:
            msg = f"Hi {name}, your order is confirmed ✅\nItems: {items}"
            wa = f"https://wa.me/{phone.replace('+','')}?text={msg}"

            col3.markdown(f"""
            <a href="{wa}" target="_blank">
            <button style="background:#25D366;color:white;padding:8px;border:none;border-radius:6px;">
            💬 WhatsApp</button></a>
            """, unsafe_allow_html=True)

        st.divider()