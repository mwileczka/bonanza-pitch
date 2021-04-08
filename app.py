from flask import Flask, render_template, request, redirect, url_for, session
from flask_socketio import SocketIO, join_room, leave_room, emit, Namespace, rooms
import flask_socketio
from flask_session import Session
from pitch import Table, Deck
from threading import Lock
import flask

app = Flask(__name__)
app.debug = True
app.config['SECRET_KEY'] = 'secret'
app.config['SESSION_TYPE'] = 'filesystem'
app.config['TEMPLATES_AUTO_RELOAD'] = True

Session(app)

socketio = SocketIO(app, manage_session=False, async_mode="threading")

tables = {}  # type: Dict[Table]

thread = None
thread_lock = Lock()


@app.route('/', methods=['GET', 'POST'])
def index():
    return render_template('lobby.html')


@app.route('/table', methods=['GET', 'POST'])
def table():
    if request.method == 'POST':
        username = request.form['username']
        table = request.form['table']
        seat = request.form['seat']
        # Store the data in session
        session['username'] = username
        session['table'] = table
        session['seat'] = seat
        # TODO add check for avail seat here
        return render_template('table.html', session=session)
    else:
        if session.get('username') is not None:
            return render_template('table.html', session=session)
        else:
            return redirect(url_for('index'))


class PitchNamespace(Namespace):
    def on_join(self, message):
        table_name = session.get('table')
        username = session.get('username')
        seat = session.get('seat')
        join_room(table_name)
        print("join", username, table_name, seat)

        # sio = flask.current_app.extensions['socketio']
        # print(sio.server.manager.rooms)

        emit('status', {'msg': username + ' has joined the table.'}, room=table_name)
        t = tables.setdefault(table_name, Table(id=table_name, tx=self.tx))

    def on_text(self, message):
        table_name = session.get('table')
        username = session.get('username')
        seat = session.get('seat')

        # send this to entire room
        emit('message', {'msg': session.get('username') + ' : ' + message['msg']}, room=table_name)

    def on_leave(self, message):
        table_name = session.get('table')
        username = session.get('username')
        seat = session.get('seat')
        print('left', username, table_name, seat)
        leave_room(table_name)
        del session['table']
        del session['seat']

        emit('status', {'msg': username + ' has left the table.'}, room=table_name)

    def on_disconnect(self):
        table_name = session.get('table')
        username = session.get('username')
        seat = session.get('seat')
        print('disconnect', username, table_name, seat)
        emit('status', {'msg': username + ' has been disconnected.'}, room=table_name)

    def on_connect(self):
        table_name = session.get('table')
        username = session.get('username')
        seat = session.get('seat')
        print('connect', username, table_name, seat)
        emit('status', {'msg': username + ' has been connected.'}, room=table_name)
        session['sid'] = request.sid

        global thread
        with thread_lock:
            if thread is None:
                thread = socketio.start_background_task(self.background_thread)

        t = tables.setdefault(table_name, Table(id=table_name, tx=self.tx))

    def background_thread(self):
        print("Background thread started")
        count = 0
        while True:
            socketio.sleep(5)
            print("Background triggered")
            count += 1
            socketio.emit('status', {'msg': f'count is {count}'}, namespace=self.namespace)

    def on_play(self, message):
        table_name = session.get('table')
        username = session.get('username')
        seat = session.get('seat')
        print('Played', message)

    def on_update(self):
        table_name = session.get('table')
        username = session.get('username')
        seat = session.get('seat')
        t = tables[table_name]
        emit('table', t.get_json())
        emit('hand', t.get_seat(username).get_hand_json())

    def on_deal(self):
        table_name = session.get('table')
        username = session.get('username')
        seat = session.get('seat')
        t = tables[table_name]
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
