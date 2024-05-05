import pprint
import time
import math
import os
from flask import Flask, render_template, request, redirect, url_for, session
from flask_socketio import SocketIO, join_room, leave_room, emit, Namespace, rooms
import flask_socketio
from bot import bot_client_proc, bot_client_username, BotPlayerClient

from flask_session import Session
from pitch import Table, Deck, Player, Seat
from threading import Lock
import flask
import multiprocessing

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


# logging.basicConfig(level=logging.DEBUG, filename='pitch.log', filemode='w')
# console = logging.StreamHandler()
# console.setLevel(logging.DEBUG)
# logging.getLogger('').addHandler(console)

def version_tick():
    return math.floor(time.time())

app.jinja_env.globals.update(version_tick=version_tick)

@app.route('/', methods=['GET','POST'])
def index():
    if request.method == 'POST':
        session.pop('username', None)
        session.pop('is_bot', None)
        session.pop('table', None)
        session.pop('seat', None)

    if 'username' in session:
        return redirect(url_for('lobby'))
    return render_template('login.html')

@app.route('/lobby', methods=['GET', 'POST'])
def lobby():
    if request.method == 'POST':
        if 'table' in request.form:
            new_table_name = request.form['table']
            if new_table_name not in tables:
                tables[new_table_name] = Table(id=new_table_name)
        else:
            username = request.form['username']
            is_bot = bool(request.form['bot'])
            # Store the data in session
            session['username'] = username
            session['is_bot'] = is_bot
        # TODO add check for avail seat here

    if session.get('seat') is not None:
        return redirect(url_for('table'))

    if session.get('username') is not None:
        return render_template('lobby.html', session=session, tables=tables)
    else:
        return redirect(url_for('index'))

@app.route('/table', methods=['GET', 'POST'])
def table():
    if request.method == 'POST':
        if 'username' in request.form:
            username = request.form['username']
            session['username'] = username
        if 'is_bot' in request.form:
            is_bot = bool(request.form['bot'])
            session['is_bot'] = is_bot

        table = request.form['table']
        seat = int(request.form['seat'])

        # Store the data in session
        session['table'] = table
        session['seat'] = seat

        # TODO add check for avail seat here

    if session.get('table') is not None:
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
        t.seats[seat].state = Seat.State.Ready

        t.update()

        t.re_request(seat)

        update_lobby()

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
        if t:
            t.seats[seat_idx].player = None
            t.seats[seat_idx].state = Seat.State.Disconnected

        emit('status', {'msg': f'{username} has left the table.'}, room=table_name)

        update_lobby()

    def on_disconnect(self):
        table_name = session.get('table')
        username = session.get('username')
        seat_idx = session.get('seat')
        print('disconnect', username, table_name, seat_idx)
        leave_room(table_name)
        players[username].ws_token = None
        emit('status', {'msg': username + ' has been disconnected.'}, room=table_name)

        t = tables.get(table_name)
        if t:
            t.seats[seat_idx].player = None
            t.seats[seat_idx].state = Seat.State.Disconnected

        if request.sid == players[username].ws_token:
            players[username].ws_token = None

    def background_thread(self):
        print("Background thread started")
        count = 0
        while True:
            socketio.sleep(0.5)
            for t in tables.values():
                t.check()

            for bk in list(bot_clients.keys()):
                if not bot_clients[bk].is_in_use():
                    print(f"Removing bot {bot_clients[bk].username}")
                    del bot_clients[bk]

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

    def on_kick(self, seat_idx):
        table_name = session.get('table')
        t = tables.get(table_name)
        t.kick(seat_idx)

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

    def on_deal(self, message):
        table_name = session.get('table')
        username = session.get('username')
        seat = session.get('seat')
        t = tables[table_name]
        force = message.get('force', False) if message else False
        test_mode = message.get('test_mode', None) if message else False
        t.deal(seat, force, test_mode)

    def on_add_bots(self):
        table_name = session.get('table')
        t = tables[table_name]
        for idx in range(0, 4):
            if not t.seats[idx].player:
                # proc = multiprocessing.Process(
                #    target=bot_client_proc,
                #    args=(table_name, idx, bot_client_username(), 'http://127.0.0.1:5000'))
                # proc.start()
                bot = BotPlayerClient(table=table_name, seat=idx,
                                      username=bot_client_username(),
                                      url=f'http://127.0.0.1:{os.environ.get("PORT",5000)}')
                bot_clients[(table_name, idx)] = bot

    def on_bid(self, args):
        print("Got bid", args)
        table_name = session.get('table')
        seat = session.get('seat')
        t = tables[table_name]
        t.bid(seat, args)

    def on_suit(self, args):
        print("Got suit", args)
        table_name = session.get('table')
        seat = session.get('seat')
        t = tables[table_name]
        t.suit(seat, args)

    def on_kitty(self):
        print("Got kitty")
        table_name = session.get('table')
        seat = session.get('seat')
        t = tables[table_name]
        t.show_kitty(seat)

def update_lobby():
    socketio.emit('lobby', [t.get_lobby_json() for t in tables.values()], to='lobby', namespace='/lobby')

class LobbyNamespace(Namespace):
    def on_req_lobby(self):
        print('on_req_lobby')
        update_lobby()

    def on_disconnect(self):
        username = session.get('username')
        print('disconnect', username)
        leave_room('lobby')

    def on_connect(self):
        username = session.get('username')
        print('connect', username)
        join_room('lobby')

    def on_create(self, table_name):
        print('create', table_name)
        if table_name not in tables:
            tables[table_name] = Table(table_name)

        update_lobby()

    def on_delete(self, table_name):
        print('delete', table_name)
        t = tables.pop(table_name, None)
        if t:
            t.kick()

        update_lobby()


socketio.on_namespace(TableNamespace('/table'))
socketio.on_namespace(LobbyNamespace('/lobby'))

if __name__ == '__main__':
    port = int(os.environ.setdefault('PORT', '5000'))
    socketio.run(app, host='0.0.0.0', port=port)
