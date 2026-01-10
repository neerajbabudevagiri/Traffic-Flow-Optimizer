import os
import sys
import traci

# Step 1: Establish path to SUMO (SUMO_HOME)
if 'SUMO_HOME' in os.environ:
    tools = os.path.join(os.environ['SUMO_HOME'], 'tools')
    sys.path.append(tools)
else:
    sys.exit("Please declare environment variable 'SUMO_HOME'")

# Step 2: Define SUMO configuration
Sumo_config = [
    'sumo-gui',
    '-c', 'routes.sumocfg',
    '--step-length', '5',
    '--delay', '0',
    '--lateral-resolution', '0.1'
]

# Step 3: Open connection between SUMO and TraCI
traci.start(Sumo_config)

# Step 4: Get all roads (edges) in the network
road_ids = traci.edge.getIDList()
total_roads = len(road_ids)
print(f"Total number of roads {total_roads}")

# Step 5: Create a dictionary to store density for each road
road_density = {}

# Step 6: Simulation loop to calculate road density
while traci.simulation.getMinExpectedNumber() > 0:
    traci.simulationStep()  # Move simulation forward 1 step

    for road in road_ids:
        vehicle_count = traci.edge.getLastStepVehicleNumber(road)  # Vehicles on this road
        lane_count = traci.edge.getLaneNumber(road)  # Get lane count

        if lane_count > 0:
            lane_id = f"{road}_0"  # Use only the first lane

            try:
                road_length = traci.lane.getLength(lane_id)  # Get road length
                density = vehicle_count / road_length if road_length > 0 else 0
                road_density[road] = density

            except traci.exceptions.TraCIException:
                print(f"Warning  Edge {road} has no valid lane. Skipping...")

# Step 7: Print road density
print("\nRoad Density (vehicles per meter) ")
for road, density in road_density.items():
    print(f"Road {road} {density:.4f} vehicles/m")

# Step 8: Close SUMO connection
traci.close()
