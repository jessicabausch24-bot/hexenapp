from flask import Flask, render_template, request, redirect, session, abort
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
import os
import json
import uuid
import datetime
import psycopg2

app = Flask(__name__)
app.secret_key = "super_secret_key"

DATA_DIR = os.environ.get("DATA_DIR", "data")

USER_FILE = os.path.join(DATA_DIR, "users.json")
ORDERS_FILE = os.path.join(DATA_DIR, "orders.json")
PRODUCTS_FILE = os.path.join(DATA_DIR, "products.json")
BUS_EVENTS_FILE = os.path.join(DATA_DIR, "bus_events.json")
BUS_RESERVIERUNGEN_FILE = os.path.join(DATA_DIR, "bus_reservierungen.json")
STORNO_FILE = os.path.join(DATA_DIR, "stornogebuehren.json")
DATABASE_URL = os.environ.get("DATABASE_URL")
print("DATABASE_URL CHECK:", DATABASE_URL.replace("0QlRTReZFTD8u0px", "****") if DATABASE_URL else "FEHLT")

def get_db():
    if not DATABASE_URL:
        raise Exception("DATABASE_URL fehlt in Render Environment")
    return psycopg2.connect(DATABASE_URL, sslmode="require")

# ---------------------------------------------------------
# DATEI-HILFSFUNKTIONEN
# ---------------------------------------------------------

def ensure_data_files():
    os.makedirs(DATA_DIR, exist_ok=True)

    if not os.path.exists(USER_FILE):
        with open(USER_FILE, "w", encoding="utf-8") as f:
            json.dump({}, f, indent=4, ensure_ascii=False)

    if not os.path.exists(ORDERS_FILE):
        with open(ORDERS_FILE, "w", encoding="utf-8") as f:
            json.dump([], f, indent=4, ensure_ascii=False)

    if not os.path.exists(BUS_EVENTS_FILE):
        with open(BUS_EVENTS_FILE, "w", encoding="utf-8") as f:
            json.dump([], f, indent=4, ensure_ascii=False)

    if not os.path.exists(BUS_RESERVIERUNGEN_FILE):
        with open(BUS_RESERVIERUNGEN_FILE, "w", encoding="utf-8") as f:
            json.dump([], f, indent=4, ensure_ascii=False)
    
    if not os.path.exists(STORNO_FILE):
        with open(STORNO_FILE, "w", encoding="utf-8") as f:
            json.dump([], f, indent=4, ensure_ascii=False)


# ---------------- USERS ----------------

def init_db():
    conn = get_db()
    cur = conn.cursor()
    cur.execute("""
        CREATE TABLE IF NOT EXISTS users (
            email TEXT PRIMARY KEY,
            name TEXT NOT NULL,
            password TEXT NOT NULL
        )
    """)
    conn.commit()
    cur.close()
    conn.close()


def load_users():
    init_db()
    conn = get_db()
    cur = conn.cursor()
    cur.execute("SELECT email, name, password FROM users")
    rows = cur.fetchall()
    cur.close()
    conn.close()

    users = {}
    for email, name, password in rows:
        users[email] = {
            "name": name,
            "password": password
        }

    return users


def save_users(users):
    init_db()
    conn = get_db()
    cur = conn.cursor()

    cur.execute("DELETE FROM users")

    for email, user in users.items():
        cur.execute("""
            INSERT INTO users (email, name, password)
            VALUES (%s, %s, %s)
        """, (email, user["name"], user["password"]))

    conn.commit()
    cur.close()
    conn.close()

# ---------------- ORDERS ----------------

def load_orders():
    ensure_data_files()
    with open(ORDERS_FILE, "r", encoding="utf-8") as f:
        return json.load(f)


def save_orders(orders):
    ensure_data_files()
    with open(ORDERS_FILE, "w", encoding="utf-8") as f:
        json.dump(orders, f, indent=4, ensure_ascii=False)


def save_order(order):
    orders = load_orders()
    orders.append(order)
    save_orders(orders)


# ---------------- BUS EVENTS ----------------

def load_bus_events():
    ensure_data_files()
    with open(BUS_EVENTS_FILE, "r", encoding="utf-8") as f:
        return json.load(f)


def save_bus_events(events):
    ensure_data_files()
    with open(BUS_EVENTS_FILE, "w", encoding="utf-8") as f:
        json.dump(events, f, indent=4, ensure_ascii=False)


# ---------------- BUS RESERVIERUNGEN ----------------

def load_bus_reservierungen():
    ensure_data_files()
    with open(BUS_RESERVIERUNGEN_FILE, "r", encoding="utf-8") as f:
        return json.load(f)


def save_bus_reservierungen(reservierungen):
    ensure_data_files()
    with open(BUS_RESERVIERUNGEN_FILE, "w", encoding="utf-8") as f:
        json.dump(reservierungen, f, indent=4, ensure_ascii=False)

def load_stornogebuehren():
    ensure_data_files()
    with open(STORNO_FILE, "r", encoding="utf-8") as f:
        return json.load(f)


def save_stornogebuehren(stornos):
    ensure_data_files()
    with open(STORNO_FILE, "w", encoding="utf-8") as f:
        json.dump(stornos, f, indent=4, ensure_ascii=False)
# ---------------------------------------------------------
# PRODUKTE LADEN & SPEICHERN
# ---------------------------------------------------------

