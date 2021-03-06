from bottle import *
import sqlite3
import hashlib

baza = "aaa.db"

secret = "to skrivnost je zelo tezko uganiti 1094107c907cw982982c42"

baza = sqlite3.connect(baza, isolation_level=None)
c = baza.cursor()
c.execute('''CREATE TABLE IF NOT EXISTS uporabnik (
  username TEXT PRIMARY KEY,
  password TEXT NOT NULL,
  ime TEXT NOT NULL
);
''')
c.close()




def password_md5(s):
    """Vrni MD5 hash danega UTF-8 niza. Gesla vedno spravimo v bazo
       kodirana s to funkcijo."""
    h = hashlib.md5()
    h.update(s.encode('utf-8'))
    return h.hexdigest()

def get_user(auto_login = True):
    """Poglej cookie in ugotovi, kdo je prijavljeni uporabnik,
       vrni njegov username in ime. Če ni prijavljen, presumeri
       na stran za prijavo ali vrni None (advisno od auto_login).
    """
    # Dobimo username iz piškotka.
    username = request.get_cookie('username', secret=secret)
    # Preverimo, ali ta uporabnik obstaja.
    if username is not None:
        c = baza.cursor()
        c.execute("SELECT username, ime FROM uporabnik WHERE username=?",
                  [username])
        r = c.fetchone()
        c.close ()
        if r is not None:
            # uporabnik obstaja, vrnemo njegove podatke.
            return r
    # Če pridemo do sem, uporabnik ni prijavljen, naredimo redirect.
    if auto_login:
        redirect('/login/')
    else:
        return None

@route("/")
def main():
    (username, ime) = get_user()
    return template("bolha.html",
                    username=username)
    

@route('/hello')
def hello():
    return "Hello World!"

@get("/login/")
def login_get():
    """Serviraj formo za login."""
    return template("login.html",
                           napaka=None,
                           username=None)
@post("/login/")
def login_post():
    """Obdelaj izpolnjeno formo za prijavo"""
    # Uporabniško ime, ki ga je uporabnik vpisal v formo
    username = request.forms.username
    # Izračunamo MD5 has gesla, ki ga bomo spravili
    password = password_md5(request.forms.password)
    # Preverimo, ali se je uporabnik pravilno prijavil
    c = baza.cursor()
    c.execute("SELECT 1 FROM uporabnik WHERE username=? AND password=?",
              [username, password])
    if c.fetchone() is None:
        # Username in geslo se ne ujemata.
        return template("login.html",
                               napaka="Nepravilna prijava",
                               username=username)
    else:
        # Vse je v redu, nastavimo cookie in preusmerimo na glavno stran
        response.set_cookie('username', username, path='/', secret=secret)
        redirect("/")



@get("/register/")
def login_get():
    """Prikaži formo za registracijo."""
    return template("register.html", 
                           username=None,
                           ime=None,
                           napaka=None)


@post("/register/")
def register_post():
    """Registriraj novega uporabnika."""
    username = request.forms.username
    ime = request.forms.ime
    password1 = request.forms.password1
    password2 = request.forms.password2
    # Ali uporabnik že obstaja?.
    c = baza.cursor()
    c.execute("SELECT 1 FROM uporabnik WHERE username=?", [username])
    if c.fetchone():
        # Uporabnik že obstaja
        return template("register.html",
                               username=username,
                               ime=ime,
                               napaka='To uporabniško ime je že zavzeto')
    elif not password1 == password2:
        # Geslo se ne ujemata
        return template("register.html",
                               username=username,
                               ime=ime,
                               napaka='Gesli se ne ujemata')
    else:
        # Vse je v redu, vstavi novega uporabnika v bazo
        password = password_md5(password1)
        c.execute("INSERT INTO uporabnik (username, ime, password) VALUES (?, ?, ?)",
                  (username, ime, password))
        # Daj uporabniku cookie
        response.set_cookie('username', username, path='/', secret=secret)
        redirect("/")

    
def hello():
    return "Hello ydyd!"



run(host='localhost', port=8080, debug=True)
