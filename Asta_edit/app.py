#               COMANDI UTILI ( dopo aver installatp Python3)
#           DA TERMINALE : python3 -m pip install flask
#           PAGINA ADMIN :http://127.0.0.1:5001/admin_partecipanti


from flask import Flask, request, redirect, url_for, render_template, jsonify, session
from threading import Timer, Lock
import time
import webbrowser
import socket

app = Flask(__name__)
app.secret_key = 'super_secret_key'

# === Variabili globali ===
TIMER_DURATION = 12
current_price = 0
current_bidder = ""
end_time = time.time() + TIMER_DURATION
history = []
lock = Lock()
timer = None
crediti_utenti = {}
auction_id = str(int(time.time()))

# === Funzioni di sistema ===
def reset_timer():
    global end_time, timer
    end_time = time.time() + TIMER_DURATION
    if timer:
        timer.cancel()
    timer = Timer(TIMER_DURATION, timer_expired)
    timer.start()

def timer_expired():
    global current_bidder, current_price
    with lock:
        if current_bidder in crediti_utenti:
            crediti_utenti[current_bidder] -= int(current_price)

# === Rotte principali ===
@app.route('/')
def index():
    if 'username' not in session:
        return redirect(url_for('setname_page'))

    username = session['username']
    if username not in crediti_utenti:
        crediti_utenti[username] = 500

    time_left = max(0, int(end_time - time.time()))
    is_admin = request.remote_addr == '127.0.0.1'

    return render_template("index.html",
                           time_left=time_left,
                           username=username,
                           crediti=crediti_utenti[username],
                           is_admin=is_admin)

@app.route('/setname_page')
def setname_page():
    return render_template("setname.html")

@app.route('/setname', methods=['POST'])
def setname():
    username = request.form['username']
    session['username'] = username
    if username not in crediti_utenti:
        crediti_utenti[username] = 500
    return redirect(url_for('index'))

@app.route('/offerta', methods=['POST'])
def offerta():
    global current_price, current_bidder, history
    name = request.form.get('name', 'Anonimo')
    session['username'] = name
    amount = float(request.form['amount'])

    with lock:
        if name not in crediti_utenti:
            crediti_utenti[name] = 500

        if crediti_utenti[name] < amount or time.time() > end_time:
            return redirect(url_for('index'))

        if amount > current_price:
            current_price = amount
            current_bidder = name
            history.insert(0, {'name': name, 'amount': amount})
            reset_timer()

    return redirect(url_for('index'))

@app.route('/rilancia', methods=['POST'])
def rilancia():
    global current_price, current_bidder, history
    data = request.get_json()
    name = data.get('name', 'Anonimo')
    session['username'] = name

    with lock:
        if name not in crediti_utenti:
            crediti_utenti[name] = 500

        if crediti_utenti[name] < 1 or time.time() > end_time:
            return '', 204

        current_price += 1
        current_bidder = name
        history.insert(0, {'name': name, 'amount': current_price})
        reset_timer()

    return '', 204

@app.route('/nuova_asta', methods=['POST'])
def nuova_asta():
    global current_price, current_bidder, history, auction_id
    with lock:
        current_price = 0
        current_bidder = ""
        history = []
        auction_id = str(int(time.time()))
        reset_timer()

    origin = request.form.get('origin')
    if origin == 'admin':
        return redirect(url_for('admin_partecipanti'))
    return redirect(url_for('index'))

# === API JSON ===
@app.route('/auction_id')
def get_auction_id():
    return jsonify({'auction_id': auction_id})

@app.route('/time')
def get_time():
    remaining = max(0, int(end_time - time.time()))
    return jsonify({'remaining': remaining})

@app.route('/history')
def get_history():
    return jsonify(history)

@app.route('/crediti')
def get_crediti():
    username = session.get('username')
    crediti = crediti_utenti.get(username, 0)
    return jsonify({'crediti': crediti})

# === Nuova route elimina_utente ===
@app.route('/elimina_utente', methods=['POST'])
def elimina_utente():
    if request.remote_addr != '127.0.0.1':
        return 'Accesso negato', 403
    utente = request.form.get('utente')
    with lock:
        if utente in crediti_utenti:
            del crediti_utenti[utente]
    return redirect(url_for('admin_partecipanti'))

# === ADMIN ===
@app.route('/admin_partecipanti', methods=['GET', 'POST'])
def admin_partecipanti():
    if request.remote_addr != '127.0.0.1':
        return 'Accesso negato', 403

    if request.method == 'POST':
        utente = request.form.get('utente')
        nuovi_crediti = request.form.get('nuovi_crediti')
        if utente in crediti_utenti:
            try:
                crediti_utenti[utente] = int(nuovi_crediti)
            except ValueError:
                pass
        return redirect(url_for('admin_partecipanti'))

    ip_server = get_ip_wifi()  # Usa la funzione sopra
    return render_template('admin.html', lista_utenti=crediti_utenti, ip_server=ip_server)
    import socket
def get_ip_wifi():
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        # Connessione fittizia verso un server esterno per determinare l'interfaccia di uscita
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
    except Exception:
        ip = "127.0.0.1"
    finally:
        s.close()
    return ip
    return render_template('admin.html', lista_utenti=crediti_utenti, ip_server=ip_server)

# === Reset crediti ===
@app.route('/reset', methods=['POST'])
def reset_totale():
    global current_price, current_bidder, history, end_time, timer, crediti_utenti
    if request.remote_addr != '127.0.0.1':
        return 'Accesso negato', 403

    with lock:
        current_price = 0
        current_bidder = ""
        history = []
        crediti_utenti.clear()
        end_time = time.time() + TIMER_DURATION
        if timer:
            timer.cancel()
        reset_timer()
    return 'Reset completato', 200

# === Avvio dell'app ===
if __name__ == '__main__':
    with lock:
        reset_timer()
    
    # Apri il browser alla pagina admin
    webbrowser.open('http://127.0.0.1:5001/admin_partecipanti')

    app.run(host="0.0.0.0", port=5001, debug=True)