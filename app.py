from flask import Flask, render_template, request, redirect, url_for, session
from flask_socketio import SocketIO, join_room, leave_room, emit, Namespace, rooms
import flask_socketio
from flask_session import Session
from pitch import Table, Deck
import flask

app = Flask(__name__)
app.debug = True
app.config['SECRET_KEY'] = 'secret'
app.config['SESSION_TYPE'] = 'filesystem'
app.config['TEMPLATES_AUTO_RELOAD'] = True

Session(app)

socketio = SocketIO(app, manage_session=False)

tables = {}  # type: Dict[Table]


@app.route('/', methods=['GET', 'POST'])
def index():
    return render_template('lobby.html')


@app.route('/table', methods=['GET', 'POST'])
def table():
    if request.method == 'POST':
        username = request.form['username']
        room = request.form['room']
        seat = request.form['seat']
        # Store the data in session
        session['username'] = username
        session['room'] = room
        session['seat'] = seat
        return render_template('table.html', session=session)
    else:
        if session.get('username') is not None:
            return render_template('table.html', session=session)
        else:
            return redirect(url_for('index'))


class PitchNamespace(Namespace):
    def on_join(self, message):
        room = session.get('room')
        username = session.get('username')
        request.sid
        join_room(room)
        print("join", room, username, request.sid)

        sio = flask.current_app.extensions['socketio']
        print(sio.server.manager.rooms)

        emit('status', {'msg': username + ' has entered the room.'}, room=room)
        t = tables.setdefault(room, Table(id=room, tx=self.tx))

    def on_text(self, message):
        room = session.get('room')
        # send this to entire room
        emit('message', {'msg': session.get('username') + ' : ' + message['msg']}, room=room)
        # send this back only to b
        emit('message', {'msg': 'you sent ' + message['msg'].upper()})

    def on_left(self, message):
        room = session.get('room')
        username = session.get('username')
        print('left', room, username, request.sid)
        leave_room(room)
        session.clear()

        emit('status', {'msg': username + ' has left the room.'}, room=room)

    def on_disconnect(self):
        room = session.get('room')
        username = session.get('username')
        print('disconnect', room, username, request.sid)

    def on_connect(self):
        room = session.get('room')
        username = session.get('username')
        print('connect', room, username, request.sid)

        t = tables.setdefault(room, Table(id=room, tx=self.tx))

    def on_play(self, message):
        room = session.get('room')
        username = session.get('username')
        print('Played', message)

    def on_update(self):
        room = session.get('room')
        username = session.get('username')
        t = tables[room]
        emit('table', t.get_json())
        emit('hand', t.get_seat(username).get_hand_json())

    def on_deal(self):
        room = session.get('room')
        username = session.get('username')
        t = tables[room]
        t.deal()
        emit('table', t.get_json())
        emit('hand', t.get_seat(username).get_hand_json())

    def tx(self, event, args, to_all=False):
        room = session.get('room') if to_all else None
        emit(event, args, room=room)

    def on_req_lobby(self):
        print('on_req_lobby')
        emit('lobby', [{'name': 'Matrix', 'seats': [None, 'Laura', 'Mike', None]}])

socketio.on_namespace(PitchNamespace('/pitch'))

if __name__ == '__main__':
    socketio.run(app)
