# run.py or wsgi.py
import eventlet
eventlet.monkey_patch()  # ✅ must be first

from app import app  # import after patching
from app import socketio

if __name__ == "__main__":
    socketio.run(app, host="0.0.0.0", port=80)