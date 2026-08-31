import os
import sys
import traci
import math
import joblib
import numpy as np
import pandas as pd
from collections import defaultdict, deque
# Add these right after your existing imports
from flask import Flask, render_template, jsonify
from collections import OrderedDict
import threading
import datetime

CONGESTION_COLORS = {
    "already_congested": "#FF0000",  # Red
    "will_be_congested": "#FE7743",  # Orange
    "normal": "#00FF00",             # Green
               # Yellow
}


# Add this right after your last global variable declaration
app = Flask(__name__)

# Digital board configuration - MUST match your HTML template lanes exactly
congestion_data = {
    "junction": "Main Junction",
    "time": "",
    "diversions": [],
    "routes": OrderedDict([
        ("184_0", {"coords": [[142.25, 440.25], [142.75, 556.75]], "congested": False, "color": CONGESTION_COLORS["normal"]}),
        ("196_0", {"coords": [[160.875, 428.625], [520,429.5]], "congested": True, "color": CONGESTION_COLORS["already_congested"]}),
        ("190_0", {"coords": [[150, 412.625], [149.5, 159.75]], "congested": False, "color": CONGESTION_COLORS["normal"]}),
        ("229_0", {"coords": [[157, 147.5], [334.5, 148.5]], "congested": False, "color": CONGESTION_COLORS["normal"]}),
        ("583_0", {"coords": [[347.5, 158], [526.5, 413]], "congested": False, "color": CONGESTION_COLORS["normal"]}),
        ("-1956_0", {"coords": [[553.625, 417.875], [732.625,162.875]], "congested": False, "color": CONGESTION_COLORS["normal"]}),
        ("1994_0", {"coords": [[163, 569.75], [524.5, 569]], "congested": False, "color": CONGESTION_COLORS["normal"]}),
        ("1992_0", {"coords": [[129.5, 569.5], [0.5, 614]], "congested": False, "color": CONGESTION_COLORS["normal"]}),
        ("2020_0", {"coords": [[139, 583.5], [138.5, 764]], "congested": False, "color": CONGESTION_COLORS["normal"]}),
        ("2192_0", {"coords": [[536.5, 580], [538,704]], "congested": False, "color": CONGESTION_COLORS["normal"]}),
        ("2182_0", {"coords": [[558, 568.5], [792.5, 569.5]], "congested": False, "color": CONGESTION_COLORS["normal"]}),
        ("1915_0", {"coords": [[364.25, 148.75], [716.5, 148.5]], "congested": False, "color": CONGESTION_COLORS["normal"]}),
        ("172_0", {"coords": [[125, 429.5], [3, 429]], "congested": False, "color": CONGESTION_COLORS["normal"]})
    ])
}

# === SUMO Initialization ===
if "SUMO_HOME" in os.environ:
    tools = os.path.join(os.environ["SUMO_HOME"], "tools")
    sys.path.append(tools)
else:
    sys.exit("❌ Please set the 'SUMO_HOME' environment variable.")

sumo_cmd = ["sumo-gui", "-c", "simple_traffic.sumocfg", "--step-length", "1", "--delay", "10"]
traci.start(sumo_cmd)

# === Load ML Models ===
try:
    clf = joblib.load("congestion_predictor.pkl")
    scaler = joblib.load("scaler.pkl")
    encoder = joblib.load("lane_encoder.pkl")
except Exception as e:
    sys.exit(f"❌ Failed to load ML models: {str(e)}")

# === Data Buffers ===
lane_flow_history = defaultdict(lambda: deque(maxlen=5))
entry_timestamps = defaultdict(lambda: deque(maxlen=1000))
exit_timestamps = defaultdict(lambda: deque(maxlen=1000))
previous_counts = defaultdict(int)
previous_phase = {}

previous_counts = {lane_id: 0 for lane_id in traci.lane.getIDList() if not lane_id.startswith(":")}
# === Initialize Counts ===
for tl_id in traci.trafficlight.getIDList():
    for lane_id in traci.trafficlight.getControlledLanes(tl_id):
        if not lane_id.startswith(":"):
            previous_counts[lane_id] = traci.lane.getLastStepVehicleNumber(lane_id)

# Global congestion tracking dictionaries
congestion_status = {}  # Updated every 30 seconds
congestion_status_copy={}
lane_clearance_times = {}  # Updated every 10 seconds
last_update_time = {"congestion": 0, "clearance": 0}


