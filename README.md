# 🚦 Traffic-Flow-Optimizer

Traffic Flow Optimizer is a Python-based project that uses SUMO (Simulation of Urban Mobility) and Machine Learning to analyze traffic conditions and dynamically optimize traffic signal timings to reduce congestion and improve traffic flow.

📌 Project Overview

Urban traffic congestion is a major challenge. This project simulates traffic using SUMO, collects real-time traffic data, predicts congestion using a trained ML model, and adapts traffic signal timings accordingly to ensure smoother vehicle flow.

🧠 Key Features

Traffic simulation using SUMO

Real-time vehicle data collection

Congestion prediction using Machine Learning

Adaptive traffic signal control

Modular and extensible code structure

📂 Project Structure
Traffic-Flow-Optimizer/
├── main.py
├── model.py
├── save_model.py
├── traffic_light.py
├── collect_data_from_sumo.py
├── get_max_vehicles.py
├── randomTrips.py
├── a.py
├── backup.py
├── congestion_predictor.pkl
├── scaler.pkl
├── lane_capacities.csv
├── *.net.xml
├── *.rou.xml
├── *.sumocfg
└── README.md

🧩 File Description
File Name	Description
main.py	Entry point of the project; runs simulation and optimization
model.py	Defines the ML model for congestion prediction
save_model.py	Trains and saves the ML model
traffic_light.py	Controls traffic signal logic
collect_data_from_sumo.py	Extracts traffic data from SUMO
get_max_vehicles.py	Computes maximum vehicle count per lane
randomTrips.py	Generates random vehicle trips
congestion_predictor.pkl	Trained congestion prediction model
scaler.pkl	Feature scaling model
.net.xml / .rou.xml / .sumocfg	SUMO network, route, and config files
⚙️ Prerequisites

Python 3.x

SUMO installed and configured

Required Python libraries:

pip install numpy pandas scikit-learn traci

▶️ How to Run
1️⃣ Generate Traffic Data
python randomTrips.py

2️⃣ Collect Simulation Data
python collect_data_from_sumo.py

3️⃣ Train & Save Model
python save_model.py

4️⃣ Run Traffic Optimization
python main.py

🔄 Workflow

Simulate traffic using SUMO

Collect lane-wise vehicle data

Predict congestion using ML

Adjust traffic suggestions dynamically

Improve traffic flow and reduce congestion
