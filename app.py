import streamlit as st
import pandas as pd

st.set_page_config(
    page_title="Stores Executive Analytics Dashboard",
    page_icon="📊",
    layout="wide"
)

st.title("📊 Multi-Store Executive Revenue & Entity Analytics")
st.markdown("Production-grade data pipeline metrics and AI natural language agent.")

STORE_DATA = {
    "STORE1": {
        "top_5_days": [
            {"date": "2025-08-20", "paid_price": 3716.66},
            {"date": "2025-09-22", "paid_price": 3584.76},
            {"date": "2026-01-15", "paid_price": 3304.98},
            {"date": "2025-09-03", "paid_price": 3261.35},
            {"date": "2025-10-17", "paid_price": 3249.17}
        ],
        "unique_users": 3221,
        "unique_authors": 324,
        "popular_author": "Darron Ernser, Miss Lorina Kertzmann",
        "best_buyer_ids": [48403, 48904, 50056]
    },
    "STORE2": {
        "top_5_days": [
            {"date": "2025-11-16", "paid_price": 3786.61},
            {"date": "2025-12-12", "paid_price": 3122.99},
            {"date": "2025-12-10", "paid_price": 3023.62},
            {"date": "2025-09-19", "paid_price": 2937.21},
            {"date": "2025-11-19", "paid_price": 2912.81}
        ],
        "unique_users": 3166,
        "unique_authors": 281,
        "popular_author": "Kenneth Hamill, Marcus McKenzie",
        "best_buyer_ids": [51014]
    },
    "STORE3": {
        "top_5_days": [
            {"date": "2025-10-09", "paid_price": 3551.19},
            {"date": "2025-09-21", "paid_price": 3242.40},
            {"date": "2025-09-04", "paid_price": 3040.20},
            {"date": "2025-09-30", "paid_price": 3016.10},
            {"date": "2025-09-01", "paid_price": 2936.02}
        ],
        "unique_users": 2955,
        "unique_authors": 307,
        "popular_author": "Loreta Metz",
        "best_buyer_ids": [52881, 53869, 54846]
    },
    "STORE4": {
        "top_5_days": [
            {"date": "2025-11-24", "paid_price": 4367.11},
            {"date": "2025-11-17", "paid_price": 3810.46},
            {"date": "2025-11-28", "paid_price": 3441.99},
            {"date": "2025-11-13", "paid_price": 3400.02},
            {"date": "2025-09-21", "paid_price": 3302.94}
        ],
        "unique_users": 2850,
        "unique_authors": 299,
        "popular_author": "Emil Rempel, Heriberto Kutch, Merle Rice",
        "best_buyer_ids": [53347, 54809]
    },
    "STORE5": {
        "top_5_days": [
            {"date": "2025-10-20", "paid_price": 3490.66},
            {"date": "2025-11-28", "paid_price": 3266.02},
            {"date": "2025-09-27", "paid_price": 3187.10},
            {"date": "2025-10-17", "paid_price": 3160.69},
            {"date": "2025-12-05", "paid_price": 3118.34}
        ],
        "unique_users": 2987,
        "unique_authors": 311,
        "popular_author": "Dulcie Bode",
        "best_buyer_ids": [52895, 53969]
    }
}

tabs = st.tabs(["STORE1", "STORE2", "STORE3", "STORE4", "STORE5"])

for idx, store_name in enumerate(["STORE1", "STORE2", "STORE3", "STORE4", "STORE5"]):
    with tabs[idx]:
        data = STORE_DATA[store_name]
        
        col1, col2, col3 = st.columns(3)
        col1.metric("Unique Real Users", f"{data['unique_users']:,}")
        col2.metric("Unique Author Sets", f"{data['unique_authors']:,}")
        col3.metric("Best Buyer IDs", str(data['best_buyer_ids']))
        
        st.markdown(f"**Most Popular Author Set:** {data['popular_author']}")
        st.divider()
        
        col_left, col_right = st.columns([1, 2])
        
        with col_left:
            st.subheader("Top 5 Days by Revenue")
            df_top = pd.DataFrame(data['top_5_days'])
            st.dataframe(df_top)
            
        with col_right:
            st.subheader("Daily Revenue Chart")
            image_path = f"{store_name}_revenue.png"
            try:
                st.image(image_path, caption=f"Daily Revenue Trend — {store_name}")
            except Exception:
                st.info("Chart image loading...")

st.sidebar.title("🤖 Data AI Assistant")
st.sidebar.markdown("Ask natural language questions about store metrics, revenue, and buyers.")

if "messages" not in st.session_state:
    st.session_state.messages = []

for message in st.session_state.messages:
    with st.sidebar.chat_message(message["role"]):
        st.markdown(message["content"])

if user_query := st.sidebar.chat_input("e.g. Who is the best buyer in STORE3?"):
    st.session_state.messages.append({"role": "user", "content": user_query})
    with st.sidebar.chat_message("user"):
        st.markdown(user_query)

    query_lower = user_query.lower()
    
    target_store = None
    for s in ["store1", "store2", "store3", "store4", "store5"]:
        if s in query_lower:
            target_store = s.upper()
            break

    if target_store:
        s_data = STORE_DATA[target_store]
        if "best buyer" in query_lower or "buyer" in query_lower or "customer" in query_lower:
            response_text = f"The best buyer ID(s) for **{target_store}** are: `{s_data['best_buyer_ids']}`."
        elif "popular author" in query_lower or "author" in query_lower:
            response_text = f"The most popular author set for **{target_store}** is **{s_data['popular_author']}**."
        elif "unique user" in query_lower or "users" in query_lower:
            response_text = f"**{target_store}** has **{s_data['unique_users']:,}** unique real users."
        elif "top day" in query_lower or "revenue" in query_lower:
            top_day = s_data['top_5_days'][0]
            response_text = f"The top revenue day for **{target_store}** was **{top_day['date']}** with **${top_day['paid_price']:,}**."
        else:
            response_text = f"Metrics for **{target_store}**:\n- Unique Users: {s_data['unique_users']}\n- Best Buyers: {s_data['best_buyer_ids']}\n- Top Author: {s_data['popular_author']}"
    else:
        response_text = "I can answer questions about any store! Try asking: *'Who is the best buyer in STORE3?'* or *'How many users in STORE1?'*"

    with st.sidebar.chat_message("assistant"):
        st.markdown(response_text)
    st.session_state.messages.append({"role": "assistant", "content": response_text})