from bottle import *
import sqlite3
import hashlib
import time
import auth_public as auth
import psycopg2, psycopg2.extensions, psycopg2.extras
from decimal import *


static_dir = "./static"
secret = "to skrivnost je zelo tezko uganiti 1094107c907cw982982c42"

#baza1 = "aaa.db"
##baza = sqlite3.connect(baza1, isolation_level=None)
##c = baza.cursor()
##c.execute('''CREATE TABLE IF NOT EXISTS uporabnik (
##  username TEXT PRIMARY KEY,
##  password TEXT NOT NULL,
##  ime TEXT NOT NULL,
##  priimek TEXT NOT NULL
##);
##''')
##c.close()

psycopg2.extensions.register_type(psycopg2.extensions.UNICODE) # se znebimo problemov s sumniki
baza = psycopg2.connect(database=auth.db, host=auth.host, user=auth.user, password=auth.password)
baza.set_isolation_level(psycopg2.extensions.ISOLATION_LEVEL_AUTOCOMMIT) # onemogocimo transakcije

cur = baza.cursor(cursor_factory=psycopg2.extras.DictCursor) 



def password_md5(s):
    """Vrni MD5 hash danega UTF-8 niza. Gesla vedno spravimo v bazo
       kodirana s to funkcijo."""
    h = hashlib.md5()
    h.update(s.encode('utf-8'))
    return h.hexdigest()

def get_user(auto_login = False,auto_redir=False):
    """Poglej cookie in ugotovi, kdo je prijavljeni uporabnik,
       vrni njegov username in ime. Če ni prijavljen, presumeri
       na stran za prijavo ali vrni None (advisno od auto_login).
    """
    # Dobimo username iz piškotka
    username = request.get_cookie('username', secret=secret)
    # Preverimo, ali ta uporabnik obstaja
    if username is not None:
        #Če si že prijavljen, nimaš tu kaj iskat! 
        if auto_redir: 
            redirect('/shop/')
        else:
            cur.execute("SELECT userID, username, name,balance  FROM users WHERE username=%s",
                      [username])
            r = cur.fetchone()
            if r is not None:
                # uporabnik obstaja, vrnemo njegove podatke
                return r
    # Če pridemo do sem, uporabnik ni prijavljen, naredimo redirect.
    if auto_login:
        redirect('/login/')
    else:
        return [None,None,None,None]

##@route("/")
##def main():
##    (username, ime) = get_user()
##    return template("bolha.html",
##                    username=username)
##

@route("/")
def main():
    redirect("/shop/")

@route("/static/<filename:path>")
def static(filename):
    """Splošna funkcija, ki servira vse statične datoteke iz naslova
       /static/..."""
    return static_file(filename, root=static_dir)



@route('/hello')
def hello():
    return "Hello World!"

@get("/index/")
def index_get():
    """Serviraj formo za index."""
    curuser = get_user()
    return template("index.html",
                           stanje = curuser[3],
                           napaka=None,
                           logged=curuser[2],                    
                           username=None)

@get("/shop/")
def shop_get():
    """Serviraj formo za shop."""
    curuser = get_user()
    return template("shop.html",
                           napaka=None,
                           stanje=curuser[3],
                           logged=curuser[2])




@get("/producttest/")
def login_get():
    """Serviraj formo za login."""
    curuser = get_user()
    return template("product-details.html",
                           napaka=None,
                           logged=curuser[2],
                           username=None)


@get("/login/")
def login_get():
    """Serviraj formo za login."""
    curuser = get_user(auto_redir = True)
    return template("login.html",
                           napaka=None,
                           logged=None,
                           username=None)




@post("/login/")
def login_post():
    """Obdelaj izpolnjeno formo za prijavo"""
    # Uporabniško ime, ki ga je uporabnik vpisal v formo
    username = request.forms.username
    # Izračunamo MD5 has gesla, ki ga bomo spravili
    password = password_md5(request.forms.password)
    # Preverimo, ali se je uporabnik pravilno prijavil
    cur.execute("SELECT 1 FROM users WHERE username=%s AND password=%s",
              [username, password])
    if cur.fetchone() is None:
        # Username in geslo se ne ujemata
        return template("login.html",
                               napaka="No such user",
                               username=username)
    else:
        # Vse je v redu, nastavimo cookie in preusmerimo na glavno stran
        response.set_cookie('username', username,path="/", secret=secret)
        redirect("/shop/")
    



@get("/register/")
def login_get():
    """Prikaži formo za registracijo."""
    curuser = get_user(auto_redir = True)
    return template("register.html", 
                           username=None,
                           ime=None,
                           napaka=None,
                           logged=curuser[2])
@post("/register/")
def register_post():
    """Registriraj novega uporabnika."""
    username = request.forms.username
    ime = request.forms.ime
    priimek = request.forms.priimek
    password1 = request.forms.password1
    password2 = request.forms.password2
    email = request.forms.email
    curuser = get_user(auto_redir = True)
    # Ali uporabnik že obstaja?
    cur.execute("SELECT 1 FROM users WHERE username=%s", [username])
    if cur.fetchone():
        # Uporabnik že obstaja
        return template("register.html",
                               username=username,
                               ime=ime,
                               napaka='To uporabniško ime je že zavzeto',
                               logged=curuser[2])
    elif not password1 == password2:
        # Geslo se ne ujemata
        return template("register.html",
                               username=username,
                               ime=ime,
                               logged=curuser[2],
                               napaka='Gesli se ne ujemata')
    else:
        # Vse je v redu, vstavi novega uporabnika v bazo
        password = password_md5(password1)
        cur.execute("INSERT INTO users (username, name, surname, email, password,balance) VALUES (%s, %s, %s, %s,%s,%s)",
                  (username, ime,priimek,email, password,0))
        # Daj uporabniku cookie
        response.set_cookie('username', username, path='/', secret=secret)
        redirect("/shop/")



@get("/account/")
def login_get():
    """Prikaži formo za registracijo."""
    curuser = get_user(auto_login=True)
    return template("account.html",
                           stanje=curuser[3],
                           username=None,
                           ime=None,
                           napaka=None,
                           logged=curuser[2])


@post("/account/")
def register_post():
    """Depozit."""
    curuser = get_user(auto_login=True)
    deposit = Decimal(request.forms.deposit)
    if deposit <= 0:
        return template("account.html",
                           stanje=curuser[3],
                           username=None,
                           ime=None,
                           napaka="Please enter a positive amount",
                           logged=curuser[2])
        
    if deposit + curuser[3] > 999999:
        return template("account.html",
                           stanje=curuser[3],
                           username=None,
                           ime=None,
                           napaka="Amount would exceed your balance limit.",
                           logged=curuser[2])

    
    cur.execute("UPDATE users SET balance = balance + %s WHERE userID = %s", [deposit,curuser[0]])
    return template("account.html",
                           stanje=curuser[3]+deposit,
                           username=None,
                           ime=None,
                           napaka="Your deposit was successful.",
                           logged=curuser[2])




@get("/new/")
def login_get():
    """Prikaži formo za registracijo."""
    curuser = get_user(auto_login=True)
    return template("new.html",
                           stanje=curuser[3],
                           username=None,
                           ime=None,
                           napaka=None,
                           logged=curuser[2])




    
@get("/logout/")
def logout():
    """Pobriši cookie in preusmeri na login."""
    response.set_cookie('username',value="bai",secret=secret,path='/', max_age=0)
    redirect('/shop/')



run(host='localhost', port=8080, debug=True)
