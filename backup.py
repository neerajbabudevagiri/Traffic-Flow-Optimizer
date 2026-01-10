# # # # #program of trafiic light setting based on the vehicle counts of lane 

# # # # # import os
# # # # # import sys
# # # # # import traci

# # # # # # Initialize SUMO
# # # # # if "SUMO_HOME" in os.environ:
# # # # #     tools = os.path.join(os.environ["SUMO_HOME"], "tools")
# # # # #     sys.path.append(tools)
# # # # # else:
# # # # #     sys.exit("Please declare environment variable 'SUMO_HOME'")

# # # # # # Define SUMO configuration
# # # # # sumo_cmd = ["sumo-gui", "-c", "routes.sumocfg", "--step-length", "1"]
# # # # # traci.start(sumo_cmd)

# # # # # # Store the last phase to prevent duplicate updates
# # # # # previous_phase = {}

# # # # # def adjust_traffic_lights(tl):
# # # # #     global previous_phase

# # # # #     # Get current phase and total number of phases
# # # # #     current_phase = traci.trafficlight.getPhase(tl)
# # # # #     num_phases = len(traci.trafficlight.getAllProgramLogics(tl)[0].phases)

# # # # #     # Check if a **full cycle has completed**
# # # # #     if tl in previous_phase and previous_phase[tl] > current_phase:
# # # # #         logic = traci.trafficlight.getAllProgramLogics(tl)[0]
# # # # #         phases = logic.phases
# # # # #         controlled_lanes = traci.trafficlight.getControlledLanes(tl)

# # # # #         print(logic)
# # # # #         print("\n")
# # # # #         print(phases)
# # # # #         print("\n")
# # # # #         print(controlled_lanes)
# # # # #         print("\n ------------------")

# # # # #         # **Step 1: Remove Duplicate Lanes**
# # # # #         unique_lanes = list(dict.fromkeys(controlled_lanes))  # Keeps order, removes duplicates

# # # # #         # Get vehicle counts per lane
# # # # #         lane_vehicle_counts = {lane: traci.lane.getLastStepVehicleNumber(lane) for lane in unique_lanes}
# # # # #         print("lane vehicle counts ", lane_vehicle_counts)
# # # # #         total_vehicles = sum(lane_vehicle_counts.values())
# # # # #         print("total vehicles ", total_vehicles)

# # # # #         # Base timings
# # # # #         min_green_time = 10
# # # # #         total_cycle_time = 100
# # # # #         remaining_time = total_cycle_time - (min_green_time * num_phases)
# # # # #         print("remaining time ", remaining_time)

# # # # #         # Allocate extra time based on vehicle count
# # # # #         extra_time_per_lane = {lane: 0 for lane in unique_lanes}
# # # # #         if total_vehicles > 0:
# # # # #             for lane, count in lane_vehicle_counts.items():
# # # # #                 print("lane ", lane, "count ", count)
# # # # #                 extra_time_per_lane[lane] = (count / total_vehicles) * remaining_time
# # # # #                 print(f"extra time per lane {lane} is {extra_time_per_lane[lane]}")
        
# # # # #         # **Step 2: Create New Phase Logic**
# # # # #         updated_phases = []
# # # # #         for i, phase in enumerate(phases):
# # # # #             if "g" in phase.state:  # ✅ Fix: Match lowercase 'g' in phase states
# # # # #                 lane = unique_lanes[i] if i < len(unique_lanes) else None
# # # # #                 new_duration = min_green_time + extra_time_per_lane.get(lane, 0) if lane else phase.duration
# # # # #             else:
# # # # #                 new_duration = phase.duration  # Keep red/yellow phases unchanged

# # # # #             updated_phases.append(traci.trafficlight.Phase(new_duration, phase.state))

# # # # #         # **Step 3: Apply Updated Logic**
# # # # #         new_logic = traci.trafficlight.Logic(logic.programID, 0, 0, updated_phases)
# # # # #         traci.trafficlight.setProgramLogic(tl, new_logic)  # ✅ Correct way to apply changes
# # # # #         traci.trafficlight.setPhase(tl, 0)  # ✅ Immediately reset to Phase 0

# # # # #         print(f"Updated timings for {tl}")

# # # # #     # Store phase for next iteration
# # # # #     previous_phase[tl] = current_phase


# # # # # # Simulation loop
# # # # # while traci.simulation.getMinExpectedNumber() > 0:
# # # # #     traci.simulationStep()

# # # # #     # Check all traffic lights
# # # # #     for tl in traci.trafficlight.getIDList():
# # # # #         adjust_traffic_lights(tl)

