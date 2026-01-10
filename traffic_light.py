import os
import sys
import traci
import math

# Initialize SUMO
if "SUMO_HOME" in os.environ:
    tools = os.path.join(os.environ["SUMO_HOME"], "tools")
    sys.path.append(tools)
else:
    sys.exit("Please declare environment variable 'SUMO_HOME'")

# Define SUMO configuration
sumo_cmd = ["sumo-gui", "-c", "routes.sumocfg", "--step-length", "1"]
traci.start(sumo_cmd)

previous_phase = {}

# === Placeholder ML Models ===
def is_congested_lane(lane_id):
    # Replace this with your congestion prediction model
    return lane_id.endswith("2")  # Fake example

def predict_time_to_reach(vehicle_id, target_lane):
    # Replace this with your model to estimate time to reach a lane
    return 25.0  # seconds

def predict_time_to_clear(lane_id):
    # Replace this with your model to estimate congestion clearance time
    return 40.0  # seconds

# ====================================
def adjust_traffic_lights(tl):
    global previous_phase

    current_phase = traci.trafficlight.getPhase(tl)
    num_phases = len(traci.trafficlight.getAllProgramLogics(tl)[0].phases)

    # Only act when the phase just transitioned (to avoid constant resets)
    if tl in previous_phase and previous_phase[tl] > current_phase:
        logic = traci.trafficlight.getAllProgramLogics(tl)[0]
        phases = logic.phases
        controlled_lanes = traci.trafficlight.getControlledLanes(tl)
        unique_lanes = list(dict.fromkeys(controlled_lanes))

        current_state = traci.trafficlight.getRedYellowGreenState(tl)
        lane_phase_map = {lane: current_state[i] for i, lane in enumerate(unique_lanes)}

        for lane, signal in lane_phase_map.items():
            if signal.lower() != 'r':
                continue  # Only consider red lanes

            vehicle_ids = traci.lane.getLastStepVehicleIDs(lane)
            lane_length = traci.lane.getLength(lane)

            for veh_id in vehicle_ids:
                pos = traci.vehicle.getLanePosition(veh_id)
                distance_to_tls = lane_length - pos

                if distance_to_tls <= 20:  # Close to junction
                    try:
                        route = traci.vehicle.getRoute(veh_id)
                        current_edge = traci.vehicle.getRoadID(veh_id)
                        current_index = route.index(current_edge)
                        remaining_route = route[current_index + 1:]

                        for edge in remaining_route:
                            for i in range(traci.edge.getLaneNumber(edge)):
                                lane_id = f"{edge}_{i}"

                                if is_congested_lane(lane_id):
                                    time_to_reach = predict_time_to_reach(veh_id, lane_id)
                                    time_to_clear = predict_time_to_clear(lane_id)

                                    if time_to_clear > time_to_reach:
                                        traci.vehicle.rerouteTraveltime(veh_id)
                                        print(f"🚗 Vehicle {veh_id} rerouted due to congestion on {lane_id}")
                                    break
                    except Exception as e:
                        print(f"Error checking vehicle {veh_id}: {e}")

        # --- Your traffic light timing logic continues here ---
        distance_threshold = math.inf
        lane_vehicle_counts = {}

        for lane in unique_lanes:
            vehicle_ids = traci.lane.getLastStepVehicleIDs(lane)
            count_near = 0
            lane_length = traci.lane.getLength(lane)

            for veh_id in vehicle_ids:
                pos = traci.vehicle.getLanePosition(veh_id)
                if lane_length - pos <= distance_threshold:
                    count_near += 1

            lane_vehicle_counts[lane] = count_near

        total_vehicles = sum(lane_vehicle_counts.values())
        min_green_time = 5
        total_cycle_time = 100
        remaining_time = total_cycle_time - (min_green_time * num_phases)
        extra_time_per_lane = {lane: 0 for lane in unique_lanes}

        if total_vehicles > 0:
            for lane, count in lane_vehicle_counts.items():
                extra_time_per_lane[lane] = (count / total_vehicles) * remaining_time

        flow_rate = 0.3
        updated_phases = []

        for i, phase in enumerate(phases):
            if "g" in phase.state:
                lane = unique_lanes[i] if i < len(unique_lanes) else None
                count = lane_vehicle_counts.get(lane, 0)
                extra = extra_time_per_lane.get(lane, 0)

                expected_time = count / flow_rate if flow_rate > 0 else min_green_time
                actual_time = max(min_green_time, min(expected_time, min_green_time + extra))
                new_duration = actual_time
            else:
                new_duration = phase.duration

            updated_phases.append(traci.trafficlight.Phase(new_duration, phase.state))

        new_logic = traci.trafficlight.Logic(logic.programID, 0, 0, updated_phases)
        traci.trafficlight.setProgramLogic(tl, new_logic)
        traci.trafficlight.setPhase(tl, 0)

    previous_phase[tl] = current_phase

# ================================
# Simulation loop
while traci.simulation.getMinExpectedNumber() > 0:
    traci.simulationStep()
    for tl in traci.trafficlight.getIDList():
        adjust_traffic_lights(tl)

traci.close()
