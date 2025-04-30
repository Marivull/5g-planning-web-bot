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

# Display the logo with text at top of main page
st.image(logo, caption="5G Site Estimator Logo")
st.title("📡 5G Site Estimator for Coverage & Capacity")
st.markdown("""
    **Misr University for Science and Technology**  
    **College of Engineering**  
    **Communication and Electronics Department**  
    **5G Network Planning Project**
""")

# Sidebar inputs
st.sidebar.header("📥 Input Parameters")

city_areas = {
    "Cairo": {"Nasr City": "Urban", "Heliopolis": "Urban", "Maadi": "Urban", "Zamalek": "Urban"},
    "Giza": {"Dokki": "Urban", "Mohandessin": "Urban", "6th of October": "Urban", "Sheikh Zayed": "Urban"},
    "Alexandria": {"Stanley": "Dense Urban", "Sidi Gaber": "Urban", "Smouha": "Urban"},
 
}

city = st.sidebar.selectbox("Select City", list(city_areas.keys()))
area = st.sidebar.selectbox("Select Area", list(city_areas[city].keys()))
urban_type = city_areas[city][area]

area_km2 = st.sidebar.number_input("Area Size (km²)", min_value=0.1, value=5.0, step=0.1)
population = st.sidebar.number_input("Population", min_value=100, value=218000, step=1000)
penetration_rate = st.sidebar.slider("5G Penetration Rate (%)", 0, 100, 15)
traffic_per_user = st.sidebar.number_input("Average Traffic per User (Mbps)", min_value=0.1, value=2.0, step=0.1)
antenna_type = st.sidebar.selectbox("Antenna Type", ["Directive", "Omni"])

st.sidebar.header("⚙️ Capacity Parameters")

bandwidth_mhz = st.sidebar.selectbox("Bandwidth (MHz)", options=[10, 20, 40, 60, 80, 100], index=3)
mod_order = st.sidebar.selectbox("Modulation Order (bits per symbol)", options=[2, 4, 6, 8, 10], index=3)
mimo_layers = st.sidebar.slider("Number of MIMO Layers", min_value=1, max_value=16, value=8)
utilization = st.sidebar.slider("Resource Utilization (%)", min_value=10, max_value=100, value=70) / 100.0
overhead = st.sidebar.slider("Overhead (%)", min_value=5, max_value=30, value=14) / 100.0
sectors_per_site = st.sidebar.selectbox("Sectors per Site", options=[1, 3], index=1)

duplex_mode = st.sidebar.selectbox("Duplex Mode", ["TDD", "FDD"], index=0)
if duplex_mode == "FDD":
    overhead = min(overhead, 0.12)  # usually lower overhead in FDD

# Band parameters for coverage calculation
if bandwidth_mhz == 10:
    n_rb = 52
elif bandwidth_mhz == 20:
    n_rb = 106
elif bandwidth_mhz == 40:
    n_rb = 217
elif bandwidth_mhz == 60:
    n_rb = 326
elif bandwidth_mhz == 80:
    n_rb = 435
elif bandwidth_mhz == 100:
    n_rb = 546
else:
    n_rb = 217  # default 40 MHz

bandwidth_hz = bandwidth_mhz * 1e6

# Show results after button press
if st.button("🚀 Show Results"):
    # Link budget parameters (fixed)
    tx_power = 49
    tx_gain = 24
    cable_loss = 0
    penetration_loss = 22
    foliage_loss = 7.5
    body_loss = 3
    interference_margin = 6
    rain_margin = 0
    shadow_margin = 6
    rx_gain = 0
    noise_figure = 9
    required_sinr = 14

    freq_mhz = 3500
    pl0 = 32.4
    n = 3.3

    thermal_noise = -174 + 10 * math.log10(bandwidth_hz)
    receiver_sensitivity = thermal_noise + noise_figure + required_sinr
    mapl = (tx_power + tx_gain + rx_gain - cable_loss - penetration_loss - foliage_loss - body_loss
            - interference_margin - rain_margin - shadow_margin - receiver_sensitivity)
    numerator = mapl - pl0 - 20 * math.log10(freq_mhz)
    denominator = 10 * n
    r_km = 10 ** (numerator / denominator)
    max_radius = 0.7
    r_km = min(max(r_km, 0.05), max_radius)
    coverage_radius_km = r_km * (1.0 if antenna_type == "Directive" else 1.2)
    a_site = (1.94 if antenna_type == "Directive" else 2.5) * coverage_radius_km ** 2
    num_sites_coverage = math.ceil(area_km2 / a_site)

    active_users = population * (penetration_rate / 100)
    total_traffic_mbps = active_users * traffic_per_user

    subcarriers_per_rb = 12
    symbols_per_slot = 14
    slots_per_sec = 1000
    coding_rate = 0.93

    bps_per_sector = (
        n_rb * subcarriers_per_rb * symbols_per_slot * slots_per_sec *
        mod_order * coding_rate * mimo_layers * utilization * (1 - overhead)
    )

    site_throughput_bps = bps_per_sector * sectors_per_site
    site_throughput_mbps = site_throughput_bps / 1e6

    num_sites_capacity = math.ceil(total_traffic_mbps / site_throughput_mbps)
    total_sites_required = max(num_sites_coverage, num_sites_capacity)

    st.header("📊 Results")
    st.write(f"Coverage Radius per Site (R): {coverage_radius_km:.3f} km")
    st.write(f"Area per Site: {a_site:.3f} km²")
    st.write(f"Number of Sites Needed for Coverage: {num_sites_coverage}")
    st.write(f"Active Users (Busy Hour): {int(active_users)}")
    st.write(f"Total Traffic Demand: {total_traffic_mbps:.0f} Mbps")
    st.write(f"Site Throughput: {site_throughput_mbps:.0f} Mbps")
    st.write(f"Number of Sites Needed for Capacity: {num_sites_capacity}")
    st.markdown("### 🔍 Final Recommendation")
    st.write(f"Total Sites Required (Max of Coverage and Capacity): {total_sites_required}")
