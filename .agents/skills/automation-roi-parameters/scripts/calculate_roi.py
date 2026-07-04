import os
import sys
import json

# Locate constants JSON relative to this script
script_dir = os.path.dirname(os.path.abspath(__file__))
constants_path = os.path.join(script_dir, "..", "resources", "roi_constants.json")

with open(constants_path, "r") as f:
    constants = json.load(f)

# Fallbacks
default_hours = constants["DEFAULT_MANUAL_HOURS_WEEKLY"]
default_rate = constants["DEFAULT_HOURLY_RATE"]
multiplier = constants["DEFAULT_EFFICIENCY_MULTIPLIER"]
maintenance = constants["DEFAULT_ANNUAL_MAINTENANCE"]

# Command line overrides
try:
    hours = float(sys.argv[1]) if len(sys.argv) > 1 else default_hours
    rate = float(sys.argv[2]) if len(sys.argv) > 2 else default_rate
except Exception:
    hours = default_hours
    rate = default_rate

# Compute calculations
weekly_savings = round(hours * rate * multiplier)
annual_savings = round((weekly_savings * 52) - maintenance)
hours_reclaimed = round(hours * 52 * multiplier)

# Output structured result
result = {
    "weekly_savings": weekly_savings,
    "annual_savings": annual_savings,
    "hours_reclaimed": hours_reclaimed,
    "hours_input": hours,
    "rate_input": rate
}

print(json.dumps(result, indent=2))
