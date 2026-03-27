ort streamlit as st
import gspread
from google.oauth2.service_account import Credentials
import pandas as pd

@st.cache_data
def load_pg_data():
    creds_dict = dict(st.secrets["gcp"])

    # 🔥 IMPORTANT FIX
    creds_dict["token_uri"] = "https://oauth2.googleapis.com/token"

    creds = Credentials.from_service_account_info(
        creds_dict,
        scopes=[
            "https://www.googleapis.com/auth/spreadsheets",
            "https://www.googleapis.com/auth/drive"
        ],
    )

    client = gspread.authorize(creds)

    sheet = client.open("pg_data").sheet1
    data = sheet.get_all_records()

    return pd.DataFrame(data)


df = load_pg_data()
pg_list = df.to_dict(orient="records")

# -----------------------
# SESSION STATE
# -----------------------
if "arrived" not in st.session_state:
    st.session_state.arrived = False

if "selected_categories" not in st.session_state:
    st.session_state.selected_categories = {}

# -----------------------
# HEADER
# -----------------------
st.title("🏠 Move-in Assistant")
st.write("Move in → Get essentials → Explore nearby")

# -----------------------
# SELECT PG (FROM SHEET)
# -----------------------
if pg_list:
    selected_pg = st.selectbox(
        "🏢 Select Your PG",
        pg_list,
        format_func=lambda x: f"{x['name']} ({x['location']})"
    )

    selected_location = selected_pg["location"].lower()
else:
    st.error("No PG data found")
    st.stop()

# -----------------------
# NEARBY DATA (STATIC FOR NOW)
# -----------------------
nearby_data = {
    "ameerpet": [
        {"name": "🍛 Ameerpet Tiffin Center", "info": "⭐ 4.2 • ₹60 meal • Open now"},
        {"name": "🏥 Apollo Pharmacy", "info": "24/7 Medical Shop"},
        {"name": "🏋️ Fitness Gym", "info": "Budget friendly"},
        {"name": "🛒 Local Grocery", "info": "Daily needs"}
    ],
    "madhapur": [
        {"name": "🍛 Madhapur Mess", "info": "⭐ 4.5 • ₹80 meal • Open now"},
        {"name": "🏥 MedPlus Pharmacy", "info": "24/7 open"},
        {"name": "🏋️ Cult Gym", "info": "Premium"},
        {"name": "🛒 Reliance Smart", "info": "Groceries"}
    ],
    "sr nagar": [
        {"name": "🍛 SR Nagar Tiffins", "info": "⭐ 4.1 • ₹50 meal"},
        {"name": "🏥 Local Pharmacy", "info": "Open now"},
        {"name": "🏋️ Power Gym", "info": "Affordable"},
        {"name": "🛒 Super Market", "info": "Daily essentials"}
    ]
}

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

    tab1, tab2 = st.tabs(["🛍️ Essentials", "📍 Nearby Guide"])

    # =====================
    # 🛍️ ESSENTIALS
    # =====================
    with tab1:
        st.subheader("Starter Kits")

        kits = [
            {"name": "🛏️ Basic Kit", "price": 249, "items": "Bedsheet + Pillow", "category": "basic"},
            {"name": "🪣 Utility Kit", "price": 199, "items": "Bucket + Mug", "category": "utility"},
            {"name": "🧼 Hygiene Kit", "price": 129, "items": "Soap + Toothpaste + Detergent", "category": "hygiene"},
            {"name": "🎁 Combo Kit ⭐ (Best Value)", "price": 449, "items": "All items included", "category": "combo"}
        ]

        for kit in kits:
            col1, col2 = st.columns([3, 1])

            with col1:
                st.markdown(f"### {kit['name']}")
                st.write(kit["items"])
                st.write(f"💰 ₹{kit['price']}")

            with col2:
                if st.button("Add", key=kit["name"]):
                    st.session_state.selected_categories[kit["category"]] = kit

        st.divider()

        # CART
        st.subheader("🛒 Your Cart")

        cart_items = list(st.session_state.selected_categories.values())

        if cart_items:
            total = 0

            for i, item in enumerate(cart_items):
                col1, col2 = st.columns([3, 1])

                with col1:
                    st.write(f"{item['name']} - ₹{item['price']}")

                with col2:
                    if st.button("❌", key=f"remove_{i}"):
                        del st.session_state.selected_categories[item["category"]]
                        st.rerun()

                total += item["price"]

            st.write(f"### Total: ₹{total}")

            if st.button("✅ Place Order"):
                st.success("🎉 Order placed! Delivery on the way.")
                st.session_state.selected_categories = {}

        else:
            st.info("Cart is empty")

    # =====================
    # 📍 NEARBY GUIDE
    # =====================
    with tab2:
        st.subheader(f"Nearby in {selected_location.title()}")

        places = nearby_data.get(selected_location, [])

        if places:
            for place in places:
                st.markdown(f"### {place['name']}")
                st.write(place["info"])
                st.markdown("[🗺️ Open in Google Maps](https://www.google.com/maps)")
                st.divider()
        else:
            st.info("No nearby data available")