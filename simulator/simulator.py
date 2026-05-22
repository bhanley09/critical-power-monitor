import random
import time
import sqlite3
import os
from datetime import datetime

db_path = os.path.join(os.path.dirname(__file__), "..", "database", "telemetry.db")
conn = sqlite3.connect(db_path)
cursor = conn.cursor()

cursor.execute("""
CREATE TABLE IF NOT EXISTS telemetry (
    timestamp TEXT,
    generator_id TEXT,
    engine_running INTEGER,
    engine_state TEXT,
    battery_voltage REAL,
    coolant_temp INTEGER,
    oil_pressure INTEGER,
    rpm INTEGER,
    runtime_hours REAL,
    frequency REAL,
    total_kw REAL,
    total_kva REAL,
    power_factor REAL,
    l1_amps REAL,
    l2_amps REAL,
    l3_amps REAL,
    v_l1_l2 REAL,
    v_l2_l3 REAL,
    v_l3_l1 REAL,
    v_l1_n REAL,
    v_l2_n REAL,
    v_l3_n REAL,
    alarm TEXT
)
""")

conn.commit()

generators = {}

for i in range(1, 9):
    generators[f"GEN-{i}"] = {
        "engine_running": random.choice([False, False, False, True]),
        "runtime_hours": round(random.uniform(800, 4500), 1),
        "battery_voltage": round(random.uniform(12.4, 13.0), 2),
        "coolant_temp": random.randint(80, 110),
        "oil_pressure": 0,
    }


def generate_data(generator_id, state):
    if random.randint(1, 35) == 1:
        state["engine_running"] = not state["engine_running"]

    if state["engine_running"]:
        engine_state = "RUNNING"
        rpm = random.randint(1785, 1815)
        frequency = round(random.uniform(59.8, 60.2), 1)
        state["coolant_temp"] = min(215, state["coolant_temp"] + random.randint(1, 3))
        state["oil_pressure"] = random.randint(45, 65)
        state["battery_voltage"] = round(random.uniform(12.3, 13.6), 2)
        state["runtime_hours"] = round(state["runtime_hours"] + 0.001, 3)

        total_kw = round(random.uniform(60, 420), 1)
        power_factor = round(random.uniform(0.82, 0.98), 2)
        total_kva = round(total_kw / power_factor, 1)

        l1_amps = round(random.uniform(100, 520), 1)
        l2_amps = round(l1_amps + random.uniform(-18, 18), 1)
        l3_amps = round(l1_amps + random.uniform(-18, 18), 1)

        v_l1_l2 = round(random.uniform(476, 484), 1)
        v_l2_l3 = round(random.uniform(476, 484), 1)
        v_l3_l1 = round(random.uniform(476, 484), 1)

        v_l1_n = round(random.uniform(274, 280), 1)
        v_l2_n = round(random.uniform(274, 280), 1)
        v_l3_n = round(random.uniform(274, 280), 1)

    else:
        engine_state = "READY"
        rpm = 0
        frequency = 0
        state["coolant_temp"] = max(85, state["coolant_temp"] - random.randint(1, 4))
        state["oil_pressure"] = 0
        state["battery_voltage"] = round(random.uniform(12.4, 13.0), 2)

        total_kw = total_kva = power_factor = 0
        l1_amps = l2_amps = l3_amps = 0
        v_l1_l2 = v_l2_l3 = v_l3_l1 = 0
        v_l1_n = v_l2_n = v_l3_n = 0

    alarm = "None"

    if state["battery_voltage"] < 12.1:
        alarm = "Battery Low"
    if state["coolant_temp"] > 200:
        alarm = "High Coolant Temp"
    if state["engine_running"] and state["oil_pressure"] < 30:
        alarm = "Low Oil Pressure"

    return (
        datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        generator_id,
        int(state["engine_running"]),
        engine_state,
        state["battery_voltage"],
        state["coolant_temp"],
        state["oil_pressure"],
        rpm,
        state["runtime_hours"],
        frequency,
        total_kw,
        total_kva,
        power_factor,
        l1_amps,
        l2_amps,
        l3_amps,
        v_l1_l2,
        v_l2_l3,
        v_l3_l1,
        v_l1_n,
        v_l2_n,
        v_l3_n,
        alarm
    )


while True:
    for gen_id, gen_state in generators.items():
        row = generate_data(gen_id, gen_state)

        cursor.execute("""
        INSERT INTO telemetry VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, row)

    conn.commit()

    print("\n--- Fleet Telemetry Updated ---")
    for gen_id, gen_state in generators.items():
        print(f"{gen_id}: {'RUNNING' if gen_state['engine_running'] else 'READY'}")

    time.sleep(3)