# # # # # # Close SUMO
# # # # # traci.close()

  

# # # #time claculated infront of traffic light

# # # # import os
# # # # import sys
# # # # import traci

# # # # # Initialize SUMO
# # # # if "SUMO_HOME" in os.environ:
# # # #     tools = os.path.join(os.environ["SUMO_HOME"], "tools")
# # # #     sys.path.append(tools)
# # # # else:
# # # #     sys.exit("Please declare environment variable 'SUMO_HOME'")

# # # # # Define SUMO configuration
# # # # sumo_cmd = ["sumo-gui", "-c", "routes.sumocfg", "--step-length", "1"]
# # # # traci.start(sumo_cmd)

# # # # # Store the last phase to prevent duplicate updates
# # # # previous_phase = {}

# # # # def adjust_traffic_lights(tl):
# # # #     global previous_phase

# # # #     # Get current phase and total number of phases
# # # #     current_phase = traci.trafficlight.getPhase(tl)
# # # #     num_phases = len(traci.trafficlight.getAllProgramLogics(tl)[0].phases)

# # # #     # Check if a **full cycle has completed**
# # # #     if tl in previous_phase and previous_phase[tl] > current_phase:
# # # #         logic = traci.trafficlight.getAllProgramLogics(tl)[0]
# # # #         phases = logic.phases
# # # #         controlled_lanes = traci.trafficlight.getControlledLanes(tl)

# # # #         print(logic)
# # # #         print("\n")
# # # #         print(phases)
# # # #         print("\n")
# # # #         print(controlled_lanes)
# # # #         print("\n ------------------")

# # # #         # **Step 1: Remove Duplicate Lanes**
# # # #         unique_lanes = list(dict.fromkeys(controlled_lanes))  # Keeps order, removes duplicates

# # # #         # Only count vehicles close to the junction
# # # #         distance_threshold = 150 # meters near the stop line
# # # #         lane_vehicle_counts = {}

# # # #         for lane in unique_lanes:
# # # #             vehicle_ids = traci.lane.getLastStepVehicleIDs(lane)
# # # #             count_near = 0
# # # #             lane_length = traci.lane.getLength(lane)

# # # #             for veh_id in vehicle_ids:
# # # #                 pos = traci.vehicle.getLanePosition(veh_id)
# # # #                 distance_to_tls = lane_length - pos
# # # #                 if distance_to_tls <= distance_threshold:
# # # #                     count_near += 1

# # # #             lane_vehicle_counts[lane] = count_near

# # # #         print("lane vehicle counts ", lane_vehicle_counts)
# # # #         total_vehicles = sum(lane_vehicle_counts.values())
# # # #         print("total vehicles ", total_vehicles)

# # # #         # Base timings
# # # #         min_green_time = 10
# # # #         total_cycle_time = 100
# # # #         remaining_time = total_cycle_time - (min_green_time * num_phases)
# # # #         print("remaining time ", remaining_time)

# # # #         # Allocate extra time based on vehicle count
# # # #         extra_time_per_lane = {lane: 0 for lane in unique_lanes}
# # # #         if total_vehicles > 0:
# # # #             for lane, count in lane_vehicle_counts.items():
# # # #                 print("lane ", lane, "count ", count)
# # # #                 extra_time_per_lane[lane] = (count / total_vehicles) * remaining_time
# # # #                 print(f"extra time per lane {lane} is {extra_time_per_lane[lane]}")

# # # #         # **Step 2: Create New Phase Logic**
# # # #         updated_phases = []
# # # #         for i, phase in enumerate(phases):
# # # #             if "g" in phase.state:  # ✅ lowercase 'g'
# # # #                 lane = unique_lanes[i] if i < len(unique_lanes) else None
# # # #                 new_duration = min_green_time + extra_time_per_lane.get(lane, 0) if lane else phase.duration
# # # #             else:
# # # #                 new_duration = phase.duration  # Keep red/yellow phases unchanged

# # # #             updated_phases.append(traci.trafficlight.Phase(new_duration, phase.state))

# # # #         # **Step 3: Apply Updated Logic**
# # # #         new_logic = traci.trafficlight.Logic(logic.programID, 0, 0, updated_phases)
# # # #         traci.trafficlight.setProgramLogic(tl, new_logic)
# # # #         traci.trafficlight.setPhase(tl, 0)  # Reset phase index

# # # #         print(f"Updated timings for {tl}")

# # # #     # Store phase for next iteration
# # # #     previous_phase[tl] = current_phase

