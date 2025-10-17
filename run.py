# run.py or wsgi.py
import eventlet
eventlet.monkey_patch()  # ✅ must be first

from app import create_app  # import after patching
from app import socketio

app = create_app()
if __name__ == "__main__":
    socketio.run(app, host="0.0.0.0", port=80)