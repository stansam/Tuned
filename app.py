from app import create_app
from app.extensions import socketio

app = create_app()
application = app
if __name__ == '__main__':
    # app.run(debug=True)
    socketio.run(app, debug=False, host="127.0.0.1", port=5000)