import os
import sys
import math
import pandas as pd
import sumolib
import traci
from datetime import datetime, timedelta

# Add SUMO tools path
if "SUMO_HOME" in os.environ:
    sys.path.append(os.path.join(os.environ["SUMO_HOME"], "tools"))

# Read timestamps
TIMESTAMPS_FILE = "timestamps.txt"
TRACE_DIR = "traces"

timestamps = []
with open(TIMESTAMPS_FILE, "r") as f:
    for line in f:
        t1, t2 = map(int, line.strip().split(","))
        dt1 = datetime.fromtimestamp(t1 / 1000)
        dt2 = datetime.fromtimestamp(t2 / 1000)
        duration = dt2 - dt1
        timestamps.append((t1, t2, dt1, dt2, duration))

# Display options
print("Please choose a number between 0 and 16:")
for i, (t1, t2, dt1, dt2, duration) in enumerate(timestamps):
    duration_str = str(duration)
    print(f"Number {i}: from {dt1.strftime('%Y-%m-%d %H:%M:%S')} to {dt2.strftime('%Y-%m-%d %H:%M:%S')} (Duration: {duration_str})")

# Get user input
while True:
    try:
        index = int(input("Enter a number (0–16): "))
        if 0 <= index <= 16:
            break
        else:
            print("Please enter a number in the valid range.")
    except ValueError:
        print("Invalid input. Please enter a number.")

# Prepare trace file
trace_file = os.path.join(TRACE_DIR, f"trace_{index}.csv")

try:
    df = pd.read_csv(trace_file, delimiter=',', encoding='utf-8')
    current_time = None
    df = df.sort_values("timestamp")
    grouped = df.groupby("timestamp")

    sumoBinary = sumolib.checkBinary('sumo-gui')
    traci.start([
        sumoBinary,
        "-n", "osm.net.xml", "--no-step-log", "--no-warnings",
    ])

    traci.route.add("trip", ["1151278799"])

    first_timestamp = None

    for timestamp, group in grouped:
        current_timestamp = int(timestamp)

        if first_timestamp is None:
            first_timestamp = current_timestamp

        current_time = (current_timestamp - first_timestamp) / 1000
        traci.simulationStep(current_time)

        current_vehicles = list(traci.vehicle.getIDList())
        current_persons = list(traci.person.getIDList())

        perceived_vehicles = []
        perceived_persons = []

        for _, row in group.iterrows():
            object_id = str(row['Id'])
            x = float(row['X'])
            y = float(row['Y'])
            speed = float(row['Speed'])
            object_class = row['Class']

            if object_class == "VEHICLE":
                perceived_vehicles.append(object_id)

                if object_id not in current_vehicles:
                    traci.vehicle.add(vehID=object_id, routeID="trip")

                traci.vehicle.moveToXY(vehID=object_id, edgeID="-1", laneIndex=-1,
                                       x=x, y=y, keepRoute=0)

                traci.vehicle.setSpeed(vehID=object_id, speed=speed)

            else:
                perceived_persons.append(object_id)

                pos = traci.simulation.convertRoad(x, y)

                if pos[0].startswith(":"):
                    continue

                if object_id not in current_persons:
                    traci.person.add(
                        personID=object_id,
                        edgeID="184963264#1",
                        pos=0,
                        depart=math.ceil(current_time)
                    )

                traci.person.moveToXY(personID=object_id, edgeID=pos[0],
                                      x=x, y=y, keepRoute=0)

                traci.person.setSpeed(personID=object_id, speed=speed)

        vehicles_to_remove = [veh_id for veh_id in current_vehicles
                              if veh_id not in perceived_vehicles]

        persons_to_remove = [p_id for p_id in current_persons
                             if p_id not in perceived_persons]

        for veh_id in vehicles_to_remove:
            traci.vehicle.remove(vehID=veh_id)

        for p_id in persons_to_remove:
            traci.person.remove(personID=p_id)

    print(f"Simulation of file {trace_file} completed successfully.")
    traci.close()

except Exception as e:
    print(e)
    print("Error :(")