def save_products():
    with open(PRODUCTS_FILE, "w", encoding="utf-8") as f:
        json.dump(products, f, indent=4, ensure_ascii=False)


def load_products():
    global products
    if os.path.exists(PRODUCTS_FILE):
        with open(PRODUCTS_FILE, "r", encoding="utf-8") as f:
            products = json.load(f)

# ---------------------------------------------------------
# LOGIN / ADMIN HILFSFUNKTIONEN
# ---------------------------------------------------------

def is_logged_in():
    return "user" in session and "email" in session


def admin_required():
    return session.get("email", "").lower() == "jessica.bausch24@gmail.com"

# ---------------------------------------------------------
# PRODUKTDATEN
# ---------------------------------------------------------

haes_teile_produkte = [
    {
        "id": 1,
        "name": "Lila Hexenpulli",
        "typ": "Oberteil",
        "preis": 49.90,
        "groessen": ["S", "M", "L", "XL", "XXL", "XXXL", "110", "116", "122", "128", "134", "140", "146", "152", "158"],
        "bild": "placeholder.png",
        "extras": []
    },
    {
        "id": 2,
        "name": "Hexenhose",
        "typ": "Hose",
        "preis": 39.90,
        "groessen": ["S", "M", "L", "XL", "XXL", "XXXL", "110", "116", "122", "128", "134", "140", "146", "152", "158"],
        "bild": "placeholder.png",
        "extras": []
    },
    {
        "id": 3,
        "name": "Hexenrock",
        "typ": "Rock",
        "preis": 29.90,
        "groessen": ["Einheitsgröße Erwachsene", "110", "116", "122", "128", "134", "140", "146", "152", "158"],
        "bild": "placeholder.png",
        "extras": []
    },
    {
        "id": 4,
        "name": "Schürze",
        "typ": "Zubehör",
        "preis": 19.90,
        "groessen": ["Erwachsene", "Kinder"],
        "bild": "placeholder.png",
        "extras": []
    },
    {
        "id": 5,
        "name": "Stola",
        "typ": "Zubehör",
        "preis": 24.90,
        "groessen": ["Extra Groß", "Normal", "Kinder"],
        "bild": "placeholder.png",
        "extras": []
    },
    {
        "id": 6,
        "name": "Maske",
        "typ": "Zubehör",
        "preis": 14.90,
        "groessen": ["Erwachsene", "Kinder"],
        "bild": "Maske.png",
        "extras": []
    },
    {
        "id": 7,
        "name": "Kopftuch",
        "typ": "Zubehör",
        "preis": 9.90,
        "groessen": [],
        "bild": "placeholder.png",
        "extras": []
    },
]

masken_zubehoer_produkte = [
    {
        "id": 101,
        "name": "Schaumstoff",
        "typ": "Maskenzubehör",
        "preis": 5.90,
        "groessen": [],
        "bild": "placeholder.png",
        "extras": []
    },
    {
        "id": 102,
        "name": "Hanfzöpfe",
        "typ": "Maskenzubehör",
        "preis": 7.90,
        "groessen": [],
        "bild": "placeholder.png",
        "extras": []
    },
    {
        "id": 103,
        "name": "Zackenlitze Kopftuch",
        "typ": "Maskenzubehör",
        "preis": 6.90,
        "groessen": [],
        "bild": "placeholder.png",
        "extras": []
    },
    {
        "id": 104,
        "name": "Wappen Kopftuch",
        "typ": "Maskenzubehör",
        "preis": 4.90,
        "groessen": [],
        "bild": "placeholder.png",
        "extras": []
    },
    {
        "id": 105,
        "name": "Maskennummer",
        "typ": "Maskenzubehör",
        "preis": 3.90,
        "groessen": [],
        "bild": "placeholder.png",
        "extras": []
    },
    {
        "id": 106,
        "name": "Klettband",
        "typ": "Maskenzubehör",
        "preis": 2.90,
        "groessen": [],
        "bild": "placeholder.png",
        "extras": []
    },
    {
        "id": 107,
        "name": "Gummi",
        "typ": "Maskenzubehör",
        "preis": 2.50,
        "groessen": [],
        "bild": "placeholder.png",
        "extras": []
    },
]