# # # # # Simulation loop
# # # # while traci.simulation.getMinExpectedNumber() > 0:
# # # #     traci.simulationStep()

# # # #     # Check all traffic lights
# # # #     for tl in traci.trafficlight.getIDList():
# # # #         adjust_traffic_lights(tl)

# # # # # Close SUMO
# # # # traci.close()


# # flow


# # # <?xml version="1.0" encoding="UTF-8"?>

# # # <!-- generated on 2025-04-02 22:40:42 by Eclipse SUMO netedit Version 1.22.0
# # # -->

# # # <routes xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" xsi:noNamespaceSchemaLocation="http://sumo.dlr.de/xsd/routes_file.xsd">
# # #     <!-- Vehicles, persons and containers (sorted by depart) -->
# # #     <flow id="f_0" begin="0.00" fromJunction="1914" toJunction="1" end="100.00" vehsPerHour="1000"/>
# # #     <flow id="f_1" begin="0.00" fromJunction="130" toJunction="1993" end="100.00" vehsPerHour="500"/>
# # # </routes>


# # import os
# # import sys
# # import traci
# # import pandas as pd
# # from csv import DictWriter

# # # Prepare CSV file
# # output_file = "traffic_training_data.csv"
# # write_header = not os.path.exists(output_file)  # Only write header if file is new

# # # Set up SUMO environment
# # if "SUMO_HOME" in os.environ:
# #     tools = os.path.join(os.environ["SUMO_HOME"], "tools")
# #     sys.path.append(tools)
# # else:
# #     sys.exit("Declare 'SUMO_HOME'!")

# # sumo_cmd = ["sumo-gui", "-c", "copy6.sumocfg", "--step-length", "1"]
# # traci.start(sumo_cmd)

# # # Open file in append mode
# # with open(output_file, mode='a', newline='') as csvfile:
# #     fieldnames = ["time", "lane_id", "density", "speed_exit", "vehicle_count", "congested"]
# #     writer = DictWriter(csvfile, fieldnames=fieldnames)

# #     if write_header:
# #         writer.writeheader()

# #     # Run the SUMO simulation
# #     while traci.simulation.getMinExpectedNumber() > 0:
# #         traci.simulationStep()

# #         for lane_id in traci.lane.getIDList():
# #             if not lane_id.startswith(":"):  # Skip internal lanes
# #                 lane_length = traci.lane.getLength(lane_id)
# #                 vehicle_ids = traci.lane.getLastStepVehicleIDs(lane_id)

# #                 speeds_near_exit = []
# #                 for veh_id in vehicle_ids:
# #                     pos = traci.vehicle.getLanePosition(veh_id)
# #                     if lane_length - pos <= 20:  # Last 20 meters
# #                         speed = traci.vehicle.getSpeed(veh_id)
# #                         speeds_near_exit.append(speed)

# #                 exit_speed = sum(speeds_near_exit) / len(speeds_near_exit) if speeds_near_exit else 0
# #                 density = traci.lane.getLastStepOccupancy(lane_id)
# #                 vehicle_count = traci.lane.getLastStepVehicleNumber(lane_id)

# #                 print(f"[{lane_id}] Exit Speed: {exit_speed:.2f}, Density: {density:.2f}, Vehicles: {vehicle_count}")

# #                 writer.writerow({
# #                     "time": traci.simulation.getTime(),
# #                     "lane_id": lane_id,
# #                     "density": density,
# #                     "speed_exit": exit_speed,
# #                     "vehicle_count": vehicle_count,
# #                     "congested": 1 if True and density > 0.5 else 0
# #                 })

# # traci.close()
# # print("✅ CSV saved incrementally during simulation.")




# import os
# import sys
# import traci
# import math

# # Initialize SUMO
# if "SUMO_HOME" in os.environ:
#     tools = os.path.join(os.environ["SUMO_HOME"], "tools")
#     sys.path.append(tools)
# else:
#     sys.exit("Please declare environment variable 'SUMO_HOME'")

# # Define SUMO configuration
# sumo_cmd = ["sumo-gui", "-c", "routes.sumocfg", "--step-length", "1"]
# traci.start(sumo_cmd)

# # Store the last phase to prevent duplicate updates
# previous_phase = {}

# # Dummy set of congested lanes for now (replace with real model later)
# congested_lanes = set(["lane1", "lane2"])

# def adjust_traffic_lights(tl):
#     global previous_phase

