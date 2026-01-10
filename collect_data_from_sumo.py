import os
import sys
import traci
import pandas as pd
from csv import DictWriter
from collections import defaultdict, deque

# Prepare CSV
output_file = "traffic_training_data.csv"
write_header = not os.path.exists(output_file)

# SUMO setup
if "SUMO_HOME" in os.environ:
    tools = os.path.join(os.environ["SUMO_HOME"], "tools")
    sys.path.append(tools)
else:
    sys.exit("Declare 'SUMO_HOME'!")

sumo_cmd = ["sumo-gui", "-c", "copy6.sumocfg", "--step-length", "1"]
traci.start(sumo_cmd)

# Buffer to store past lane data
buffer = defaultdict(deque)  # lane_id -> deque of (time, density, speed_exit, vehicle_count)

# Start simulation
with open(output_file, mode='a', newline='') as csvfile:
    fieldnames = ["time", "lane_id", "density", "speed_exit", "vehicle_count", "congested"]
    writer = DictWriter(csvfile, fieldnames=fieldnames)
    if write_header:
        writer.writeheader()
        csvfile.flush()  # Ensure header is saved immediately

    while traci.simulation.getMinExpectedNumber() > 0:
        current_time = traci.simulation.getTime()
        traci.simulationStep()

        for lane_id in traci.lane.getIDList():
            if lane_id.startswith(":"):
                continue  # skip internal lanes

            lane_length = traci.lane.getLength(lane_id)
            vehicle_ids = traci.lane.getLastStepVehicleIDs(lane_id)

            speeds_near_exit = [
                traci.vehicle.getSpeed(veh_id)
                for veh_id in vehicle_ids
                if lane_length - traci.vehicle.getLanePosition(veh_id) <= 20
            ]
            speed_exit = sum(speeds_near_exit) / len(speeds_near_exit) if speeds_near_exit else 0
            density = traci.lane.getLastStepOccupancy(lane_id)
            vehicle_count = traci.lane.getLastStepVehicleNumber(lane_id)

            # Store current data in buffer
            buffer[lane_id].append((current_time, density, speed_exit, vehicle_count))

            # Check if we have old data from 30 seconds ago
            while buffer[lane_id] and buffer[lane_id][0][0] <= current_time - 30:
                old_time, old_density, old_speed, old_count = buffer[lane_id].popleft()
                
                # Define "congestion" based on current values (30s later)
                congested = 1 if density > 0.5 else 0

                # Write labeled old record
                writer.writerow({
                    "time": old_time,
                    "lane_id": lane_id,
                    "density": old_density,
                    "speed_exit": old_speed,
                    "vehicle_count": old_count,
                    "congested": congested
                })
                csvfile.flush()  # ✅ Write immediately

traci.close()
print("✅ Labeled CSV created with 30s future congestion evaluation and live saving.")