merchandise_produkte = [
    {
        "id": 201,
        "name": "Hexenbecher",
        "typ": "Merchandise",
        "preis": 12.90,
        "groessen": [],
        "bild": "hexenbecher.jpg",
        "extras": [
            {"name": "name_aufdruck", "label": "Name für Aufdruck", "type": "text"},
            {"name": "mit_deckel", "label": "Mit Deckel", "type": "select", "options": ["Nein", "Ja"]}
        ]
    },
    {
        "id": 202,
        "name": "Schnapsbecher",
        "typ": "Merchandise",
        "preis": 8.90,
        "groessen": [],
        "bild": "schnapsbecher.jpg",
        "extras": [
            {"name": "name_aufdruck", "label": "Name für Aufdruck", "type": "text"}
        ]
    },
    {
        "id": 203,
        "name": "Fleecejacke",
        "typ": "Merchandise",
        "preis": 39.90,
        "groessen": ["128", "134", "140", "146", "152", "158", "164", "S", "M", "L", "XL", "XXL", "3XL"],
        "bild": "fleecejacke.jpg",
        "extras": [
            {"name": "name_aufdruck", "label": "Name für Aufdruck", "type": "text"}
        ]
    },
    {
        "id": 204,
        "name": "Hexen T-Shirt",
        "typ": "Merchandise",
        "preis": 19.90,
        "groessen": ["128", "134", "140", "146", "152", "158", "164", "S", "M", "L", "XL", "XXL", "3XL"],
        "bild": "hexen_tshirt.jpg",
        "extras": []
    },
    {
        "id": 205,
        "name": "Stirnband",
        "typ": "Merchandise",
        "preis": 9.90,
        "groessen": ["Erwachsene", "Kinder"],
        "bild": "stirnband.jpg",
        "extras": []
    },
    {
        "id": 206,
        "name": "Mütze",
        "typ": "Merchandise",
        "preis": 11.90,
        "groessen": ["Erwachsene", "Kinder"],
        "bild": "muetze.jpg",
        "extras": []
    },
    {
        "id": 207,
        "name": "Mütze mit Bommel",
        "typ": "Merchandise",
        "preis": 13.90,
        "groessen": ["Erwachsene", "Kinder"],
        "bild": "muetze_bommel.jpg",
        "extras": []
    },
    {
        "id": 208,
        "name": "Käppi",
        "typ": "Merchandise",
        "preis": 14.90,
        "groessen": ["Erwachsene", "Kinder"],
        "bild": "kaeppi.jpg",
        "extras": []
    },
    {
        "id": 209,
        "name": "Mini Hexenmaske",
        "typ": "Merchandise",
        "preis": 16.90,
        "groessen": ["groß", "klein"],
        "bild": "mini_hexenmaske.jpg",
        "extras": []
    }
]

sonstiges_produkte = []

products = {
    "haes_teile": haes_teile_produkte,
    "masken_zubehoer": masken_zubehoer_produkte,
    "merchandise": merchandise_produkte,
    "sonstiges": sonstiges_produkte
}


def get_product(produkt_id):
    for kategorie in products.values():
        produkt = next((p for p in kategorie if p["id"] == produkt_id), None)
        if produkt:
            return produkt
    return None


# ---------------------------------------------------------
# MAIL-FUNKTION
# ---------------------------------------------------------

def send_email(subject, body, to_email):
    print("----- BESTELLBESTÄTIGUNG -----")
    print("An:", to_email)
    print("Betreff:", subject)
    print(body)
    print("-----------------------------")
    return True


# ---------------------------------------------------------
# STARTSEITE
# ---------------------------------------------------------

@app.route('/')
def index():
    if is_logged_in():
        return redirect('/dashboard')
    return redirect('/login')
# ---------------------------------------------------------
# DATENSCHUTZ & IMPRESSUM
# ---------------------------------------------------------

@app.route('/datenschutz')
def datenschutz():
    return render_template('datenschutz.html')

@app.route('/impressum')
def impressum():
    return render_template('impressum.html')

# ---------------------------------------------------------
# LOGIN
# ---------------------------------------------------------

@app.route('/login', methods=['GET', 'POST'])
def login():
    users = load_users()

    if request.method == 'POST':
        email = request.form.get('email', '').strip()
        password = request.form.get('password', '')

        if email in users:
            user = users[email]

            if check_password_hash(user["password"], password):
                session['user'] = user["name"]
                session['email'] = email
                return redirect('/dashboard')

        return render_template('login.html', error="E-Mail oder Passwort falsch")

    return render_template('login.html')


# ---------------------------------------------------------
# REGISTRIERUNG
# ---------------------------------------------------------
@app.route('/register', methods=['GET', 'POST'])
def register():
    users = load_users()

    if request.method == 'POST':
        name = request.form.get('name', '').strip()
        email = request.form.get('email', '').strip()
        password = request.form.get('password', '')

        if not name or not email or not password:
            return render_template('register.html', error="Bitte alle Felder ausfüllen")

        if len(name.split()) < 2:
            return render_template('register.html', error="Bitte Vor- und Nachname eingeben")

        if email in users:
            return render_template('register.html', error="E-Mail existiert bereits")

        users[email] = {
            "name": name,
            "password": generate_password_hash(password)
        }
        save_users(users)
        return redirect('/login')

    return render_template('register.html')


# ---------------------------------------------------------
# LOGOUT
# ---------------------------------------------------------
@app.route('/logout')
def logout():
    session.clear()
    return redirect('/login')


# ---------------------------------------------------------
# DASHBOARD
# ---------------------------------------------------------

@app.route('/dashboard')
def dashboard():
    if not is_logged_in():
        return redirect('/login')
    return render_template('dashboard.html', user=session['user'])
@app.route('/meine-bestellungen')
def meine_bestellungen():
    if not is_logged_in():
        return redirect('/login')

    email = session.get('email')
    orders = load_orders()

    user_orders = [
        order for order in orders
        if order.get("email") == email
    ]

    user_orders = list(reversed(user_orders))

    return render_template(
        "meine_bestellungen.html",
        orders=user_orders
    )