#     current_phase = traci.trafficlight.getPhase(tl)
#     num_phases = len(traci.trafficlight.getAllProgramLogics(tl)[0].phases)

#     if tl in previous_phase and previous_phase[tl] > current_phase:
#         logic = traci.trafficlight.getAllProgramLogics(tl)[0]
#         phases = logic.phases
#         controlled_lanes = traci.trafficlight.getControlledLanes(tl)

#         print(logic)
#         print("\n")
#         print(phases)
#         print("\n")
#         print(controlled_lanes)
#         print("\n ------------------")

#         unique_lanes = list(dict.fromkeys(controlled_lanes))
#         current_state = traci.trafficlight.getRedYellowGreenState(tl)

#         lane_phase_map = {lane: current_state[i] for i, lane in enumerate(unique_lanes)}

#         for lane, signal in lane_phase_map.items():
#             if signal.lower() != 'r':
#                 continue  # only consider red signal lanes

#             vehicle_ids = traci.lane.getLastStepVehicleIDs(lane)
#             lane_length = traci.lane.getLength(lane)

#             for veh_id in vehicle_ids:
#                 pos = traci.vehicle.getLanePosition(veh_id)
#                 distance_to_tls = lane_length - pos

#                 if distance_to_tls <= 20:  # Only vehicles near junction
#                     try:
#                         route = traci.vehicle.getRoute(veh_id)
#                         current_index = route.index(lane) if lane in route else 0
#                         remaining_route = route[current_index:]
#                     except ValueError:
#                         remaining_route = []

#                     # You should replace this with actual congestion prediction from your model
#                     will_be_congested = any(l in congested_lanes for l in remaining_route)

#                     if will_be_congested:
#                         print(f"🚧 Vehicle {veh_id} on {lane} rerouted due to predicted congestion")
#                         traci.vehicle.rerouteTraveltime(veh_id)

#         distance_threshold = math.inf
#         lane_vehicle_counts = {}

#         for lane in unique_lanes:
#             vehicle_ids = traci.lane.getLastStepVehicleIDs(lane)
#             count_near = 0
#             lane_length = traci.lane.getLength(lane)

#             for veh_id in vehicle_ids:
#                 pos = traci.vehicle.getLanePosition(veh_id)
#                 distance_to_tls = lane_length - pos
#                 print(veh_id, "    ", distance_to_tls)
#                 if distance_to_tls <= distance_threshold:
#                     count_near += 1

#             lane_vehicle_counts[lane] = count_near

#         print("lane vehicle counts ", lane_vehicle_counts)
#         total_vehicles = sum(lane_vehicle_counts.values())
#         print("total vehicles ", total_vehicles)

#         min_green_time = 5
#         total_cycle_time = 100
#         remaining_time = total_cycle_time - (min_green_time * num_phases)
#         print("remaining time ", remaining_time)

#         extra_time_per_lane = {lane: 0 for lane in unique_lanes}
#         if total_vehicles > 0:
#             for lane, count in lane_vehicle_counts.items():
#                 print("lane ", lane, "count ", count)
#                 extra_time_per_lane[lane] = (count / total_vehicles) * remaining_time
#                 print(f"extra time per lane {lane} is {extra_time_per_lane[lane]}")

#         flow_rate = 0.3  # vehicles per second

#         updated_phases = []
#         for i, phase in enumerate(phases):
#             if "g" in phase.state:
#                 lane = unique_lanes[i] if i < len(unique_lanes) else None
#                 count = lane_vehicle_counts.get(lane, 0)
#                 extra = extra_time_per_lane.get(lane, 0)

#                 expected_time = count / flow_rate if flow_rate > 0 else min_green_time
#                 if expected_time < min_green_time + extra:
#                     actual_time = max(min_green_time, expected_time)
#                 else:
#                     actual_time = min_green_time + extra

#                 print(f"Final green time for lane {lane} is {actual_time}")
#                 new_duration = actual_time
#             else:
#                 new_duration = phase.duration

#             updated_phases.append(traci.trafficlight.Phase(new_duration, phase.state))

#         new_logic = traci.trafficlight.Logic(logic.programID, 0, 0, updated_phases)
#         traci.trafficlight.setProgramLogic(tl, new_logic)
#         traci.trafficlight.setPhase(tl, 0)

#         print(f"Updated timings for {tl}")

#     previous_phase[tl] = current_phase

# # Simulation loop
# while traci.simulation.getMinExpectedNumber() > 0:
#     traci.simulationStep()
#     for tl in traci.trafficlight.getIDList():
#         adjust_traffic_lights(tl)

# traci.close()
