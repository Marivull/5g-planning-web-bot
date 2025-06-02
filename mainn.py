import streamlit as st
from PIL import Image
import requests
from io import BytesIO
import math
import random

st.set_page_config(page_title="5G Site Estimator for Coverage & Capacity", layout="centered")

logo_url = "https://github.com/Marivull/5g-planning-web-bot/raw/main/logo.png"
response = requests.get(logo_url)
logo = Image.open(BytesIO(response.content))

st.image(logo, caption="5G Site Estimator Logo")
st.title("📡 5G Site Estimator for Coverage & Capacity")
st.markdown("""
**Misr University for Science and Technology**  
**College of Engineering**  
**Communication and Electronics Department**  
**5G Network Planning Project**
""")

st.sidebar.header("📥 Input Parameters")

city_areas = {
    "Cairo": {"Nasr City": "Urban", "Heliopolis": "Urban", "Maadi": "Urban", "Zamalek": "Urban"},
    "Giza": {"Dokki": "Urban", "Mohandessin": "Urban", "6th of October": "Urban", "Sheikh Zayed": "Urban"},
    "Alexandria": {"Stanley": "Dense Urban", "Sidi Gaber": "Urban", "Smouha": "Urban"},
}

city = st.sidebar.selectbox("Select City", list(city_areas.keys()))
area = st.sidebar.selectbox("Select Area", list(city_areas[city].keys()))
urban_type = city_areas[city][area]

area_km2 = st.sidebar.number_input("Area Size (km²)", min_value=0.1, value=0.1, step=0.1)
population = st.sidebar.number_input("Population", min_value=0, value=0, step=1000)
penetration_rate = st.sidebar.slider("5G Penetration Rate (%)", 0, 100, 0)
traffic_per_user = st.sidebar.number_input("Average Traffic per User (Mbps)", min_value=0.0, value=0.0, step=0.1)
antenna_type = st.sidebar.selectbox("Antenna Type", ["Directive", "Omni"])

st.sidebar.header("📶 Frequency Band")
band_option = st.sidebar.selectbox("Select 5G Frequency Band", [
    "Low-Band (e.g. 700 MHz)",
    "Mid-Band (e.g. 3.5 GHz)",
    "mmWave (e.g. 28 GHz)"
])

if band_option == "Low-Band (e.g. 700 MHz)":
    freq_mhz = 700
elif band_option == "Mid-Band (e.g. 3.5 GHz)":
    freq_mhz = 3500
else:
    freq_mhz = 28000

freq_ghz = freq_mhz / 1000

st.sidebar.header("📡 Link Budget Parameters")
use_custom_link_budget = st.sidebar.checkbox("Customize Link Budget Parameters", value=False)

if use_custom_link_budget:
    tx_power = st.sidebar.number_input("Tx Power (dBm)", value=49)
    tx_gain = st.sidebar.number_input("Tx Antenna Gain (dBi)", value=24)
    cable_loss = st.sidebar.number_input("Cable Loss (dB)", value=0)
    penetration_loss = st.sidebar.number_input("Penetration Loss (dB)", value=22)
    foliage_loss = st.sidebar.number_input("Foliage Loss (dB)", value=7.5)
    body_loss = st.sidebar.number_input("Body Loss (dB)", value=3)
    interference_margin = st.sidebar.number_input("Interference Margin (dB)", value=6)
    rain_margin = st.sidebar.number_input("Rain Margin (dB)", value=0)
    shadow_margin = st.sidebar.number_input("Shadow Margin (dB)", value=6)
    rx_gain = st.sidebar.number_input("Rx Antenna Gain (dBi)", value=0)
    noise_figure = st.sidebar.number_input("Receiver Noise Figure (dB)", value=9)
    required_sinr = st.sidebar.number_input("Required SINR (dB)", value=14)
else:
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

st.sidebar.header("⚙️ Capacity Parameters")
bandwidth_mhz = int(st.sidebar.selectbox("Bandwidth (MHz)", options=[10, 20, 40, 60, 80, 100], index=3))
mod_order = st.sidebar.selectbox("Modulation Order (bits per symbol)", options=[2, 4, 6, 8, 10], index=3)
mimo_layers = st.sidebar.slider("Number of MIMO Layers", min_value=1, max_value=16, value=1)
utilization = st.sidebar.slider("Resource Utilization (%)", min_value=0, max_value=100, value=0) / 100.0
overhead = st.sidebar.slider("Overhead (%)", min_value=0, max_value=100, value=0) / 100.0
sectors_per_site = st.sidebar.selectbox("Sectors per Site", options=[1, 3], index=1)

