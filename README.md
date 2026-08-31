# Traffic Management System using SUMO, Computer Vision, and Machine Learning

## Overview
This project implements an **adaptive traffic management system** that:
- Dynamically adjusts **traffic light timings** based on **real-time vehicle count**.
- **Predicts congestion** using **machine learning** models trained on traffic features.
- **Diverts vehicles** by rerouting them **before** they encounter congestion.
- Uses **digital boards** near junctions to suggest alternative routes based on predicted conditions.

It integrates:
- **SUMO (Simulation of Urban MObility)** for traffic simulation.
- **Computer Vision** to detect vehicle counts from simulated video feeds or screenshots.
- **Machine Learning** to predict congestion and estimate clearance times.



## System Architecture

1. **Traffic Simulation**:
   - SUMO simulates a city layout with vehicles.
   - Traffic light control is done via TraCI API.

2. **Computer Vision**:
   - Camera feeds (or screenshots in SUMO) are processed to detect vehicle count on each lane.
   - Object detection models like YOLOv8 or simple background subtraction can be used.

3. **Machine Learning**:
   - A trained model predicts congestion based on extracted traffic features.
   - Another model estimates how quickly a congested lane can clear up.

4. **Signal and Rerouting Controller**:
   - Decides signal timings.
   - Reroutes vehicles dynamically based on predictions.

5. **Digital Board Frontend**:
   - A web dashboard (HTML, CSS, JS, Flask backend) displays nearby junctions and traffic status.

## Technology Stack

| Component          | Technology                     |
|--------------------|---------------------------------|
| Traffic Simulation | SUMO + TraCI API                |
| Vehicle Detection  | OpenCV, YOLOv8 (optional)       |
| ML Models          | Scikit-learn (Gradient Boosting)|
| Rerouting Logic    | Python, NetworkX graphs         |
| Backend            | Flask                           |
| Frontend           | HTML, CSS, JavaScript           |


