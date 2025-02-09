import keyboard
import threading
import time

# Shared list to store pressed keys
pressed_keys = []

def key_listener():
    """Listens for key presses and adds them to the list."""
    while True:
        event = keyboard.read_event()
        if event.event_type == keyboard.KEY_DOWN:
            pressed_keys.append(event.name)  # Store the key name
            print(f"Key '{event.name}' added to the list.")

# Run the key listener in a separate thread
listener_thread = threading.Thread(target=key_listener, daemon=True)
listener_thread.start()

def main():
    """Main loop that runs indefinitely, printing the list every few seconds."""
    while True:
        print("Current List:", pressed_keys)
        time.sleep(2)  # Print every 2 seconds to show updates

if __name__ == "__main__":
    main()
