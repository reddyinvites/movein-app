import streamlit as st

# Page config
st.set_page_config(page_title="Move-in Assistant", layout="wide")

# Session state
if "arrived" not in st.session_state:
    st.session_state.arrived = False

if "cart" not in st.session_state:
    st.session_state.cart = []

# Header
st.title("🏠 Move-in Assistant")
st.write("Move in → Get essentials → Explore nearby")

# Arrival button
if not st.session_state.arrived:
    if st.button("📍 I reached PG"):
        st.session_state.arrived = True
        st.success("Welcome! Let's get you settled 👇")

# Main content
if st.session_state.arrived:

    tab1, tab2 = st.tabs(["🛍️ Essentials", "📍 Nearby Guide"])

    # ---------------- Essentials ----------------
    with tab1:
        st.subheader("Starter Kits")

        kits = [
            {"name": "🛏️ Basic Kit", "price": 249, "items": "Bedsheet + Pillow"},
            {"name": "🪣 Utility Kit", "price": 199, "items": "Bucket + Mug"},
            {"name": "🧼 Hygiene Kit", "price": 129, "items": "Soap + Toothpaste + Detergent"},
            {"name": "🎁 Combo Kit ⭐ (Best Value)", "price": 449, "items": "All items included"}
        ]

        for kit in kits:
            col1, col2 = st.columns([3, 1])

            with col1:
                st.markdown(f"### {kit['name']}")
                st.write(kit["items"])
                st.write(f"💰 ₹{kit['price']}")

            with col2:
                if st.button("Add", key=kit["name"]):
                    st.session_state.cart.append(kit)

        st.divider()

        # Cart
        st.subheader("🛒 Your Cart")

        if st.session_state.cart:
            total = 0
            for item in st.session_state.cart:
                st.write(f"{item['name']} - ₹{item['price']}")
                total += item["price"]

            st.write(f"### Total: ₹{total}")

            if st.button("✅ Place Order"):
                st.success("🎉 Order placed! Delivery on the way.")
                st.session_state.cart = []
        else:
            st.info("Cart is empty")

    # ---------------- Nearby ----------------
    with tab2:
        st.subheader("Nearby Essentials")

        places = [
            {"name": "🍛 ABC Tiffin Center", "info": "⭐ 4.3 • ₹50 meal • Open now"},
            {"name": "🏥 MedPlus Pharmacy", "info": "⭐ 4.5 • Open 24/7"},
            {"name": "🏋️ Local Gym", "info": "⭐ 4.1 • Budget friendly"},
            {"name": "🛒 Reliance Smart", "info": "⭐ 4.2 • Groceries"}
        ]

        for place in places:
            st.markdown(f"### {place['name']}")
            st.write(place["info"])
            st.markdown("[🗺️ Open in Google Maps](https://www.google.com/maps)")
            st.divider()
