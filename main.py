import os
import sys
import traci
import csv
import json
from get_max_vehicles import calculate_max_vehicles

# Initialize SUMO
if "SUMO_HOME" in os.environ:
    tools = os.path.join(os.environ["SUMO_HOME"], "tools")
    sys.path.append(tools)
else:
    sys.exit("Declare 'SUMO_HOME'!")

sumo_cmd = ["sumo-gui", "-c", "routes.sumocfg", "--step-length", "1"]
traci.start(sumo_cmd)

# Calculate lane capacities (EXCLUDING internal lanes)
lanes = traci.lane.getIDList()
lane_capacity = {
    lane: calculate_max_vehicles(lane)
    for lane in lanes
    if not lane.startswith(":")  # Skip internal lanes
}

# Save to CSV
with open('lane_capacities.csv', 'w', newline='') as csvfile:
    writer = csv.writer(csvfile)
    writer.writerow(["Lane ID", "Max Vehicles"])
    for lane, capacity in lane_capacity.items():
        writer.writerow([lane, capacity])

# Save to JSON (optional)
with open('lane_capacities.json', 'w') as jsonfile:
    json.dump(lane_capacity, jsonfile, indent=4)

print("Non-internal lane capacities saved to CSV and JSON!")

# Proceed with simulation...
try:
    while traci.simulation.getMinExpectedNumber() > 0:
        traci.simulationStep()
finally:
    traci.close()