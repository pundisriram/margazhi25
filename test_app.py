"""Minimal test to check if Streamlit works"""
import streamlit as st

st.title("Test App")
st.write("If you see this, Streamlit is working!")

try:
    from data_loader import ConcertDataLoader
    st.success("Data loader imported successfully")
    
    loader = ConcertDataLoader("2025_Margazhi_schedule_cleaned.txt")
    st.success(f"Data loaded: {len(loader.df)} rows")
except Exception as e:
    st.error(f"Error: {e}")
    import traceback
    st.code(traceback.format_exc())