# ---------------------------------------------------------
# MEINE RESERVIERUNGEN
# ---------------------------------------------------------
@app.route('/reservierungen')
def reservierungen():
    if not is_logged_in():
        return redirect('/login')

    email = session.get('email')
    reservierungen = load_bus_reservierungen()

    meine_reservierungen = [
        r for r in reservierungen
        if r.get("email") == email
    ]

    heute = datetime.datetime.now().date()

    for r in meine_reservierungen:
        r["stornogebuehr"] = False
        r["stornierbar_kostenlos"] = False

        datum_roh = r.get("veranstaltungsdatum", "")

        event_date = None

        # Format aus HTML date input: 2026-02-07
        try:
            event_date = datetime.datetime.strptime(datum_roh, "%Y-%m-%d").date()
        except:
            pass

        # Falls alte Daten so gespeichert wurden: 07.02.2026
        if event_date is None:
            try:
                event_date = datetime.datetime.strptime(datum_roh, "%d.%m.%Y").date()
            except:
                pass

        if event_date:
            tage_bis_event = (event_date - heute).days

            if tage_bis_event >= 5:
                r["stornierbar_kostenlos"] = True
            else:
                r["stornogebuehr"] = True
        else:
            r["stornogebuehr"] = True

    meine_reservierungen = list(reversed(meine_reservierungen))

    return render_template(
        "reservierungen.html",
        reservierungen=meine_reservierungen
    )
# ---------------------------------------------------------
# BUS KALENDER
# ---------------------------------------------------------

@app.route('/bus')
def bus():
    if not is_logged_in():
        return redirect('/login')

    veranstaltungen = load_bus_events()
    reservierungen = load_bus_reservierungen()

    belegung = {}

    for v in veranstaltungen:
        belegung[v["id"]] = sum(
            r.get("anzahl", 0)
            for r in reservierungen
            if r.get("veranstaltung_id") == v["id"]
        )

    return render_template(
        "bus.html",
        veranstaltungen=veranstaltungen,
        belegung=belegung
    )


# ---------------------------------------------------------
# BUS DETAIL / RESERVIERUNG
# ---------------------------------------------------------

@app.route('/bus/<event_id>', methods=['GET', 'POST'])
def bus_detail(event_id):
    if not is_logged_in():
        return redirect('/login')

    veranstaltungen = load_bus_events()
    reservierungen = load_bus_reservierungen()

    event = next((v for v in veranstaltungen if v["id"] == event_id), None)

    if not event:
        abort(404)

    belegt = sum(
        r.get("anzahl", 0)
        for r in reservierungen
        if r.get("veranstaltung_id") == event_id
    )

    frei = event.get("gesamtplaetze", 0) - belegt

    if request.method == 'POST':
        anzahl = int(request.form.get("anzahl", 1))

        if anzahl > frei:
            return render_template(
                "bus_detail.html",
                event=event,
                belegt=belegt,
                frei=frei,
                error="Es sind nicht mehr genügend Plätze frei."
            )

        reservierung = {
            "id": str(uuid.uuid4()),
            "datum": datetime.datetime.now().strftime("%d.%m.%Y %H:%M"),
            "name": session.get("user"),
            "email": session.get("email"),
            "veranstaltung_id": event["id"],
            "ausfahrt": event.get("titel"),
            "veranstaltungsdatum": event.get("datum"),
            "abfahrtszeit": event.get("abfahrtszeit"),
            "haltestellen": event.get("haltestellen", []),
            "anzahl": anzahl
        }

        reservierungen.append(reservierung)
        save_bus_reservierungen(reservierungen)

        return redirect(f"/bus/{event_id}")

    return render_template(
        "bus_detail.html",
        event=event,
        belegt=belegt,
        frei=frei
    )
# ---------------------------------------------------------
# BUS RESERVIERUNG STORNIEREN
# ---------------------------------------------------------

@app.route('/reservierung-stornieren/<reservierung_id>')
def reservierung_stornieren(reservierung_id):
    if not is_logged_in():
        return redirect('/login')

    reservierungen = load_bus_reservierungen()
    email = session.get("email")

    reservierung = next((r for r in reservierungen if r["id"] == reservierung_id), None)

    if not reservierung:
        return redirect('/reservierungen')

    if reservierung.get("email") != email:
        return redirect('/reservierungen')

    # Prüfen ob Stornogebühr anfällt
    stornogebuehr = False
    datum_roh = reservierung.get("veranstaltungsdatum", "")
    event_date = None

    try:
        event_date = datetime.datetime.strptime(datum_roh, "%Y-%m-%d").date()
    except:
        pass

    if event_date is None:
        try:
            event_date = datetime.datetime.strptime(datum_roh, "%d.%m.%Y").date()
        except:
            pass

    if event_date:
        tage_bis_event = (event_date - datetime.datetime.now().date()).days
        if tage_bis_event < 5:
            stornogebuehr = True
    else:
        stornogebuehr = True

    if stornogebuehr:
        stornos = load_stornogebuehren()
        stornos.append({
            "id": str(uuid.uuid4()),
            "datum": datetime.datetime.now().strftime("%d.%m.%Y %H:%M"),
            "name": reservierung.get("name"),
            "email": reservierung.get("email"),
            "veranstaltung": reservierung.get("ausfahrt"),
            "veranstaltungsdatum": reservierung.get("veranstaltungsdatum"),
            "anzahl": reservierung.get("anzahl", 1),
            "betrag": 15.00
        })
        save_stornogebuehren(stornos)

    reservierungen = [r for r in reservierungen if r["id"] != reservierung_id]
    save_bus_reservierungen(reservierungen)

    return redirect('/reservierungen')
# ---------------------------------------------------------
# SHOP – HAUPTSEITE
# ---------------------------------------------------------

@app.route('/shop')
def shop():
    if not is_logged_in():
        return redirect('/login')
    return render_template('shop.html')


# ---------------------------------------------------------
# SHOP – KATEGORIEN
# ---------------------------------------------------------