def suggest_diversions(source_lane, G, lane_avg_speeds):
    """
    Suggest alternate routes from a given source lane, avoiding congested lanes,
    and calculating travel time and length using graph data only.
    """
    diversions = []
    source_edge = source_lane.split("_")[0]

    # Identify congested edges (to be removed as nodes)
    congested_edges = {
        lane_id.split("_")[0]
        for lane_id, status in congestion_status_copy.items()
        if status in ("already_congested", "will_be_congested")
    }

    print("congested edges:", congested_edges)

    # Create a filtered graph
    G_filtered = G.copy()

    for cong_edge in congested_edges:
        if cong_edge not in G:
            continue

        # Remove congested node temporarily
        if cong_edge in G_filtered:
            G_filtered.remove_node(cong_edge)

        successors = list(G.successors(cong_edge))
        print(f"Successors of {cong_edge}:", successors)

        for target_edge in successors:
            if target_edge not in G_filtered:
                continue

            try:
                path = nx.shortest_path(G_filtered, source=source_edge, target=target_edge, weight='weight')

                total_length = sum(
                    G[u][v].get('length', G[u][v].get('weight', 1))
                    for u, v in zip(path[:-1], path[1:])
                )

                total_time = 0
                for edge in path:
                    lane_id = edge + "_0"
                    speed = lane_avg_speeds.get(lane_id, 10)
                    length = sum(
                        G[edge][succ].get('length', G[edge][succ].get('weight', 1))
                        for succ in G.successors(edge)
                        if (edge, succ) in G.edges
                    )
                    total_time += length / speed if speed > 0 else float('inf')

                diversions.append({
                    "from": source_lane,
                    "to": target_edge,
                    "via": path,
                    "length": round(total_length, 1),
                    "estimated_time": round(total_time, 1)
                })

            except (nx.NetworkXNoPath, nx.NodeNotFound):
                print(f"No path from {source_edge} to {target_edge}")
                continue

        # Re-add the removed congested node and its edges
        if cong_edge not in G_filtered:
            G_filtered.add_node(cong_edge)

        for pred in G.predecessors(cong_edge):
            if G.has_edge(pred, cong_edge):
                G_filtered.add_edge(pred, cong_edge, **G[pred][cong_edge])
        for succ in G.successors(cong_edge):
            if G.has_edge(cong_edge, succ):
                G_filtered.add_edge(cong_edge, succ, **G[cong_edge][succ])

    return sorted(diversions, key=lambda x: x["estimated_time"])[14:18]


                


def update_digital_board():
    """Sync SUMO data with digital board"""
    current_time = traci.simulation.getTime()
    congestion_data["time"] = str(datetime.timedelta(seconds=current_time))

    diversions = []

    for lane_id, route_data in congestion_data["routes"].items():
        status = congestion_status.get(lane_id, False)
        clearance = lane_clearance_times.get(lane_id, float('inf'))

        # Update route color based on congestion status
        if status == "already_congested":
            route_data.update({
                "congested": True,
                "color": CONGESTION_COLORS["already_congested"]
            })
        elif status == "will_be_congested":
            route_data.update({
                "congested": True,
                "color": CONGESTION_COLORS["will_be_congested"]
            })
        else:
            route_data.update({
                "congested": False,
                "color": CONGESTION_COLORS["normal"]
            })

    # Suggest diversions from a central source lane (e.g., "172_0")
    source_lane = "172_0"
    alternate_routes = suggest_diversions(source_lane, G, lane_avg_speeds)
    for diversion in alternate_routes:
        clearance = lane_clearance_times.get(diversion["to"], float('inf'))
        route_color = congestion_data["routes"].get(diversion["to"], {}).get("color", CONGESTION_COLORS["normal"])
        diversions.append({
            "lane": diversion["from"],
            "destination": diversion["to"],
            "via": diversion["via"],
            "clearance": clearance if clearance != float('inf') else "N/A",
            "length": diversion["length"],
            "estimated_time": diversion["estimated_time"],
            "color": route_color
        })

    # Keep only top 3 by shortest clearance time
    congestion_data["diversions"] = sorted(
        diversions,
        key=lambda x: x["clearance"] if isinstance(x["clearance"], (int, float)) else float('inf')
    )[:3]

    # Add status summary (clearance times + average speeds)
    status_summary = []
    for lane_id in congestion_data["routes"]:
        clearance_time = lane_clearance_times.get(lane_id, float('inf'))
        if clearance_time != float('inf'):
            avg_speed = lane_avg_speeds.get(lane_id, 0.0)
            status_summary.append({
                "lane": lane_id,
                "clearance_time": round(clearance_time, 1),
                "average_time": round(avg_speed, 1)
            })

    congestion_data["status_summary"] = status_summary







