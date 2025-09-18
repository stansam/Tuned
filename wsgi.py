from app import create_app
from app.extensions import socketio

app = create_app()

application = app

if __name__ == "__main__":
    socketio.run(app, debug=False, host="0.0.0.0", port=5000)
    # socketio.run(app, debug=False, host="127.0.0.1", port=5000)