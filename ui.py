import streamlit as st
import requests
import subprocess
import time
import os

# Function to start Flask backend
def start_backend():
    if "backend_running" not in st.session_state:
        st.session_state.backend_running = False
    
    if not st.session_state.backend_running:
        st.session_state.backend_process = subprocess.Popen(["python", "backend.py"])
        time.sleep(3)  # Wait for the backend to start
        st.session_state.backend_running = True

# Start backend
start_backend()

# Set Flask backend URL
BACKEND_URL = "http://127.0.0.1:8000"

st.title("AI Healthcare Diagnosis App")

# Section: Diagnosis
st.header("Patient Diagnosis")
symptoms = st.text_area("Enter symptoms:")
if st.button("Get Diagnosis"):
    if symptoms:
        response = requests.post(f"{BACKEND_URL}/diagnose", json={"symptoms": symptoms})
        if response.status_code == 200:
            result = response.json()
            st.success(f"Diagnosis: {result['diagnosis']}")
            st.write("Recommended Hospitals:")
            for hospital in result["hospitals"]:
                st.write(f"- **{hospital['name']}** ({hospital['location']}), Contact: {hospital['contact']}")
        else:
            st.error("Failed to fetch diagnosis. Try again.")
    else:
        st.warning("Please enter symptoms.")

# Section: Register a Hospital
st.header("Register a Hospital")
name = st.text_input("Hospital Name")
location = st.text_input("Location")
contact = st.text_input("Contact")
services = st.text_area("Services (comma-separated)").split(",")

if st.button("Register Hospital"):
    if name and location and contact and services:
        response = requests.post(f"{BACKEND_URL}/register_hospital", json={
            "name": name,
            "location": location,
            "contact": contact,
            "services": services
        })
        if response.status_code == 201:
            st.success("Hospital registered successfully!")
        else:
            st.error("Failed to register hospital.")
    else:
        st.warning("Please fill all fields.")

# Stop backend when closing Streamlit
if "backend_process" in st.session_state:
    st.session_state.backend_process.terminate()