@app.route('/')
def index():
    update_digital_board()
    return render_template("digital_board.html",
                       junction=congestion_data["junction"],
                       time=congestion_data["time"],
                       diversions=congestion_data["diversions"],
                       routes=list(congestion_data["routes"].values()),
                       status_summary=congestion_data["status_summary"])



@app.route('/update')
def get_update():
    update_digital_board()
    return jsonify(congestion_data)

def run_flask():
    app.run(host='0.0.0.0', port=5000, debug=False, use_reloader=False)

def is_congested_lane(lane_id):
    """Determines lane congestion status with three possible return states:
    - "already_congested" (density > 55%)
    - "will_be_congested" (ML model predicts congestion)
    - False (no current or predicted congestion)"""
    
    try:
        if not lane_flow_history.get(lane_id):
            print("a")
            return False
       
        latest = lane_flow_history[lane_id][-1]
        current_density = latest[0]  # Latest density measurement
        # print(f"\nLane {lane_id} status:")
        # print(f"• Density: {current_density:.1%}")
        # print(f"• Vehicles: {latest[3]} (In: {latest[1]}, Out: {latest[2]})")
        # print(f"• Net flow: {latest[4]:.1f}")
        
        # Immediate congestion check
        if current_density > 0.55:  # 55% density threshold
            return "already_congested"
        
        # Predictive congestion check
        X = pd.DataFrame([[
            encoder.transform([lane_id])[0],  # Lane ID encoded
            current_density,
            latest[1],  # entering_rate
            latest[2],  # exit_rate
            latest[3],  # vehicle_count
            latest[4],  # net_flow
            latest[5],  # flow_ratio
            latest[6]   # flow_vs_count
        ]], columns=clf.feature_names_in_)
        
        if current_density==0 and latest[3]==0:
            return False
        # Prepare features
        for col in X.columns[1:]:
            X[col] = X[col].astype(np.float64)
        X.iloc[:, 1:] = scaler.transform(X.iloc[:, 1:])
        
        # Debug output
        
        # print(f"\nLane {lane_id} status:")
        # print(f"• Density: {current_density:.1%}")
        # print(f"• Vehicles: {latest[3]} (In: {latest[1]}, Out: {latest[2]})")
        # print(f"• Net flow: {latest[4]:.1f}")
        
        # Make prediction
        if clf.predict(X)[0] == 1:
            return "will_be_congested"
        return False
        
    except Exception as e:
        
        return current_density > 0.55

def update_congestion_status():
    # Updates congestion status for all lanes every 30 seconds.
    # Maintains three states in congestion_status dictionary:
    # - "already_congested"
    # - "will_be_congested" 
    # - False (no congestion)
    
    current_time = traci.simulation.getTime()
    if current_time - last_update_time["congestion"] >= 30:
        # print(f"\nUpdating congestion status at {current_time:.1f}s")
        
        for lane_id in traci.lane.getIDList():
            if lane_id.startswith(":"):  # Skip internal lanes
                continue
                
            status = is_congested_lane(lane_id)
            if status=="already_congested": 
             congestion_status[lane_id] ="already_congested"
            elif status=="will_be_congested":
                congestion_status[lane_id]="will_be_congested"
            else:
                congestion_status[lane_id]=False
            
            # Optional debug print
            # if status:
            #     print(f" - Lane {lane_id}: {status}")
        
        last_update_time["congestion"] = current_time

