import streamlit as st
from PIL import Image
import requests
from io import BytesIO
import math

# Set up the Streamlit page layout
st.set_page_config(page_title="5G Site Estimator for Coverage & Capacity", layout="centered")

# Load logo image from GitHub
logo_url = "https://github.com/Marivull/5g-planning-web-bot/raw/main/logo.png"
response = requests.get(logo_url)
logo = Image.open(BytesIO(response.content))

# Display the logo
st.image(logo, caption="5G Site Estimator Logo")

st.title("📡 5G Site Estimator for Coverage & Capacity")

# User Inputs Section
with st.form(key="inputs_form"):
    # Location Inputs
    country = st.selectbox("Select Country:", ["Egypt"])
    city = st.selectbox("Select City:", ["Cairo", "Giza", "Alexandria"])

    if city == "Cairo":
        area = st.selectbox("Select Area:", ["Nasr City", "Heliopolis", "Maadi", "Zamalek", "Downtown"])
    elif city == "Giza":
        area = st.selectbox("Select Area:", ["Dokki", "Mohandessin", "6th of October", "Sheikh Zayed"])
    else:
        area = st.selectbox("Select Area:", ["Sidi Gaber", "Smouha", "Stanley", "Gleem", "Miami"])

    # Area Size, Frequency, and other parameters
    area_km2 = st.number_input("Enter Area Size (km²):", min_value=0.1, value=5.0)
    frequency_mhz = st.number_input("Enter Carrier Frequency (MHz):", min_value=600, max_value=5000, value=3500)
    desired_rsrp = st.number_input("Enter Desired RSRP (dBm):", min_value=-130, max_value=0, value=-100)
    population = st.number_input("Enter Population of the Area:", min_value=100, value=8000)
    penetration_rate = st.slider("5G Penetration Rate (%):", min_value=0, max_value=100, value=20)
    antenna_type = st.selectbox("Select Antenna Type:", ['8T8R', '32T32R', '64T64R', '128T128R'])

    # Submit Button
    submit_button = st.form_submit_button("Calculate Results")

# Only show results if the form is submitted
if submit_button:
    # Constants and adjustments
    antenna_scaling = {'8T8R': 1.0, '32T32R': 1.5, '64T64R': 2.0, '128T128R': 3.0}
    scaling_factor = antenna_scaling[antenna_type]

    # Adjusted coverage radius function
    def calculate_coverage_radius(freq_mhz, rsrp):
        base_radius = 0.5  # Adjusted for urban area with better coverage
        freq_adjustment = (3500 / freq_mhz) ** 0.5  # Frequency effect
        rsrp_adjustment = (abs(rsrp + 110) / 10) ** 0.5  # Better RSRP = more radius
        radius = base_radius * freq_adjustment * rsrp_adjustment
        return max(0.3, min(radius, 0.6))  # Adjusted to be within realistic limits

    coverage_radius_km = calculate_coverage_radius(frequency_mhz, desired_rsrp)

    # Calculate the number of sites based on coverage
    def calculate_number_of_sites(area_km2, coverage_radius_km):
        # Adjusting for ISD (inter-site distance)
        ideal_isd_km = coverage_radius_km * 2  # Assuming sites need to be 2x the radius apart
        area_per_site = (math.sqrt(3) / 2) * (ideal_isd_km ** 2)
        return math.ceil(area_km2 / area_per_site)

    num_sites_coverage = calculate_number_of_sites(area_km2, coverage_radius_km)

    # Site throughput estimation (FDD, 100 MHz BW)
    def calculate_site_throughput(scaling):
        return 1e6 * 1 * 4 * scaling * 100 * 12 * 0.5 * 0.9 * (1 - 0.05)  # bps

    site_throughput_bps = calculate_site_throughput(scaling_factor)

    # Capacity calculation
    active_users = population * (penetration_rate / 100) * 0.8 * 1  # 80% share, 1 BHAU
    traffic_per_user = 2e6  # 2 Mbps per user
    required_capacity = active_users * traffic_per_user

    # Calculate the number of sites based on required capacity
    def calculate_capacity_sites(required_capacity, site_throughput_bps):
        return math.ceil(required_capacity / site_throughput_bps)

    num_sites_capacity = calculate_capacity_sites(required_capacity, site_throughput_bps)

    # Display results after form submission
    st.markdown("### 🧮 Results")
    st.write(f"📍 **Location:** {country} > {city} > {area}")
    st.write(f"📏 **Area to Cover:** {area_km2} km²")
    st.write(f"📡 **Estimated Coverage Radius per Site:** {coverage_radius_km:.2f} km")
    st.write(f"📏 **Ideal Inter-site Distance (ISD):** {coverage_radius_km * 2:.2f} km")
    st.write(f"🗼 **Number of Sites Needed for Coverage:** {num_sites_coverage}")
    st.write(f"📶 **Estimated Site Throughput:** {site_throughput_bps / 1e6:.2f} Mbps")
    st.write(f"👥 **Active 5G Users:** {int(active_users)}")
    st.write(f"🗼 **Number of Sites Needed for Capacity:** {num_sites_capacity}")

