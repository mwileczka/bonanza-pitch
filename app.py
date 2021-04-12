import pprint

from flask import Flask, render_template, request, redirect, url_for, session
from flask_socketio import SocketIO, join_room, leave_room, emit, Namespace, rooms
import flask_socketio
from bot import BotPlayerClient

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
tables['Matrix'] = Table('Matrix')

players = {}
bot_clients = {}

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


class WebPlayer(Player):
    def __init__(self, username, session_token, ws_token):
        self.session_token = session_token
        self.ws_token = ws_token
        self.username = username

    def tx(self, event, args):
        socketio.emit(event, args, to=self.ws_token, namespace='/table')


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
            player = WebPlayer(username, session.sid, request.sid)
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

        t.update()

    def on_text(self, message):
        table_name = session.get('table')
        username = session.get('username')
        seat = session.get('seat')

        # send this to entire room
        emit('message', {'msg': session.get('username') + ' : ' + message['msg']}, room=table_name)

    def on_leave(self, message):
        table_name = session.get('table')
        username = session.get('username')
        seat_idx = session.get('seat')
        print('left', username, table_name, seat_idx)
        leave_room(table_name)
        del session['table']
        del session['seat']

        t = tables.get(table_name)
        t.seats[seat_idx].player = None

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
            socketio.sleep(0.5)
            for t in tables.values():
                t.check()

            # socketio.emit('status', {'msg': f'count is {count}'}, namespace=self.namespace)

            if '/table' not in socketio.server.manager.rooms:
                print('No more tables - Background thread stopped')
                break

    def on_play(self, message):
        table_name = session.get('table')
        username = session.get('username')
        seat = session.get('seat')
        t = tables.get(table_name)
        t.play_card(seat, message)

    def on_discard(self, message):
        table_name = session.get('table')
        username = session.get('username')
        seat = session.get('seat')
        t = tables.get(table_name)
        t.discard(seat, message)

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

    def on_add_bots(self):
        table_name = session.get('table')
        t = tables[table_name]
        for idx in range(0, 4):
            if not t.seats[idx].player:
                bot = BotPlayerClient(table_name, idx)
                bot_clients[bot.username] = bot

    def on_bid(self, args):
        print("Got bid", args)
        table_name = session.get('table')
        username = session.get('username')
        seat = session.get('seat')
        t = tables[table_name]
        t.bid(seat, args)

    def on_suit(self, args):
        print("Got suit", args)
        table_name = session.get('table')
        username = session.get('username')
        seat = session.get('seat')
        t = tables[table_name]
        t.suit(args)

class LobbyNamespace(Namespace):
    def on_req_lobby(self):
        print('on_req_lobby')
        emit('lobby', [t.get_lobby_json() for t in tables.values()])

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

if __name__ == '__main__':
    socketio.run(app)