def update_clearance_times():
    """Update clearance times with focus on congested/predicted lanes"""
    current_time = traci.simulation.getTime()
    if current_time - last_update_time["clearance"] >= 10:
        # Process all lanes but prioritize congested ones
        for lane_id in traci.lane.getIDList():
            if lane_id.startswith(":"):
                continue
          
            # Only calculate clearance for relevant lanes
            if congestion_status.get(lane_id) in ["already_congested", "will_be_congested"]:
                
                if lane_id in lane_flow_history and len(lane_flow_history[lane_id]) >= 3:
                    # Enhanced outflow calculation with congestion weighting
                    recent_data = list(lane_flow_history[lane_id])[-3:]
                    
                    # Weight more recent data higher
                    weights = [0.3, 0.3, 0.4]  # Weights for [t-2, t-1, current]
                    weighted_outflow = sum(d[2]*w for d,w in zip(recent_data, weights))
                    
                    # Apply congestion severity factor
                    congestion_factor = 1.5 if congestion_status[lane_id] == "already_congested" else 1.2
                    adjusted_outflow = weighted_outflow * congestion_factor / 10.0
                    
                    current_count = recent_data[-1][3]
                    # print(adjusted_outflow)
                    # print()
                    if adjusted_outflow > 0.01:
                        # Include buffer time based on congestion level
                        buffer_time = 15 if congestion_status[lane_id] == "already_congested" else 8
                        lane_clearance_times[lane_id] = (current_count / adjusted_outflow) + buffer_time
                        
                    else:
                        lane_clearance_times[lane_id] = float('inf')
                else:
                    lane_clearance_times[lane_id] = float('inf')
                
                # Debug output for congested lanes
                # if lane_clearance_times[lane_id] != float('inf'):
                #     print(f"⚠️ Congestion clearance for {lane_id}: {lane_clearance_times[lane_id]:.1f}s")
            else:
                # Non-congested lanes get default clearance
                lane_clearance_times[lane_id] = float('inf')
        
        last_update_time["clearance"] = current_time



# Global data structures for tracking lane traversal times
lane_traversal_times = defaultdict(list)  # Stores actual traversal times per lane
lane_avg_speeds = {}  # Stores calculated average speeds per lane
vehicle_entry_times = {}  # Tracks when vehicles enter lanes

def update_lane_statistics():
    """Update lane speed statistics based on vehicle movements"""
    current_time = traci.simulation.getTime()
    
    # Track new vehicles entering lanes
    for veh_id in traci.vehicle.getIDList():
        lane_id = traci.vehicle.getLaneID(veh_id)
        if veh_id not in vehicle_entry_times:
            vehicle_entry_times[veh_id] = (lane_id, current_time)
        
        # Check if vehicle changed lanes
        prev_lane, entry_time = vehicle_entry_times[veh_id]
        if prev_lane != lane_id:
            # Record traversal time for previous lane
            traversal_time = current_time - entry_time
            lane_traversal_times[prev_lane].append(traversal_time)
            
            # Keep only recent samples (last 10 vehicles)
            if len(lane_traversal_times[prev_lane]) > 10:
                lane_traversal_times[prev_lane].pop(0)
            
            # Update average speed for the lane
            if lane_traversal_times[prev_lane]:
                avg_time = np.mean(lane_traversal_times[prev_lane])
                lane_length = traci.lane.getLength(prev_lane)
                lane_avg_speeds[prev_lane] = lane_length / min(avg_time,10 )
            
            # Record entry to new lane
            vehicle_entry_times[veh_id] = (lane_id, current_time)





import traci
import networkx as nx
from sumolib.net import readNet

# Load SUMO network and build graph (call once before simulation loop)
net = readNet("map.net.xml")  # Replace with your .net.xml path
G = nx.DiGraph()
for edge in net.getEdges():
    if not edge.getID().startswith(":"):  # Skip internal edges
        for succ in edge.getOutgoing():
            if not succ.getID().startswith(":"):
                G.add_edge(edge.getID(), succ.getID(), weight=succ.getLength())

# Dummy global lane clearance dictionary (replace with your logic)
lane_clearance_times = {}  # e.g., { "edge_0": 120 }

# Dummy time estimator (replace with your model or logic)
def estimate_route_time(route):
    # Example: assume 13.9 m/s (50 km/h) on each lane
    speed = 13.9
    return sum(traci.lane.getLength(f"{e}_0") / speed for e in route if not e.startswith(":"))

# Find a route avoiding a specific edge using NetworkX
def find_shortest_path_excluding(G, start, end, avoid_edge):
    G_filtered = G.copy()
    if G_filtered.has_node(avoid_edge):
        G_filtered.remove_node(avoid_edge)
    try:
        return nx.shortest_path(G_filtered, start, end, weight='weight')
    except nx.NetworkXNoPath:
        return None

# Wrapper to be used inside the rerouting function
def find_alternative_route_nx(veh_id, congested_edge, G, net):
    try:
        current_edge = traci.vehicle.getRoadID(veh_id)
        original_route = traci.vehicle.getRoute(veh_id)
        destination_edge = next(edge for edge in reversed(original_route) if not edge.startswith(':'))

        new_route = find_shortest_path_excluding(G, current_edge, destination_edge, congested_edge)

        if not new_route or congested_edge in new_route:
            return None

        return new_route
    except Exception as e:
        print(f"⚠️ Error in alternative route: {e}")
        return None


