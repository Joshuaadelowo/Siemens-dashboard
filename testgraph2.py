import json
from pathlib import Path
import matplotlib.pyplot as plt
import matplotlib.ticker as ticker

# 1. Average UK 2-Bed Home Monthly Electricity Consumption (in kWh)
TWO_BED_HOME_MONTHLY_KWH = 150

# 2. Load the JSON data
json_path = Path(__file__).resolve().parent / "siemens_data.json"
with open(json_path, "r", encoding="utf-8") as f:
    data = json.load(f)

# 3. Extract the electricity data
dates = []
electricity_values = []

# View 159 contains the Electricity data
for view in data.get("views", []):
    if view.get("viewId") == 159:
        dates = view["data"][0]
        electricity_values = view["data"][2]
        break

# Clean the date formatting for the X-axis
short_dates = [d.split(" ")[0] for d in dates]

# 4. Convert Campus kWh to 2-Bed Homes Powered
homes_array = [val / TWO_BED_HOME_MONTHLY_KWH for val in electricity_values]

# 5. Build the Graphic
plt.figure(figsize=(10, 6))
# Changed the color to a nice architectural blue for the homes metric
plt.bar(short_dates, homes_array, color="#2B547E", edgecolor="#1C3854")

# Formatting the visual
plt.title("Campus Electricity Equivalency: UK 2-Bed Homes Powered", fontsize=14, fontweight="bold")
plt.xlabel("Month", fontsize=12)
plt.ylabel("Number of 2-Bed Homes", fontsize=12)
plt.xticks(rotation=45)

# Format the Y-axis to show commas for thousands
plt.gca().yaxis.set_major_formatter(ticker.FuncFormatter(lambda x, p: format(int(x), ',')))
plt.grid(axis="y", linestyle="--", alpha=0.7)
plt.tight_layout()

# Display the final graphic
print("Generating Power BI mockup graphic for 2-Bed Homes...")
plt.show()