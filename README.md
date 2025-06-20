# SUMO Replay from Real-World RSU Data

## Overview

This repo offers a way to import real-world experimental data into the simulation tool **SUMO**. It offers at once perception data (found in the `traces` folder) from an RSU installed in a roundabout in Rouen, France, and a mechanism that replays the exact perceived scenario in simulation thanks to SUMO.

## How to use?

To run the simulation, you simply have to run the following command:

```bash
python3 script.py
```

It will prompt you to provide a number between **0 and 16**. Each number corresponds to a **time interval**, as will be shown in your terminal output.

Once you select a time interval, **SUMO will be automatically opened**. You then only have to **start the simulation from SUMO**.
