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

# -----------------------
# LOAD SPREADSHEET
# -----------------------
try:
    spreadsheet = client.open_by_key("1y60dTYBKgkOi7J37jtGK4BkkmUoZF8yD4P5J3xA5q6Q")
except Exception as e:
    st.error(f"❌ Cannot open sheet: {e}")
    st.stop()

# -----------------------
# LOAD PG DATA
# -----------------------
try:
    pg_sheet = spreadsheet.sheet1
    pg_data = pg_sheet.get_all_records()
except Exception as e:
    st.error(f"❌ PG Load Error: {e}")
    pg_data = []

# -----------------------
# LOAD ORDERS SHEET (SAFE)
# -----------------------
try:
    sheet_names = [ws.title for ws in spreadsheet.worksheets()]
    # st.write("DEBUG:", sheet_names)  # optional debug

    if "orders" in sheet_names:
        order_sheet = spreadsheet.worksheet("orders")
    else:
        st.error("❌ 'orders' sheet not found. Create it manually.")
        st.stop()

except Exception as e:
    st.error(f"❌ Sheet Error: {e}")
    st.stop()

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
# SELECT PG
# -----------------------
if pg_data:
    selected_pg = st.selectbox(
        "🏢 Select Your PG",
        pg_data,
        format_func=lambda x: f"{x['name']} - {x['location']} - ₹{x.get('price','N/A')}"
    )
    selected_location = selected_pg["location"].lower()
else:
    st.error("No PG data found")
    st.stop()

# -----------------------
# ARRIVAL BUTTON
# -----------------------
if not st.session_state.arrived:
    if st.button("📍 I reached PG"):
        st.session_state.arrived = True
        st.success("Welcome! Let's get you settled 👇")

# -----------------------
# MAIN CONTENT
# -----------------------
if st.session_state.arrived:

    tab1, tab2, tab3 = st.tabs(["🛍️ Essentials", "📍 Nearby", "📜 Orders"])

    # =====================
    # 🛍️ ESSENTIALS
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

        # CART
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
                        "Active",
                        str(datetime.now())
                    ])

                    st.success("🎉 Order placed successfully!")
                    st.session_state.selected_categories = {}

                else:
                    st.warning("⚠️ Enter name & phone")

        else:
            st.info("Cart is empty")

    # =====================
    # 📍 NEARBY
    # =====================
    with tab2:

        st.subheader(f"Nearby in {selected_location}")

        nearby_data = {
            "ameerpet": ["🍛 Tiffin Center", "🏥 Pharmacy", "🏋️ Gym"],
            "madhapur": ["🍛 Mess", "🏥 MedPlus", "🏋️ Cult Gym"],
            "sr nagar": ["🍛 Tiffins", "🏥 Medical", "🏋️ Gym"]
        }

        places = nearby_data.get(selected_location, [])

        if places:
            for place in places:
                st.write(place)
        else:
            st.info("No nearby data")

    # =====================
    # 📜 ORDERS
    # =====================
    with tab3:

        try:
            orders = order_sheet.get_all_records()
        except:
            orders = []

        user_orders = [o for o in orders if o["phone"] == user_phone]

        if user_orders:
            for i, order in enumerate(user_orders):

                st.write(f"🧾 {order['items']} - ₹{order['total']}")
                st.write(f"📍 {order['pg']}")
                st.write(f"📌 Status: {order['status']}")

                if order["status"] == "Active":
                    if st.button("❌ Cancel", key=f"cancel_{i}"):

                        row_index = i + 2
                        order_sheet.update_cell(row_index, 6, "Cancelled")

                        st.success("Cancelled successfully")
                        st.rerun()

                st.divider()

        else:
            st.info("No orders found")