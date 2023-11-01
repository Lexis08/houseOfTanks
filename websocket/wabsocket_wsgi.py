from websocket_controller import app

# gunicorn --bind 0.0.0.0:3000 websocket_wsgi:app &
if __name__ == "__main__":
    app.run()