rerouted_vehicles = set()

# Main rerouting decision logic
def should_reroute(veh_id, next_lane):
    """Enhanced rerouting decision that avoids the congested lane and finds the shortest alternative route"""
    if veh_id in rerouted_vehicles:
        return False
    
    current_edge = traci.vehicle.getRoadID(veh_id)
    original_route = traci.vehicle.getRoute(veh_id)
    congested_edge = next_lane.split('_')[0]

    try:
        current_idx = original_route.index(current_edge)
        congested_idx = original_route.index(congested_edge, current_idx + 1)
        route_segment = original_route[current_idx:congested_idx+1]
    except ValueError:
        return False

    time_to_reach_congestion = estimate_route_time(route_segment)
    clearance_time = lane_clearance_times.get(next_lane, float('inf'))

    if time_to_reach_congestion > clearance_time:
        return False

    original_length = sum(traci.lane.getLength(f"{e}_0") for e in original_route if not e.startswith(':'))
    original_time = estimate_route_time(original_route)

    # ✅ Use NetworkX for finding alternative route
    alternative_route = find_alternative_route_nx(veh_id, congested_edge, G, net)

    if alternative_route is None:
        return False

    new_length = sum(traci.lane.getLength(f"{e}_0") for e in alternative_route if not e.startswith(':'))
    new_time = estimate_route_time(alternative_route)

    print(f"🔁 Rerouting {veh_id}")
    print(f"   Old route: {original_route}")
    print(f"   New route: {alternative_route}")

    # Apply new route
    traci.vehicle.setRoute(veh_id, alternative_route)

    rerouted_vehicles.add(veh_id)

    # Optional: Customize decision criteria
    return True








# === Update Flow History ===
def update_lane_flow_data(lane_id):
    if lane_id.startswith(":"):  # Skip internal lanes
        return
        
    try:
        current_time = traci.simulation.getTime()
        current_count = traci.lane.getLastStepVehicleNumber(lane_id)
        density = traci.lane.getLastStepOccupancy(lane_id)
        
        # Calculate vehicle movements
        count_diff = current_count - previous_counts[lane_id]
        
        # Update entry/exit timestamps
        if count_diff > 0:  # Vehicles entered
            entry_timestamps[lane_id].extend([current_time] * count_diff)
        elif count_diff < 0:  # Vehicles exited
            exit_timestamps[lane_id].extend([current_time] * abs(count_diff))
            
        # Purge old data (60-second window)
        cutoff = max(0, current_time - 60)
       
        entry_timestamps[lane_id] = deque(
            (ts for ts in entry_timestamps[lane_id] if ts >= cutoff),
            maxlen=1000
        )
        exit_timestamps[lane_id] = deque(
            (ts for ts in exit_timestamps[lane_id] if ts >= cutoff),
            maxlen=1000
        )
        
        # Calculate metrics
        entering_rate = len(entry_timestamps[lane_id])
        exit_rate = len(exit_timestamps[lane_id])
       
        # if lane_id=='-190_0':
        #  print(lane_id)
        #  print(entering_rate)
        #  print(exit_rate)
        #  print(current_time)
        #  print()
    
        
        # Update flow history
        lane_flow_history[lane_id].append((
            density,
            entering_rate,
            exit_rate,
            current_count,
            entering_rate - exit_rate,  # net flow
            entering_rate / (exit_rate + 1),  # flow ratio
            (entering_rate - exit_rate) / (current_count + 1)  # flow vs count
        ))
        
     
        
        previous_counts[lane_id] = current_count
        
    except Exception as e:
        print(f"⚠️ Error updating {lane_id}: {str(e)}")



