from flask import Flask, render_template, request
from flask_socketio import SocketIO, send, emit

app = Flask(__name__)
app.config['SECRET_KEY'] = 'chatroom-secret'

socketio = SocketIO(app, async_mode='threading')

# 記錄線上使用者
clients = {}


@app.route('/')
def index():
    return render_template('index.html')


# 更新線上人數
def broadcast_user_count():
    socketio.emit('user_count', {
        'count': sum(1 for name in clients.values() if name)
    })


# 使用者連線
@socketio.on('connect')
def on_connect():
    clients[request.sid] = None
    print('使用者已連線')


# 使用者加入聊天室
@socketio.on('join')
def on_join(data):
    username = str(data.get('username', '匿名')).strip() or '匿名'
    clients[request.sid] = username

    emit('user_joined', {
        'username': username
    }, broadcast=True)

    broadcast_user_count()


# 使用者離開聊天室
@socketio.on('disconnect')
def on_disconnect():
    username = clients.pop(request.sid, None)

    if username:
        emit('user_left', {
            'username': username
        }, broadcast=True)

    broadcast_user_count()


# 接收與廣播聊天訊息
@socketio.on('message')
def handle_message(message):
    print('收到訊息：', message)
    send(message, broadcast=True)


@socketio.on('typing')
def on_typing(data):
    print('收到輸入狀態：', data)
    emit('typing', data, broadcast=True, include_self=False)
@socketio.on('change_username')
def on_change_username(data):
    old_name = clients.get(request.sid)
    new_name = str(data.get('username', '')).strip()

    if not new_name or not old_name or old_name == new_name:
        return

    clients[request.sid] = new_name

    emit('username_changed', {
        'old_name': old_name,
        'new_name': new_name
    }, broadcast=True)

if __name__ == '__main__':
    socketio.run(
        app,
        host='127.0.0.1',
        port=5001,
        debug=True,
        allow_unsafe_werkzeug=True
    )
