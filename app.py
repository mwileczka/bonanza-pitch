from flask import Flask, render_template, request, redirect, url_for, session
from flask_socketio import SocketIO, join_room, leave_room, emit, Namespace
from flask_session import Session

app = Flask(__name__)
app.debug = True
app.config['SECRET_KEY'] = 'secret'
app.config['SESSION_TYPE'] = 'filesystem'
app.config['TEMPLATES_AUTO_RELOAD'] = True

Session(app)

socketio = SocketIO(app, manage_session=False)


@app.route('/', methods=['GET', 'POST'])
def index():
    return render_template('index.html')


@app.route('/chat', methods=['GET', 'POST'])
def chat():
    if request.method == 'POST':
        username = request.form['username']
        room = request.form['room']
        # Store the data in session
        session['username'] = username
        session['room'] = room
        return render_template('chat.html', session=session)
    else:
        if session.get('username') is not None:
            return render_template('chat.html', session=session)
        else:
            return redirect(url_for('index'))


class ChatNamespace(Namespace):
    def on_join(self, message):
        room = session.get('room')
        join_room(room)
        emit('status', {'msg': session.get('username') + ' has entered the room.'}, room=room)

    def on_text(self, message):
        room = session.get('room')
        # send this to entire room
        emit('message', {'msg': session.get('username') + ' : ' + message['msg']}, room=room)
        # send this back only to b
        emit('message', {'msg': 'you sent ' + message['msg'].upper() })

    def on_left(self, message):
        room = session.get('room')
        username = session.get('username')
        leave_room(room)
        session.clear()
        emit('status', {'msg': username + ' has left the room.'}, room=room)

    def on_disconnect(self):
        room = session.get('room')
        username = session.get('username')
        print('Client disconnected', room, username)

    def on_connect(self):
        room = session.get('room')
        username = session.get('username')
        print('Client connect', room, username)

    def on_play(self, message):
        room = session.get('room')
        username = session.get('username')
        print('Played', message)


socketio.on_namespace(ChatNamespace('/chat'))

if __name__ == '__main__':
    socketio.run(app)
