import traci
def calculate_max_vehicles(lane_id, vehicle_length=5.0, min_gap=2.5):
    """Returns the maximum number of vehicles that can fit in a lane."""
    lane_length = traci.lane.getLength(lane_id)  # in meters
    max_vehicles = lane_length / (vehicle_length + min_gap)
    return int(max_vehicles)  # Round down to whole vehicles