@app.route('/shop/haes-teile')
def shop_haes_teile():
    if not is_logged_in():
        return redirect('/login')

    load_products()

    return render_template(
        'haes-teile.html',
        produkte=products.get("haes_teile", [])
    )


@app.route('/shop/masken-zubehoer')
def shop_masken_zubehoer():
    if not is_logged_in():
        return redirect('/login')

    load_products()

    return render_template(
        'masken-zubehoer.html',
        produkte=products.get("masken_zubehoer", [])
    )


@app.route('/shop/merchandise')
def shop_merchandise():
    if not is_logged_in():
        return redirect('/login')

    load_products()

    return render_template(
        'merchandise.html',
        produkte=products.get("merchandise", [])
    )


@app.route('/shop/sonstiges')
def shop_sonstiges():
    if not is_logged_in():
        return redirect('/login')

    load_products()

    return render_template(
        'sonstiges.html',
        produkte=products.get("sonstiges", [])
    )

# ---------------------------------------------------------
# PRODUKTDETAIL
# ---------------------------------------------------------

@app.route('/produkt/<int:produkt_id>')
def produkt_detail(produkt_id):
    if not is_logged_in():
        return redirect('/login')

    produkt = get_product(produkt_id)
    if not produkt:
        abort(404)

    return render_template('produkt_detail.html', produkt=produkt)

# ---------------------------------------------------------
# WARENKORB
# ---------------------------------------------------------

@app.route('/add_to_cart/<int:produkt_id>', methods=['POST'])
def add_to_cart(produkt_id):
    if not is_logged_in():
        return redirect('/login')

    produkt = get_product(produkt_id)
    if produkt is None:
        return redirect('/shop')

    groesse = request.form.get("groesse", "")
    anzahl = int(request.form.get("anzahl", 1))
    anmerkung = request.form.get("anmerkung", "").strip()

    extras_data = {}
    for extra in produkt.get("extras", []):
        extras_data[extra["label"]] = request.form.get(extra["name"], "").strip()

    cart = session.get("cart", [])

    cart.append({
        "id": produkt["id"],
        "name": produkt["name"],
        "preis": produkt["preis"],
        "groesse": groesse,
        "anzahl": anzahl,
        "anmerkung": anmerkung,
        "bild": produkt.get("bild", None),
        "extras": extras_data,
        "groessen_verfuegbar": produkt.get("groessen", [])
    })

    session["cart"] = cart
    session.modified = True

    return redirect('/cart')


@app.route('/cart', methods=['GET', 'POST'])
def cart():
    if not is_logged_in():
        return redirect('/login')

    if 'cart' not in session:
        session['cart'] = []

    cart_items = session.get('cart', [])
    message = None

    if request.method == 'POST':
        if not cart_items:
            return render_template(
                'cart.html',
                cart_items=[],
                total=0,
                message="Der Warenkorb ist leer."
            )

        total = sum(item.get('preis', 0) * item.get('anzahl', 1) for item in cart_items)

        voller_name = session.get('user')
        email = session.get('email')

        order = {
            "id": str(uuid.uuid4()),
            "datum": datetime.datetime.now().strftime("%d.%m.%Y %H:%M"),
            "user": voller_name,
            "email": email,
            "items": cart_items,
            "total": total
        }

        save_order(order)

        if email:
            order_lines = []
            for item in cart_items:
                zeile = f"{item['name']} x{item.get('anzahl', 1)}"

                if item.get('groesse'):
                    zeile += f" (Größe: {item['groesse']})"

                if item.get('extras'):
                    for key, value in item['extras'].items():
                        if value:
                            zeile += f" | {key}: {value}"

                if item.get('anmerkung'):
                    zeile += f" | Anmerkung: {item['anmerkung']}"

                order_lines.append(zeile)

            order_text = "\n".join(order_lines)
            bestelldatum = datetime.datetime.now().strftime("%d.%m.%Y")

            send_email(
                "Ihre Bestellung bei Oachberghexa",
                f"Hallo {voller_name},\n\n"
                f"vielen Dank für Deine Bestellung.\n"
                f"Hiermit bestätigen wir den Eingang Deiner Bestellung vom {bestelldatum}.\n\n"
                f"Bestellübersicht:\n"
                f"{order_text}\n\n"
                f"Gesamtsumme: {total:.2f} €\n",
                email
            )

        session.pop('cart', None)
        message = 'Ihre Bestellung wurde abgeschickt.'

        return render_template('cart.html', cart_items=[], total=0, message=message)

    total = sum(item.get('preis', 0) * item.get('anzahl', 1) for item in cart_items)
    return render_template('cart.html', cart_items=cart_items, total=total, message=message)


@app.route('/update_cart', methods=['POST'])
def update_cart():
    if not is_logged_in():
        return redirect('/login')

    index = int(request.form.get('index'))
    new_amount = int(request.form.get('anzahl'))

    cart = session.get('cart', [])
    if 0 <= index < len(cart):
        cart[index]['anzahl'] = new_amount
        session['cart'] = cart
        session.modified = True

    return redirect('/cart')


@app.route('/remove_from_cart', methods=['POST'])
def remove_from_cart():
    if not is_logged_in():
        return redirect('/login')

    index = int(request.form.get('index'))

    cart = session.get('cart', [])
    if 0 <= index < len(cart):
        cart.pop(index)
        session['cart'] = cart
        session.modified = True

    return redirect('/cart')


