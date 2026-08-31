from flask import Flask, render_template, jsonify
from datetime import datetime
import threading
import traci
import time
from collections import OrderedDict

app = Flask(__name__)

# Shared congestion data with ordered lanes
congestion_data = {
    "junction": "Main Junction",
    "time": "",
    "diversions": [],
    "routes": OrderedDict([
        ("184_0", {"coords": [[142.25, 440.25], [142.75, 556.75]], "congested": False}),
        ("196_0", {"coords": [[160.875, 428.625], [520,429.5]], "congested": False}),
        ("190_0", {"coords": [[150, 412.625], [149.5, 159.75]], "congested": False}),
        ("229_0", {"coords": [[157, 147.5], [334.5, 148.5]], "congested": False}),
        ("583_0", {"coords": [[347.5, 158], [526.5, 413]], "congested": False}),
        ("-1956_0", {"coords": [[553.625, 417.875], [732.625,162.875]], "congested": False}),
        ("1994_0", {"coords": [[163, 569.75], [524.5, 569]], "congested": False}),
        ("1992_0", {"coords": [[129.5, 569.5], [0.5, 614]], "congested": False}),
        ("2020_0", {"coords": [[139, 583.5], [138.5, 764]], "congested": False}),
        ("2192_0", {"coords": [[536.5, 580], [538,704]], "congested": False}),
        ("2182_0", {"coords": [[558, 568.5], [792.5, 569.5]], "congested": False}),
        ("1915_0", {"coords": [[364.25, 148.75], [716.5, 148.5]], "congested": False}),
        ("172_0", {"coords": [[125, 429.5], [3, 429]], "congested": False})
    ])
}

def run_simulation():
    """Thread running SUMO simulation and updating congestion data"""
    while True:
        current_time = datetime.now().strftime("%H:%M:%S")
        congestion_data["time"] = current_time
        
        # Get updated congestion status from your traffic light code
        update_congestion_status()  # Your existing function
        update_clearance_times()    # Your existing function
        
        # Update digital board data
        update_digital_board()
        time.sleep(10)  # Update every 10 seconds

def update_digital_board():
    """Update board data from simulation"""
    diversions = []
    
    for lane_id, route_data in congestion_data["routes"].items():
        # Update congestion status
        status = congestion_status.get(lane_id, False)
        route_data["congested"] = status in ["already_congested", "will_be_congested"]
        
        # Add to diversions if congested
        if route_data["congested"]:
            diversions.append({
                "lane": lane_id,
                "destination": f"Lane {lane_id.split('_')[0]}",
                "via": f"Alternate {lane_id.split('_')[0]} Route",
                "clearance": lane_clearance_times.get(lane_id, "N/A")
            })
    
    congestion_data["diversions"] = diversions[:3]  # Show top 3

@app.route('/')
def index():
    return render_template("index.html", 
                         junction=congestion_data["junction"],
                         time=congestion_data["time"],
                         diversions=congestion_data["diversions"],
                         routes=list(congestion_data["routes"].values()))

@app.route('/update')
def get_update():
    """Endpoint for AJAX updates"""
    return jsonify({
        "time": congestion_data["time"],
        "diversions": congestion_data["diversions"],
        "routes": list(congestion_data["routes"].values())
    })

if __name__ == "__main__":
    # Start SUMO thread
    sim_thread = threading.Thread(target=run_simulation)
    sim_thread.daemon = True
    sim_thread.start()
    
    # Start Flask
    app.run(debug=True, use_reloader=False)