duplex_mode = st.sidebar.selectbox("Duplex Mode", ["TDD", "FDD"], index=0)
if duplex_mode == "FDD":
    overhead = min(overhead, 0.12)

propagation_model = st.sidebar.selectbox("Select Propagation Model", ["UMi-Street Canyon", "UMa"])

rb_table = {10: 52, 20: 106, 40: 217, 60: 326, 80: 435, 100: 546}
n_rb = rb_table.get(bandwidth_mhz, 217)
bandwidth_hz = bandwidth_mhz * 1e6

def pl_umi(d_m, f_ghz, h_ue=1.5):
    d_km = d_m / 1000.0
    p_los = min(18/d_km, 1) * (1 - math.exp(-d_km/36)) + math.exp(-d_km/36)
    is_los = random.random() < p_los
    if is_los:
        pl = 32.4 + 21 * math.log10(d_m) + 20 * math.log10(f_ghz)
    else:
        pl_los = 32.4 + 21 * math.log10(d_m) + 20 * math.log10(f_ghz)
        pl_nlos = 22.4 + 35.3 * math.log10(d_m) + 21.3 * math.log10(f_ghz) - 0.3 * (h_ue - 1.5)
        pl = max(pl_los, pl_nlos)
    return pl

def pl_uma(d_m, f_ghz, h_ue=1.5):
    d_km = d_m / 1000.0
    p_los = min(18/d_km, 1) * (1 - math.exp(-d_km/63)) + math.exp(-d_km/63)
    is_los = random.random() < p_los
    if is_los:
        pl = 28 + 22 * math.log10(d_m) + 20 * math.log10(f_ghz)
    else:
        pl_los = 28 + 22 * math.log10(d_m) + 20 * math.log10(f_ghz)
        pl_nlos = 13.54 + 39.08 * math.log10(d_m) + 20 * math.log10(f_ghz) - 0.6 * (h_ue - 1.5)
        pl = max(pl_los, pl_nlos)
    return pl

def find_coverage_radius(link_budget_margin, f_ghz, model_func, max_radius_km=0.7, h_ue=1.5):
    low = 1.0
    high = max_radius_km * 1000
    for _ in range(30):
        mid = (low + high) / 2
        pl = model_func(mid, f_ghz, h_ue)
        if pl > link_budget_margin:
            high = mid
        else:
            low = mid
    return low / 1000.0

if st.button("🚀 Show Results"):
    thermal_noise = -174 + 10 * math.log10(bandwidth_hz)
    receiver_sensitivity = thermal_noise + noise_figure + required_sinr

    mapl = (tx_power + tx_gain + rx_gain - cable_loss - penetration_loss - foliage_loss - body_loss
            - interference_margin - rain_margin - shadow_margin - receiver_sensitivity)

    model_func = pl_umi if propagation_model == "UMi-Street Canyon" else pl_uma
    coverage_radius_km = find_coverage_radius(mapl, freq_ghz, model_func)
    coverage_radius_km *= 1.0 if antenna_type == "Directive" else 1.2
    a_site = (1.94 if antenna_type == "Directive" else 2.5) * coverage_radius_km ** 2
    num_sites_coverage = math.ceil(area_km2 / a_site)

    active_users = population * (penetration_rate / 100)
    total_traffic_mbps = active_users * traffic_per_user

    bps_per_sector = (
        n_rb * 12 * 14 * 1000 * mod_order * 0.93 * mimo_layers * utilization * (1 - overhead)
    )
    site_throughput_mbps = (bps_per_sector * sectors_per_site) / 1e6
    num_sites_capacity = math.ceil(total_traffic_mbps / site_throughput_mbps) if site_throughput_mbps > 0 else 0
    total_sites_required = max(num_sites_coverage, num_sites_capacity)

    st.header("📊 Results")
    st.write(f"Propagation Model: {propagation_model}")
    st.write(f"Coverage Radius per Site: {coverage_radius_km:.3f} km")
    st.write(f"Area per Site: {a_site:.3f} km²")
    st.write(f"Number of Sites Needed for Coverage: {num_sites_coverage}")
    st.write(f"Active Users (Busy Hour): {int(active_users)}")
    st.write(f"Total Traffic Demand: {total_traffic_mbps:.0f} Mbps")
    st.write(f"Site Throughput: {site_throughput_mbps:.0f} Mbps")
    st.write(f"Number of Sites Needed for Capacity: {num_sites_capacity}")
    st.markdown("### 🔍 Final Recommendation")
    st.write(f"Total Sites Required: {total_sites_required}")

