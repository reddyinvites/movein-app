import streamlit as st
import gspread
from google.oauth2.service_account import Credentials

# =========================
# GOOGLE CONNECT (FIXED)
# =========================
scope = [
    "https://spreadsheets.google.com/feeds",
    "https://www.googleapis.com/auth/drive"
]

if "gcp" not in st.secrets:
    st.error("Missing GCP secrets")
    st.stop()

gcp_info = dict(st.secrets["gcp"])
gcp_info["private_key"] = gcp_info["private_key"].replace("\\n", "\n")

creds = Credentials.from_service_account_info(
    gcp_info,
    scopes=scope
)

client = gspread.authorize(creds)

# 🔥 YOUR SHEET ID
sheet = client.open_by_key("1y60dTYBKgkOi7J37jtGK4BkkmUoZF8yD4P5J3xA5q6Q")

pg_sheet = sheet.sheet1
order_sheet = sheet.worksheet("orders")

# =========================
# SESSION
# =========================
if "mode" not in st.session_state:
    st.session_state.mode = None

if "selected" not in st.session_state:
    st.session_state.selected = {}

if "arrived" not in st.session_state:
    st.session_state.arrived = False

if "ordered" not in st.session_state:
    st.session_state.ordered = False


# =========================
# MODE SELECT
# =========================
if st.session_state.mode is None:
    st.title("🏠 Move-in Assistant")

    col1, col2 = st.columns(2)

    if col1.button("👤 User"):
        st.session_state.mode = "user"
        st.rerun()

    if col2.button("🧑‍💼 Admin"):
        st.session_state.mode = "admin"
        st.rerun()


# =========================
# USER APP
# =========================
if st.session_state.mode == "user":

    st.title("👤 User Dashboard")

    name = st.text_input("", placeholder="Enter your name")
    phone = st.text_input("", placeholder="+91XXXXXXXXXX")

    pg_list = pg_sheet.get_all_records()

    selected_pg = st.selectbox(
        "Select PG",
        pg_list,
        format_func=lambda x: f"{x['name']} - {x['location']}"
    )

    if st.button("📍 I reached PG"):
        st.session_state.arrived = True

    kits = {
        "basic": {"name": "Basic Kit", "price": 249, "items": "Bedsheet + Pillow"},
        "utility": {"name": "Utility Kit", "price": 199, "items": "Bucket + Mug"},
        "hygiene": {"name": "Hygiene Kit", "price": 129, "items": "Soap + Toothpaste"},
        "combo": {"name": "Combo Kit", "price": 499, "items": "All included"}
    }

    if st.session_state.arrived:

        st.success("Choose your essentials 👇")

        selected = st.session_state.selected

        combo_selected = "combo" in selected
        normal_selected = any(k in selected for k in ["basic", "utility", "hygiene"])

        def add_item(key):
            st.session_state.selected[key] = kits[key]

        def remove_item(key):
            if key in st.session_state.selected:
                del st.session_state.selected[key]

        for key, kit in kits.items():

            st.subheader(kit["name"])
            st.write(kit["items"])
            st.write(f"₹{kit['price']}")

            disabled = False
            if key == "combo" and normal_selected:
                disabled = True
            if key != "combo" and combo_selected:
                disabled = True

            if key in selected:
                if st.button(f"❌ Remove {kit['name']}", key=key):
                    remove_item(key)
                    st.rerun()
            else:
                if st.button(f"Add {kit['name']}", key=key, disabled=disabled):
                    add_item(key)
                    st.rerun()

            st.divider()

        if selected:

            total = sum(i["price"] for i in selected.values())

            st.subheader("🛒 Selected Items")
            for i in selected.values():
                st.write(f"{i['name']} - ₹{i['price']}")

            st.write(f"### Total: ₹{total}")

            if st.button("✅ Place Order"):

                items = ", ".join(i["name"] for i in selected.values())

                order_sheet.append_row([
                    name,
                    phone,
                    selected_pg["name"],
                    items,
                    total,
                    "Pending"
                ])

                st.session_state.ordered = True
                st.success("Order placed! Pay now 👇")

        if st.session_state.ordered:

            upi = f"upi://pay?pa=reddyinvites@okicici&pn=MoveIn&am={total}&cu=INR"

            st.link_button("💰 Pay Now", upi)

            st.warning("Upload payment screenshot")

            file = st.file_uploader("Upload Screenshot")

            if file:
                st.success("Uploaded! We will confirm shortly via WhatsApp 📲")

                st.session_state.selected = {}
                st.session_state.arrived = False
                st.session_state.ordered = False

                st.rerun()


# =========================
# ADMIN PANEL
# =========================
if st.session_state.mode == "admin":

    st.title("🧑‍💼 Admin Dashboard")

    pwd = st.text_input("Password", type="password")

    if pwd == "admin123":

        if st.button("🚪 Logout"):
            st.session_state.mode = None
            st.rerun()

        data = order_sheet.get_all_records()

        for i, o in enumerate(data, start=2):

            st.write(f"👤 {o['name']} | {o['phone']}")
            st.write(f"🛒 {o['items']} | ₹{o['total']}")

            if o["status"] == "Pending":
                st.warning("Pending")
            else:
                st.success("Paid")

            col1, col2 = st.columns(2)

            if o["status"] == "Pending":
                if col1.button("Approve", key=f"a{i}"):

                    order_sheet.update_cell(i, 6, "Paid")

                    msg = f"Hi {o['name']}, your order is confirmed ✅"
                    wa = f"https://wa.me/{o['phone']}?text={msg.replace(' ','%20')}"

                    st.markdown(f"""
                        <meta http-equiv="refresh" content="0;url={wa}">
                    """, unsafe_allow_html=True)

                    st.rerun()

            else:
                msg = f"Hi {o['name']}, your order is confirmed ✅"
                wa = f"https://wa.me/{o['phone']}?text={msg.replace(' ','%20')}"
                st.link_button("📲 WhatsApp", wa)

            if col2.button("Cancel", key=f"c{i}"):
                order_sheet.delete_rows(i)
                st.error("Deleted")
                st.rerun()

            st.divider()