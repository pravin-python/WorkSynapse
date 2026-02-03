import time
import json
import sys

# Placeholder for pynput or pywin32 logic
# from pynput import mouse, keyboard

def main():
    while True:
        # Mock data
        activity = {
            "status": "active",
            "active_window": "Visual Studio Code",
            "idle_time": 0,
            "timestamp": time.time()
        }
        print(json.dumps(activity))
        sys.stdout.flush()
        time.sleep(5)

if __name__ == "__main__":
    main()