@app.route('/update_size', methods=['POST'])
def update_size():
    if not is_logged_in():
        return redirect('/login')

    index = int(request.form.get('index'))
    new_size = request.form.get('groesse', '')

    cart = session.get('cart', [])
    if 0 <= index < len(cart):
        cart[index]['groesse'] = new_size
        session['cart'] = cart
        session.modified = True

    return redirect('/cart')

# ---------------------------------------------------------
# ADMINBEREICH
# ---------------------------------------------------------

@app.route('/admin')
def admin():
    if not admin_required():
        return redirect('/login')
    return render_template('admin.html')


# ---------------------------------------------------------
# ADMINBEREICH - PRODUKTE
# ---------------------------------------------------------

@app.route('/admin/produkte')
def admin_produkte():
    if not admin_required():
        return redirect('/login')

    load_products()

    return render_template(
        'admin-produkte.html',
        haes_teile=products.get("haes_teile", []),
        masken_zubehoer=products.get("masken_zubehoer", []),
        merchandise=products.get("merchandise", []),
        sonstiges=products.get("sonstiges", [])
    )


@app.route('/admin/produkt-hinzufuegen', methods=['GET', 'POST'])
def admin_produkt_hinzufuegen():
    if not admin_required():
        return redirect('/login')

    load_products()

    if request.method == 'POST':
        name = request.form.get('name', '').strip()
        typ = request.form.get('typ', '').strip()
        preis = float(request.form.get('preis', 0))
        kategorie = request.form.get('kategorie', '').strip()
        bild = request.form.get('bild', '').strip()

        groessen_roh = request.form.get('groessen', '').strip()
        groessen = [g.strip() for g in groessen_roh.split(",") if g.strip()] if groessen_roh else []

        bild_datei = request.files.get("bild_upload")
        if bild_datei and bild_datei.filename:
            filename = secure_filename(bild_datei.filename)
            upload_folder = os.path.join("static", "img")
            os.makedirs(upload_folder, exist_ok=True)
            upload_path = os.path.join(upload_folder, filename)
            bild_datei.save(upload_path)
            bild = filename

        if not bild:
            bild = "placeholder.png"

        extras = []

        if request.form.get("extra_name"):
            extras.append({
                "name": "name_aufdruck",
                "label": request.form.get("extra_name"),
                "type": "text"
            })

        if request.form.get("extra_select_label") and request.form.get("extra_select_options"):
            extras.append({
                "name": "extra_select",
                "label": request.form.get("extra_select_label"),
                "type": "select",
                "options": [
                    o.strip()
                    for o in request.form.get("extra_select_options").split(",")
                    if o.strip()
                ]
            })

        if kategorie not in products:
            products[kategorie] = []

        neue_id = max(
            [p["id"] for liste in products.values() for p in liste],
            default=0
        ) + 1

        products[kategorie].append({
            "id": neue_id,
            "name": name,
            "typ": typ,
            "preis": preis,
            "groessen": groessen,
            "bild": bild,
            "extras": extras
        })

        save_products()
        return redirect('/admin/produkte')

    return render_template('admin-produkt-hinzufuegen.html')


@app.route('/admin/produkt-bearbeiten/<int:produkt_id>', methods=['GET', 'POST'])
def admin_produkt_bearbeiten(produkt_id):
    if not admin_required():
        return redirect('/login')

    load_products()

    produkt = get_product(produkt_id)
    if not produkt:
        abort(404)

    if request.method == 'POST':
        try:
            produkt["name"] = request.form.get('name', '').strip()
            produkt["typ"] = request.form.get('typ', '').strip()
            produkt["preis"] = float(request.form.get('preis', 0))

            groessen_roh = request.form.get('groessen', '').strip()
            produkt["groessen"] = [
                g.strip()
                for g in groessen_roh.split(",")
                if g.strip()
            ] if groessen_roh else []

            bild_datei = request.files.get("bild_upload")

            if bild_datei and bild_datei.filename:
                filename = secure_filename(bild_datei.filename)
                upload_folder = os.path.join("static", "img")
                os.makedirs(upload_folder, exist_ok=True)
                upload_path = os.path.join(upload_folder, filename)
                bild_datei.save(upload_path)
                produkt["bild"] = filename
            else:
                produkt["bild"] = request.form.get('bild', '').strip() or "placeholder.png"

            save_products()
            return redirect('/admin/produkte')

        except Exception as e:
            return render_template(
                'admin-produkt-bearbeiten.html',
                produkt=produkt,
                error=f"Fehler beim Speichern: {e}"
            )

    return render_template('admin-produkt-bearbeiten.html', produkt=produkt)


@app.route('/admin/produkt-loeschen/<int:produkt_id>')
def admin_produkt_loeschen(produkt_id):
    if not admin_required():
        return redirect('/login')

    load_products()

    for kat in ["haes_teile", "masken_zubehoer", "merchandise", "sonstiges"]:
        for p in products.get(kat, []):
            if p["id"] == produkt_id:
                products[kat].remove(p)
                save_products()
                return redirect('/admin/produkte')

    return redirect('/admin/produkte')


# ---------------------------------------------------------
# ADMINBEREICH - BESTELLUNGEN
# ---------------------------------------------------------

