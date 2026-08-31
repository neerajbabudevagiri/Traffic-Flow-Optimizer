import os
import sys
import traci
from collections import defaultdict, deque
from csv import DictWriter

# Configurable step interval (seconds)
step_interval = 1  # ← change this to 10, 15, etc. for slower stepping

# Prepare CSV
output_file = ""
write_header = not os.path.exists(output_file) 

# SUMO setup
if "SUMO_HOME" in os.environ:
    tools = os.path.join(os.environ["SUMO_HOME"], "tools")
    sys.path.append(tools)
else:
    sys.exit("❌ Please set the 'SUMO_HOME' environment variable.")

# Start SUMO with GUI
sumo_cmd = ["sumo-gui", "-c", "network.sumocfg", "--step-length", "10"]
traci.start(sumo_cmd)

# Buffers
previous_vehicles_on_lane = defaultdict(set)
entry_times = defaultdict(deque)
exit_times = defaultdict(deque)
lane_data_buffer = defaultdict(deque)

with open(output_file, mode='a', newline='') as csvfile:
    fieldnames = ["time", "lane_id", "density", "entering_rate", "exit_rate", "vehicle_count", "congested"]
    writer = DictWriter(csvfile, fieldnames=fieldnames)

    if write_header:
        writer.writeheader()
        csvfile.flush()

    current_time = 0
    while traci.simulation.getMinExpectedNumber() > 0:
        traci.simulationStep(current_time)

        for lane_id in traci.lane.getIDList():
            if lane_id.startswith(":"):
                continue

            lane_length = traci.lane.getLength(lane_id)
            current_vehicle_ids = set(traci.lane.getLastStepVehicleIDs(lane_id))

            prev_vehicle_ids = previous_vehicles_on_lane[lane_id]
            entered = current_vehicle_ids - prev_vehicle_ids
            exited = prev_vehicle_ids - current_vehicle_ids
            previous_vehicles_on_lane[lane_id] = current_vehicle_ids

            for _ in entered:
                entry_times[lane_id].append(current_time)
            for _ in exited:
                exit_times[lane_id].append(current_time)

            while entry_times[lane_id] and entry_times[lane_id][0] <= current_time - 60:
                entry_times[lane_id].popleft()
            while exit_times[lane_id] and exit_times[lane_id][0] <= current_time - 60:
                exit_times[lane_id].popleft()

            entering_rate = len(entry_times[lane_id])
            exit_rate = len(exit_times[lane_id])
            density = traci.lane.getLastStepOccupancy(lane_id)
            vehicle_count = traci.lane.getLastStepVehicleNumber(lane_id)

            lane_data_buffer[lane_id].append((
                current_time, density, entering_rate, exit_rate, vehicle_count
            ))

            while lane_data_buffer[lane_id] and lane_data_buffer[lane_id][0][0] <= current_time - 60:
                old_time, old_density, old_in_rate, old_out_rate, old_count = lane_data_buffer[lane_id].popleft()

                if old_density > 0.55:
                    continue

                congested = 1 if density > 0.5 else 0

                writer.writerow({
                    "time": old_time,
                    "lane_id": lane_id,
                    "density": old_density,
                    "entering_rate": old_in_rate,
                    "exit_rate": old_out_rate,
                    "vehicle_count": old_count,
                    "congested": congested
                })
                csvfile.flush()

        # Step ahead by your custom interval
        current_time += step_interval

traci.close()
print(f"✅ Dataset created using {step_interval}s intervals.")
