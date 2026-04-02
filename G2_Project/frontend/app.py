<<<<<<< HEAD
import streamlit as st
import requests
import pandas as pd
from dotenv import load_dotenv
import os

load_dotenv()

API_BASE_URL = os.getenv("API_BASE_URL", "http://127.0.0.1:8000")

st.set_page_config(page_title="E-commerce Recommendation System", layout="wide")

st.title("E-commerce Product Recommendation System")
st.write("Get personalized product recommendations based on customer purchase history.")

st.sidebar.header("Input")
customer_id = st.sidebar.number_input("Enter Customer ID", min_value=1, step=1, value=17850)
top_n = st.sidebar.slider("Number of Recommendations", min_value=1, max_value=20, value=10)

get_recommendations_btn = st.sidebar.button("Get Recommendations")
show_history_btn = st.sidebar.button("Show Purchase History")

col1, col2 = st.columns(2)

if get_recommendations_btn:
    try:
        response = requests.get(f"{API_BASE_URL}/recommend/{customer_id}", params={"top_n": top_n}, timeout=30)

        with col1:
            st.subheader("Recommended Products")

            if response.status_code == 200:
                recommendations = response.json().get("recommendations", [])
                if recommendations:
                    rec_df = pd.DataFrame(recommendations)
                    st.dataframe(rec_df, use_container_width=True)
                else:
                    st.warning("No recommendations found.")
            else:
                st.error("Failed to fetch recommendations.")
    except Exception as e:
        st.error(f"Error while fetching recommendations: {e}")

if show_history_btn:
    try:
        response = requests.get(f"{API_BASE_URL}/customer/{customer_id}/history", timeout=30)

        with col2:
            st.subheader("Customer Purchase History")

            if response.status_code == 200:
                history = response.json().get("history", [])
                if history:
                    history_df = pd.DataFrame(history)
                    st.dataframe(history_df, use_container_width=True)
                else:
                    st.warning("No purchase history found.")
            else:
                st.error("Failed to fetch purchase history.")
    except Exception as e:
        st.error(f"Error while fetching history: {e}")

st.markdown("---")
st.subheader("Popular Products")

try:
    response = requests.get(f"{API_BASE_URL}/popular", params={"limit": 10}, timeout=30)

    if response.status_code == 200:
        popular_products = response.json().get("popular_products", [])
        if popular_products:
            popular_df = pd.DataFrame(popular_products)
            st.dataframe(popular_df, use_container_width=True)
        else:
            st.warning("No popular products found.")
    else:
        st.error("Failed to fetch popular products.")
except Exception as e:
=======
import streamlit as st
import requests
import pandas as pd
from dotenv import load_dotenv
import os

load_dotenv()

API_BASE_URL = os.getenv("API_BASE_URL", "http://127.0.0.1:8000")

st.set_page_config(page_title="E-commerce Recommendation System", layout="wide")

st.title("E-commerce Product Recommendation System")
st.write("Get personalized product recommendations based on customer purchase history.")

st.sidebar.header("Input")
customer_id = st.sidebar.number_input("Enter Customer ID", min_value=1, step=1, value=17850)
top_n = st.sidebar.slider("Number of Recommendations", min_value=1, max_value=20, value=10)

get_recommendations_btn = st.sidebar.button("Get Recommendations")
show_history_btn = st.sidebar.button("Show Purchase History")

col1, col2 = st.columns(2)

if get_recommendations_btn:
    try:
        response = requests.get(f"{API_BASE_URL}/recommend/{customer_id}", params={"top_n": top_n}, timeout=30)

        with col1:
            st.subheader("Recommended Products")

            if response.status_code == 200:
                recommendations = response.json().get("recommendations", [])
                if recommendations:
                    rec_df = pd.DataFrame(recommendations)
                    st.dataframe(rec_df, use_container_width=True)
                else:
                    st.warning("No recommendations found.")
            else:
                st.error("Failed to fetch recommendations.")
    except Exception as e:
        st.error(f"Error while fetching recommendations: {e}")

if show_history_btn:
    try:
        response = requests.get(f"{API_BASE_URL}/customer/{customer_id}/history", timeout=30)

        with col2:
            st.subheader("Customer Purchase History")

            if response.status_code == 200:
                history = response.json().get("history", [])
                if history:
                    history_df = pd.DataFrame(history)
                    st.dataframe(history_df, use_container_width=True)
                else:
                    st.warning("No purchase history found.")
            else:
                st.error("Failed to fetch purchase history.")
    except Exception as e:
        st.error(f"Error while fetching history: {e}")

st.markdown("---")
st.subheader("Popular Products")

try:
    response = requests.get(f"{API_BASE_URL}/popular", params={"limit": 10}, timeout=30)

    if response.status_code == 200:
        popular_products = response.json().get("popular_products", [])
        if popular_products:
            popular_df = pd.DataFrame(popular_products)
            st.dataframe(popular_df, use_container_width=True)
        else:
            st.warning("No popular products found.")
    else:
        st.error("Failed to fetch popular products.")
except Exception as e:
>>>>>>> 078f103c00d85cbbec5ede50581083ac1663ff12
    st.error(f"Error while fetching popular products: {e}")