# === Traffic Light Control ===
# === Traffic Light Control ===
# === Traffic Light Control ===
def adjust_traffic_lights(tl_id):
    global previous_phase

    current_phase = traci.trafficlight.getPhase(tl_id)
    logic = traci.trafficlight.getAllProgramLogics(tl_id)[0]
    num_phases = len(logic.phases)
    controlled_lanes = list(dict.fromkeys(traci.trafficlight.getControlledLanes(tl_id)))

    # Only update timing if the cycle has completed (phase reset)
    if tl_id in previous_phase and previous_phase[tl_id] > current_phase:
        lane_vehicle_counts = {}
        distance_threshold = math.inf

        for lane in controlled_lanes:
            vehicle_ids = traci.lane.getLastStepVehicleIDs(lane)
            count_near = 0
            lane_length = traci.lane.getLength(lane)

            for veh_id in vehicle_ids:
                pos = traci.vehicle.getLanePosition(veh_id)
                if lane_length - pos <= distance_threshold:
                    count_near += 1

            lane_vehicle_counts[lane] = count_near

        total_vehicles = sum(lane_vehicle_counts.values())
        min_green_time = 15
        total_cycle_time = 100
        remaining_time = total_cycle_time - (min_green_time * num_phases)
        extra_time_per_lane = {lane: 0 for lane in controlled_lanes}

        if total_vehicles > 0:
            for lane, count in lane_vehicle_counts.items():
                extra_time_per_lane[lane] = (count / total_vehicles) * remaining_time

        flow_rate = 0.3
        updated_phases = []

        for i, phase in enumerate(logic.phases):
            if "g" in phase.state.lower():
                lane = controlled_lanes[i] if i < len(controlled_lanes) else None
                count = lane_vehicle_counts.get(lane, 0)
                extra = extra_time_per_lane.get(lane, 0)
                expected_time = count / flow_rate if flow_rate > 0 else min_green_time
                new_duration = max(min_green_time, min(expected_time, min_green_time + extra))
            else:
                new_duration = phase.duration

            updated_phases.append(traci.trafficlight.Phase(new_duration, phase.state))

        new_logic = traci.trafficlight.Logic(logic.programID, 0, 0, updated_phases)
        traci.trafficlight.setProgramLogic(tl_id, new_logic)
        traci.trafficlight.setPhase(tl_id, 0)

    previous_phase[tl_id] = current_phase

def immediate_reroute_on_red(tl_id):
    current_state = traci.trafficlight.getRedYellowGreenState(tl_id)
    controlled_lanes = traci.trafficlight.getControlledLanes(tl_id)

    for i, lane_id in enumerate(controlled_lanes):
        if current_state[i].lower() != 'r':
            continue

        for veh_id in traci.lane.getLastStepVehicleIDs(lane_id):
            if traci.vehicle.getSpeed(veh_id) < 0.1:
                lane_pos = traci.vehicle.getLanePosition(veh_id)
                lane_length = traci.lane.getLength(lane_id)

                if lane_length - lane_pos <= 50:
                    try:
                        route = traci.vehicle.getRoute(veh_id)
                        current_edge = traci.vehicle.getRoadID(veh_id)

                        if current_edge in route:
                            next_edges = route[route.index(current_edge) + 1:]

                            for edge in next_edges:
                                for j in range(traci.edge.getLaneNumber(edge)):
                                    next_lane = f"{edge}_{j}"
                                    if congestion_status.get(next_lane, False):
                                        if should_reroute(veh_id, next_lane):
                                            # traci.vehicle.rerouteTraveltime(veh_id)
                                            current_time=traci.simulation.getTime()
                                            print(f"🔄 Rerouted {veh_id} to avoid {next_lane} {current_time}")
                                            return
                    except Exception as e:
                        print(f"⚠️ Reroute failed for {veh_id}: {str(e)}")


# === Main Simulation Loop ===
if __name__ == "__main__":
    # Add these 3 lines at the VERY START of the main block
    flask_thread = threading.Thread(target=run_flask)
    flask_thread.daemon = True
    flask_thread.start()

    try:
        step = 0
        while traci.simulation.getMinExpectedNumber() > 0:
            traci.simulationStep()

             
        
            update_lane_statistics()
           
    
    # Process each unique lane only once
            
            for lane_id in traci.lane.getIDList():
              if not lane_id.startswith(":"):
                update_lane_flow_data(lane_id)
            
            # Keep all existing code below exactly as is until:
            
            if step % 10 == 0:
                update_clearance_times()
                  # <-- Add this line
            
            # Rest of your code remains identical
            if step % 23 == 0:
                update_congestion_status()
                update_digital_board()
            
            if step % 5 == 0:
                for tl_id in traci.trafficlight.getIDList():
                    adjust_traffic_lights(tl_id)
                    immediate_reroute_on_red(tl_id) 
            update_digital_board()  

            congestion_status_copy=congestion_status.copy()
           
            step += 1
            
    except KeyboardInterrupt:
        print("\nSimulation stopped by user")
    finally:
        traci.close()