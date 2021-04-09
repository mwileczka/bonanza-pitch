from flask import Flask, render_template, request, redirect, url_for, session
from flask_socketio import SocketIO, join_room, leave_room, emit, Namespace, rooms
import flask_socketio

import pitch
from flask_session import Session
from pitch import Table, Deck, Player
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

players = {}

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
        seat = int(request.form['seat'])
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


class TableNamespace(Namespace):
    def on_connect(self):
        table_name = session.get('table')
        username = session.get('username')
        seat = session.get('seat')
        print('connect', username, table_name, seat)
        emit('status', {'msg': f'{username} has been connected.'}, room=table_name)

        join_room(table_name)

        if username in players:
            player = players[username]
        else:
            player = Player(username)
            players[username] = player

        if player.session_token and player.session_token != session.sid:
            print('replacing player session')
        player.session_token = session.sid

        if player.ws_token and player.ws_token != request.sid:
            print('replacing ws token')
        player.ws_token = request.sid

        global thread
        with thread_lock:
            if thread is not None and not thread.is_alive():
                thread = None
            if thread is None:
                thread = socketio.start_background_task(self.background_thread)

        t = tables.setdefault(table_name, Table(id=table_name))
        t.seats[seat].player = player

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

        emit('status', {'msg': f'{username} has left the table.'}, room=table_name)

    def on_disconnect(self):
        table_name = session.get('table')
        username = session.get('username')
        seat = session.get('seat')
        print('disconnect', username, table_name, seat)
        leave_room(table_name)
        players[username].ws_token = None
        emit('status', {'msg': username + ' has been disconnected.'}, room=table_name)

        if request.sid == players[username].ws_token:
            players[username].ws_token = None

    def background_thread(self):
        print("Background thread started")
        count = 0
        while True:
            socketio.sleep(5)
            print("Background triggered")
            count += 1
            socketio.emit('status', {'msg': f'count is {count}'}, namespace=self.namespace)

            if '/table' not in socketio.server.manager.rooms:
                print('No more tables - Background thread stopped')
                break

    def on_play(self, message):
        table_name = session.get('table')
        username = session.get('username')
        seat = session.get('seat')
        t = tables.get(table_name)
        t.play_card(seat, message.get('card'))

    def on_update(self):
        table_name = session.get('table')
        seat = session.get('seat')
        t = tables[table_name]
        t.update(seat_idx=seat)

    def on_deal(self):
        table_name = session.get('table')
        username = session.get('username')
        seat = session.get('seat')
        t = tables[table_name]
        t.deal()

class LobbyNamespace(Namespace):
    def on_req_lobby(self):
        print('on_req_lobby')
        emit('lobby', [{'name': 'Matrix', 'seats': [None, 'Laura', 'Mike', None]}])

    def on_disconnect(self):
        username = session.get('username')
        print('disconnect', username)
        leave_room('lobby')

    def on_connect(self):
        username = session.get('username')
        print('connect', username)
        join_room('lobby')


socketio.on_namespace(TableNamespace('/table'))
socketio.on_namespace(LobbyNamespace('/lobby'))

def sio_tx(to, event, args):
    print('sio_tx', to, event, args)
    socketio.emit(event, args, to=to, namespace='/table')

# override the transmitter to use socketio
pitch.base_tx = sio_tx

if __name__ == '__main__':
    socketio.run(app)
