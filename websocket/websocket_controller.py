import logging
import json
from flask import Flask, request
from flask import Response
from flask_socketio import SocketIO

# Logging
logging.basicConfig(level=logging.DEBUG)
logging.getLogger('werkzeug').setLevel(logging.WARN)
LOGGER = logging.getLogger('websocket_controller')

# Init app
app = Flask(__name__)
socketio = SocketIO(app, cors_allowed_origins='*')

# Clients Dict
clients = {}

#================================================
# HTTP
#================================================
@app.route('/dispatch_shoot_result', methods=['POST'])
def dispatch_shoot_result():
    json_as_dict = request.json
    print(json_as_dict)

    LOGGER.info('emit shoot_result to Session ID [%s]', json_as_dict['src_sid'])
    socketio.emit("shoot_result",
                  json.dumps({
                      "txt": json_as_dict['src_msg'],
                      "pv": json_as_dict['src_pv'],
                      "shield": json_as_dict['src_shield'],
                  }),
                  room=json_as_dict['src_sid'])

    if json_as_dict['target_sid']:
        print('===> Target sid :', json_as_dict['target_sid'], 'txt :', json_as_dict['target_msg'])
        LOGGER.info('emit shoot_result to Session ID [%s]', json_as_dict['target_sid'])
        socketio.emit("shoot_result",
                      json.dumps({
                          "txt": json_as_dict['target_msg'],
                          "pv": json_as_dict['target_pv'],
                          "shield": json_as_dict['target_shield'],
                      }),
                      room=json_as_dict['target_sid'])

    return Response()

#================================================
# WebSocket
#================================================
@socketio.on('connect')
def connect():
    sid = request.sid
    LOGGER.info('new connection : Session ID = [%s]', sid)
    clients[request.sid] = sid
    socketio.emit("connection", json.dumps({"sid": sid}), room=sid)

#================================================
# RUN
#================================================
if __name__ == '__main__':
    socketio.run(app, host='0.0.0.0', port=3000, allow_unsafe_werkzeug=True)
