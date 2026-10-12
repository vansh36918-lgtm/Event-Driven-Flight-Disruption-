"""
Zero-IDE Master Launcher.
Runs the complete Event-Driven Flight Disruption & Autonomous Re-Accommodation Platform.
No VS Code or external tools required — execute directly via:
    python run.py
"""
import sys
import os
import uvicorn

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

BANNER = """
================================================================================
   AirOps: Flight Disruption & Autonomous Re-Accommodation Platform
================================================================================
  [Pipeline]     FastAPI | RabbitMQ / AsyncBus | NetworkX | AI Concierge
  [Status]       GDS Telemetry Live • Multi-Hub Graph Active
  [Web Console]  http://localhost:8000
  [Swagger Docs] http://localhost:8000/docs
================================================================================
  Press CTRL+C to stop the server anytime.
================================================================================
"""

if __name__ == "__main__":
    # Ensure current directory is in PYTHONPATH
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    print(BANNER)
    uvicorn.run("app.api.main:app", host="0.0.0.0", port=8000, reload=False, log_level="info")
