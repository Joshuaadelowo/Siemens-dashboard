import json
from pathlib import Path
import matplotlib.pyplot as plt
import matplotlib.ticker as ticker
import numpy as np

# 1. Carbon Conversion Factors (Approximate kg CO2e per unit)
FACTOR_ELEC = 0.207
FACTOR_GAS = 0.183
FACTOR_WATER = 0.344

# 2. Load the JSON data
json_path = Path(__file__).resolve().parent / "siemens_data.json"
with open(json_path, "r", encoding="utf-8") as f:
    data = json.load(f)

# 3. Extract the comprehensive data
dates, elec_kwh, gas_kwh, water_m3 = [], [], [], []

for view in data.get("views", []):
    if view.get("viewId") == 157:
        dates = view["data"][0]
        gas_kwh = view["data"][2]   # FuelsDH_Total
        elec_kwh = view["data"][3]  # EL_Total
        water_m3 = view["data"][4]  # UtilityWater
        break

short_dates = [d.split(" ")[0] for d in dates]

# 4. Calculate TOTAL Carbon (Tonnes) per month
total_carbon = []
for i in range(len(short_dates)):
    elec_c = (elec_kwh[i] * FACTOR_ELEC) / 1000
    gas_c = (gas_kwh[i] * FACTOR_GAS) / 1000
    water_c = (water_m3[i] * FACTOR_WATER) / 1000
    total_carbon.append(elec_c + gas_c + water_c)

# 5. Build the "Punchy" Line Graph
fig, ax = plt.subplots(figsize=(12, 6), facecolor="#1E1E1E") # Dark mode background
ax.set_facecolor("#1E1E1E")

# The Actual Usage Line (Thick, bright neon blue with large hover markers)
ax.plot(short_dates, total_carbon, color="#00E5FF", linewidth=4, 
        marker="o", markersize=10, markerfacecolor="#FFFFFF", 
        markeredgewidth=2, label="Actual Campus Emissions")

# The Target Line (Dotted, bright yellow)
target_line = np.linspace(70, 50, len(short_dates))
ax.plot(short_dates, target_line, color="#FFEA00", linestyle="--", 
        linewidth=3, label="Interim 2030 Target")

# 6. Formatting for Maximum Readability
ax.set_title("Total Campus Carbon Footprint (Tonnes CO2e)", color="white", fontsize=16, fontweight="bold", pad=20)

# Clean up axes and text for dark mode
ax.tick_params(colors="white", labelsize=11)
plt.xticks(rotation=45)
ax.yaxis.set_major_formatter(ticker.FuncFormatter(lambda x, p: f"{int(x)}t"))

# Minimalist grid and legend
ax.grid(axis="y", color="#444444", linestyle="-", linewidth=0.5)
ax.spines['top'].set_visible(False)
ax.spines['right'].set_visible(False)
ax.spines['left'].set_color('#444444')
ax.spines['bottom'].set_color('#444444')

legend = ax.legend(loc="upper right", frameon=True, facecolor="#333333", edgecolor="none")
for text in legend.get_texts():
    text.set_color("white")

plt.tight_layout()
plt.show()