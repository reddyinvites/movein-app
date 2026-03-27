import streamlit as st

# -----------------------
# PAGE CONFIG
# -----------------------
st.set_page_config(page_title="Move-in Assistant", layout="wide")

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
    # 🛍️ ESSENTIALS TAB
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
                    # Only one per category
                    st.session_state.selected_categories[kit["category"]] = kit

        st.divider()

        # -----------------------
        # CART
        # -----------------------
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
    # 📍 NEARBY GUIDE TAB
    # =====================
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