@app.route('/admin/bestellungen')
def admin_bestellungen():
    if not admin_required():
        return redirect('/login')

    orders = load_orders()
    suche = request.args.get("q", "").strip().lower()

    if suche:
        gefilterte_orders = []

        for order in orders:
            user_match = suche in str(order.get("user", "")).lower()
            email_match = suche in str(order.get("email", "")).lower()
            id_match = suche in str(order.get("id", "")).lower()

            artikel_match = False
            for item in order.get("items", []):
                if suche in str(item.get("name", "")).lower():
                    artikel_match = True
                    break

            if user_match or email_match or id_match or artikel_match:
                gefilterte_orders.append(order)

        orders = gefilterte_orders

    orders = list(reversed(orders))

    return render_template(
        "admin_bestellungen.html",
        orders=orders,
        suche=suche
    )


@app.route('/admin/bestellungen-drucken')
def admin_bestellungen_drucken():
    if not admin_required():
        return redirect('/login')

    orders = load_orders()
    orders = list(reversed(orders))

    gesamt = sum(float(order.get("total", 0)) for order in orders)

    return render_template(
        "admin_bestellungen_drucken.html",
        orders=orders,
        gesamt=gesamt
    )


@app.route('/admin/bestellung/<order_id>')
def admin_bestellung_detail(order_id):
    if not admin_required():
        return redirect('/login')

    orders = load_orders()
    order = next((o for o in orders if o["id"] == order_id), None)

    if not order:
        return "Bestellung nicht gefunden", 404

    return render_template(
        "admin_bestellung_detail.html",
        order=order
    )


@app.route('/admin/bestellung-bearbeiten/<order_id>', methods=['GET', 'POST'])
def admin_bestellung_bearbeiten(order_id):
    if not admin_required():
        return redirect('/login')

    orders = load_orders()
    order = next((o for o in orders if o["id"] == order_id), None)

    if not order:
        return "Bestellung nicht gefunden", 404

    if request.method == 'POST':
        order["user"] = request.form.get("user", "").strip()
        order["email"] = request.form.get("email", "").strip()

        for i, item in enumerate(order.get("items", [])):
            item["name"] = request.form.get(f"name_{i}", item.get("name", "")).strip()
            item["groesse"] = request.form.get(f"groesse_{i}", item.get("groesse", "")).strip()
            item["anzahl"] = int(request.form.get(f"anzahl_{i}", item.get("anzahl", 1)))
            item["anmerkung"] = request.form.get(f"anmerkung_{i}", item.get("anmerkung", "")).strip()

        order["total"] = sum(
            float(item.get("preis", 0)) * int(item.get("anzahl", 1))
            for item in order.get("items", [])
        )

        save_orders(orders)
        return redirect(f'/admin/bestellung/{order_id}')

    return render_template(
        "admin_bestellung_bearbeiten.html",
        order=order
    )


@app.route('/admin/bestellung-loeschen/<order_id>')
def admin_bestellung_loeschen(order_id):
    if not admin_required():
        return redirect('/login')

    orders = load_orders()
    orders = [o for o in orders if o["id"] != order_id]
    save_orders(orders)

    return redirect('/admin/bestellungen')


@app.route('/admin/bestellung-drucken/<order_id>')
def admin_bestellung_drucken(order_id):
    if not admin_required():
        return redirect('/login')

    orders = load_orders()
    order = next((o for o in orders if o["id"] == order_id), None)

    if not order:
        return "Bestellung nicht gefunden", 404

    return render_template(
        "admin_bestellung_drucken.html",
        order=order
    )


@app.route('/admin/bestellliste')
def admin_bestellliste():
    if not admin_required():
        return redirect('/login')

    orders = load_orders()
    orders = list(reversed(orders))

    gesamt = sum(float(order.get("total", 0)) for order in orders)

    return render_template(
        "admin_bestellliste.html",
        orders=orders,
        gesamt=gesamt
    )
# ---------------------------------------------------------
# ADMINBEREICH - USER
# ---------------------------------------------------------

@app.route('/admin/users')
def admin_users():
    if not admin_required():
        return redirect('/login')

    users = load_users()
    return render_template('admin-users.html', users=users)


@app.route('/admin/user-bearbeiten/<path:email>', methods=['GET', 'POST'])
def admin_user_bearbeiten(email):
    if not admin_required():
        return redirect('/login')

    users = load_users()

    if email not in users:
        abort(404)

    user = users[email]

    if request.method == 'POST':
        neuer_name = request.form.get('name', '').strip()
        neue_email = request.form.get('email', '').strip()
        neues_passwort = request.form.get('password', '').strip()

        if not neuer_name or not neue_email:
            return render_template(
                'admin-user-bearbeiten.html',
                current_email=email,
                user=user,
                error="Name und E-Mail dürfen nicht leer sein."
            )

        if neue_email != email and neue_email in users:
            return render_template(
                'admin-user-bearbeiten.html',
                current_email=email,
                user=user,
                error="Diese E-Mail existiert bereits."
            )

        neuer_user_datensatz = {
            "name": neuer_name,
            "password": user["password"]
        }

        if neues_passwort:
            neuer_user_datensatz["password"] = generate_password_hash(neues_passwort)

        if neue_email != email:
            del users[email]
            users[neue_email] = neuer_user_datensatz

            if session.get("email") == email:
                session["email"] = neue_email
                session["user"] = neuer_name
        else:
            users[email] = neuer_user_datensatz

            if session.get("email") == email:
                session["user"] = neuer_name

        save_users(users)
        return redirect('/admin/users')

    return render_template(
        'admin-user-bearbeiten.html',
        current_email=email,
        user=user
    )


