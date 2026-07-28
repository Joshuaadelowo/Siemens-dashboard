import json
from pathlib import Path
import matplotlib.pyplot as plt

# 1. Load the local JSON file
json_path = Path(__file__).resolve().parent / "siemens_data.json"
with open(json_path, "r", encoding="utf-8") as f:
    data = json.load(f)

# 2. Extract the data arrays from the Electricity view (viewId 159)
# We navigate to the views list, find the electricity view, and pull its arrays
electricity_view = None
for view in data.get("views", []):
    if view.get("viewId") == 159:
        electricity_view = view
        break

if electricity_view:
    # Index 0 of 'data' contains the dates
    # Index 2 of 'data' contains the EL_Single / EL_Total values in kWh
    dates = electricity_view["data"][0]
    electricity_values = electricity_view["data"][2]

    # Clean up the date strings slightly for better X-axis labels (e.g., "08/01/2025")
    short_dates = [d.split(" ")[0] for d in dates]

    # 3. Create the Bar Graph
    plt.figure(figsize=(12, 6))
    plt.bar(short_dates, electricity_values, color="#00A699", edgecolor="black")

    # Add titles and labels
    plt.title("Docklands Campus - Monthly Electricity Consumption", fontsize=14, fontweight="bold")
    plt.xlabel("Date", fontsize=12)
    plt.ylabel("Electricity Consumption (kWh)", fontsize=12)
    plt.xticks(rotation=45)
    plt.grid(axis="y", linestyle="--", alpha=0.7)
    plt.tight_layout()

    # 4. Show the plot window
    print("Generating bar graph...")
    plt.show()
else:
    print("Error: Could not find the electricity view in the JSON structure.")