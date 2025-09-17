from app import create_app
from app.extensions import socketio

app = create_app()
application = app
if __name__ == '__main__':
    # app.run(debug=True)
    socketio.run(app, debug=True, host="0.0.0.0", port=5000, use_reloader=True, allow_unsafe_werkzeug=True)