@app.route('/admin/user-loeschen/<path:email>')
def admin_user_loeschen(email):
    if not admin_required():
        return redirect('/login')

    users = load_users()

    if email in users:
        del users[email]
        save_users(users)

    return redirect('/admin/users')


# ---------------------------------------------------------
# ADMIN - BUS VERANSTALTUNGEN
# ---------------------------------------------------------

@app.route('/admin/bus')
def admin_bus_events():
    if not admin_required():
        return redirect('/login')

    events = load_bus_events()
    reservierungen = load_bus_reservierungen()

    belegung = {}
    for event in events:
        event_id = event["id"]
        belegung[event_id] = sum(
            r.get("anzahl", 0)
            for r in reservierungen
            if r.get("veranstaltung_id") == event_id
        )

    return render_template(
        "admin_bus_events.html",
        events=events,
        belegung=belegung
    )


@app.route('/admin/bus/hinzufuegen', methods=['GET', 'POST'])
def admin_bus_event_hinzufuegen():
    if not admin_required():
        return redirect('/login')

    if request.method == 'POST':
        events = load_bus_events()

        titel = request.form.get("titel", "").strip()
        datum = request.form.get("datum", "").strip()
        abfahrtszeit = request.form.get("abfahrtszeit", "").strip()
        haltestellen_roh = request.form.get("haltestellen", "").strip()
        gesamtplaetze = int(request.form.get("gesamtplaetze", 0))

        haltestellen = [h.strip() for h in haltestellen_roh.split(",") if h.strip()]

        event = {
            "id": str(uuid.uuid4()),
            "titel": titel,
            "datum": datum,
            "abfahrtszeit": abfahrtszeit,
            "haltestellen": haltestellen,
            "gesamtplaetze": gesamtplaetze
        }

        events.append(event)
        save_bus_events(events)

        return redirect('/admin/bus')

    return render_template("admin_bus_event_form.html", event=None)


@app.route('/admin/bus/bearbeiten/<event_id>', methods=['GET', 'POST'])
def admin_bus_event_bearbeiten(event_id):
    if not admin_required():
        return redirect('/login')

    events = load_bus_events()
    event = next((e for e in events if e["id"] == event_id), None)

    if not event:
        return "Veranstaltung nicht gefunden", 404

    if request.method == 'POST':
        event["titel"] = request.form.get("titel", "").strip()
        event["datum"] = request.form.get("datum", "").strip()
        event["abfahrtszeit"] = request.form.get("abfahrtszeit", "").strip()

        haltestellen_roh = request.form.get("haltestellen", "").strip()
        event["haltestellen"] = [h.strip() for h in haltestellen_roh.split(",") if h.strip()]

        event["gesamtplaetze"] = int(request.form.get("gesamtplaetze", 0))

        save_bus_events(events)

        return redirect('/admin/bus')

    return render_template("admin_bus_event_form.html", event=event)


@app.route('/admin/bus/loeschen/<event_id>')
def admin_bus_event_loeschen(event_id):
    if not admin_required():
        return redirect('/login')

    events = load_bus_events()
    events = [e for e in events if e["id"] != event_id]
    save_bus_events(events)

    reservierungen = load_bus_reservierungen()
    reservierungen = [
        r for r in reservierungen
        if r.get("veranstaltung_id") != event_id
    ]
    save_bus_reservierungen(reservierungen)

    return redirect('/admin/bus')


@app.route('/admin/bus/reservierungen/<event_id>')
def admin_bus_event_reservierungen(event_id):
    if not admin_required():
        return redirect('/login')

    events = load_bus_events()
    event = next((e for e in events if e["id"] == event_id), None)

    if not event:
        return "Veranstaltung nicht gefunden", 404

    reservierungen = load_bus_reservierungen()
    event_reservierungen = [
        r for r in reservierungen
        if r.get("veranstaltung_id") == event_id
    ]

    return render_template(
        "admin_bus_event_reservierungen.html",
        event=event,
        reservierungen=event_reservierungen
    )


@app.route('/admin/bus/reservierung-loeschen/<reservierung_id>')
def admin_bus_reservierung_loeschen(reservierung_id):
    if not admin_required():
        return redirect('/login')

    reservierungen = load_bus_reservierungen()

    reservierung = next(
        (r for r in reservierungen if r["id"] == reservierung_id),
        None
    )

    event_id = reservierung.get("veranstaltung_id") if reservierung else None

    reservierungen = [
        r for r in reservierungen
        if r["id"] != reservierung_id
    ]

    save_bus_reservierungen(reservierungen)

    if event_id:
        return redirect(f'/admin/bus/reservierungen/{event_id}')

    return redirect('/admin/bus')


# ---------------------------------------------------------
# ADMIN - STORNOGEBÜHREN
# ---------------------------------------------------------

@app.route('/admin/stornogebuehren')
def admin_stornogebuehren():
    if not admin_required():
        return redirect('/login')

    stornos = load_stornogebuehren()
    stornos = list(reversed(stornos))

    gesamt = sum(float(s.get("betrag", 0)) for s in stornos)

    return render_template(
        "admin_stornogebuehren.html",
        stornos=stornos,
        gesamt=gesamt
    )
# ---------------------------------------------------------
# START
# ---------------------------------------------------------

if __name__ == '__main__':
    ensure_data_files()
    load_products()
    app.run(debug=True)