from bottle import *
import sqlite3
import hashlib
import time
import auth_public as auth
import psycopg2, psycopg2.extensions, psycopg2.extras
from decimal import *
import os

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


def all_cat_parents(catid):
    
    cur.execute('''
                    SELECT starsi,category_name from
                    (
                        WITH RECURSIVE x(categoryid,parentid,parents,last_id, depth) AS (
                          SELECT categoryid, parentid, ARRAY[categoryid] AS parents, categoryid AS last_id, 0 AS depth FROM categories
                          UNION ALL
                          SELECT x.categoryid, x.parentid, parents||t1.parentid, t1.parentid AS last_id, x.depth + 1
                          FROM x 
                            INNER JOIN categories t1 
                            ON (last_id= t1.categoryid)
                          WHERE t1.parentid IS NOT NULL
                        )
                        SELECT unnest(parents) as starsi

                        FROM x 
                        WHERE depth = (SELECT max(sq.depth) FROM x sq WHERE sq.categoryid = x.categoryid) AND categoryid=%s
                    )
                    AS parents JOIN categories ON parents.starsi = categories.categoryid

                    


                ''',[catid])
    return(cur.fetchall())



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
    cur.execute("SELECT * FROM categories WHERE parentid is NULL")
    podkategorije=cur.fetchall()
    print(podkategorije)
    return template("shop.html",
                           query={},
                           atributi = [],
                           starsi=[],
                           napaka=None,
                           podkategorije = podkategorije,
                           stanje=curuser[3],
                           logged=curuser[2])


@get("/shop/<catid>/")
def shop_get(catid):
    """Serviraj formo za shop."""
    curuser = get_user()
    print(catid)
    starsi = list(reversed(all_cat_parents(catid)))
    cur.execute("SELECT * FROM categories WHERE parentid = %s",[catid])
    podkategorije=cur.fetchall()
    cur.execute("SELECT * FROM cat_attrib WHERE categoryid = ANY(%s)",[[i[0] for i in starsi]])
    atributi = cur.fetchall()
    cur.execute("SELECT * FROM attributes WHERE attributeid = ANY(%s)",[[i[0] for i in atributi]])
    vrednosti_atributov = cur.fetchall()
    vrednosti_atributov = list(set([(i[1],i[2]) for i in vrednosti_atributov]))
    #cur.execute("")
    query = dict(request.query)
    cleanquery= {i:query[i] for i in query if query[i]!=''}
    textquery = tuple([(i,cleanquery[i]) for i in cleanquery if 'max' not in i and 'min' not in i])
    intquery =  {i:cleanquery[i] for i in cleanquery if ('max'  in i or 'min'  in i) and ('bo' not in i and 'bid' not in i)}
    print(query,cleanquery)
    print(textquery,intquery)
    print(atributi)

    parameters = []
    parameters.append(textquery)
    length = len(textquery)
    ORstring=''
    for i in [t[0] for t in atributi if t[2] == 'INTEGER']:
        c = 0
        try:
            intquery[str(i)+'min']
            c +=1
        except:
            pass
        try:
            intquery[str(i)+'max']
            c +=2
        except:
            pass
        if c == 3:
            length+=1
            ORstring += 'OR (attributeid =%s AND value::integer >= %s AND value::integer <= %s)\n'
            parameters = parameters + [i,intquery[str(i)+'min'],intquery[str(i)+'max']]
        elif c== 2:
            length+=1
            ORstring += 'OR (attributeid =%s AND value::integer <= %s)\n'
            parameters = parameters + [i,intquery[str(i)+'max']]
        elif c== 1:
            length+=1
            ORstring += 'OR (attributeid =%s AND value::integer >= %s)\n'
            parameters = parameters + [i,intquery[str(i)+'min']]
    
    print(ORstring)


    print(length)
    parameters.append(length)
    print(parameters)
    
  
        #OR (attributeid =4 AND value::integer >= 1 AND value::integer <= 4)      
    cur.execute('''
        SELECT itemid from attributes where (attributeid,value) IN %s\n'''+ORstring+'''


        GROUP BY itemid
        HAVING count(*) = %s
                ''',parameters)
    test=cur.fetchall()
    print(test)
    
    


    
    #cur.execute(""

    
    return template("shop.html",
                           query=query,
                           vrednosti_atributov=vrednosti_atributov,
                           atributi = atributi,
                           starsi=starsi,
                           napaka=None,
                           podkategorije = podkategorije,
                           stanje=curuser[3],
                           logged=curuser[2])




@get("/producttest/")
def login_get():
    """Serviraj formo za login."""
    curuser = get_user()
    return template("product-details.html",
                           napaka=None,
                           stanje=curuser[3],
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
							   logged=None,
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
    maxdepth = 99 #mogoče nepotrebno
    curuser = get_user(auto_login=True)
    query = dict(request.query) #poberemo parametre iz query stringa, shranimo v slovar
    seznam_kategorij = []#seznam seznamov kategorij (po globinah)
    seznam_atributov = []
    cur.execute("SELECT categoryid,category_name FROM categories WHERE parentid is NULL") #dobi vse kategorije globine 0 in jih spravi v seznam kategorij
    seznam_kategorij.append(cur.fetchall())
    attrib = 0
    cleanquery = {} #tu shranimo samo ustrezne elemente slovarja query
    values = [None]*6
    for i in range(0,5):
        #globina kategorij zaenkrat največ pet
        try:
            ustreznost="krneki" 
            if i >0:
                #query stringi se lahko pomešajo, napačni inputi itd. Ta if preveri, če hiearhija res drži, sicer vrne napako
                cur.execute("SELECT categoryid,category_name FROM categories WHERE categoryid = %s AND parentid = %s",[query[str(i)],query[str(i-1)]])
                ustreznost=cur.fetchone()
            if ustreznost == None:
                raise
            else:
                #če je vse v redu, dobi vse podkategorije izbrane kategorije in jih spravi v seznam seznamov
                cur.execute("SELECT categoryid,category_name FROM categories WHERE parentid = %s",[int(query[str(i)])])
                result = cur.fetchall()
                cleanquery[str(i)] = query[str(i)]
                if not result:
                    attrib = 1
                    break
                else:
                    seznam_kategorij.append(result)                   
        except:
            #če pride do napake (npr. query stringa ni bilo za dan 'i') nastavi vrednost v slovarju na dummy, da ga html ignorira
            query[str(i)] = "dummy"
            


    if attrib == 1:
        #če smo izbrali končno kategorijo, izberemo atribute za predmet:
        print(query,cleanquery)
        
        for i in cleanquery:
            cur.execute("SELECT attributeid,attributename,attributeclass FROM cat_attrib WHERE categoryid = %s",[cleanquery[str(i)]])
            seznam_atributov+= cur.fetchall()
        for i in seznam_atributov:
            values.append('')
            
            
    print(seznam_atributov)
    return template("new.html",
                           values = values,
                           attrib = attrib,
                           maxdepth = maxdepth,
                           seznam=seznam_kategorij,
                           seznam_atributov = seznam_atributov,
                           query=query,
                           stanje=curuser[3],
                           username=None,
                           ime=None,
                           napaka=None,
                           logged=curuser[2])


@post("/new/")
def post():
    maxdepth = 99 #mogoče nepotrebno
    curuser = get_user(auto_login=True)
    query = dict(request.query) #poberemo parametre iz query stringa, shranimo v slovar
    seznam_kategorij = []#seznam seznamov kategorij (po globinah)
    seznam_atributov = []
    cur.execute("SELECT categoryid,category_name FROM categories WHERE parentid is NULL") #dobi vse kategorije globine 0 in jih spravi v seznam kategorij
    seznam_kategorij.append(cur.fetchall())
    attrib = 0
    cleanquery = {} #tu shranimo samo ustrezne elemente slovarja query
    values = [None]*6
    napaka=None
    for i in range(0,5):
        #globina kategorij zaenkrat največ pet
        try:
            ustreznost="krneki"     
            if i >0:
                #query stringi se lahko pomešajo, napačni inputi itd. Ta if preveri, če hiearhija res drži, sicer vrne napako
                cur.execute("SELECT categoryid,category_name FROM categories WHERE categoryid = %s AND parentid = %s",[query[str(i)],query[str(i-1)]])
                ustreznost=cur.fetchone()
            if ustreznost == None:
                raise
            else:
                #če je vse v redu, dobi vse podkategorije izbrane kategorije in jih spravi v seznam seznamov
                cur.execute("SELECT categoryid,category_name FROM categories WHERE parentid = %s",[int(query[str(i)])])
                result = cur.fetchall()
                cleanquery[str(i)] = query[str(i)]
                if not result:
                    attrib = 1
                    break
                else:
                    seznam_kategorij.append(result)                   
        except:
            #če pride do napake (npr. query stringa ni bilo za dan 'i') nastavi vrednost v slovarju na dummy, da ga html ignorira
            query[str(i)] = "dummy"
            


    if attrib == 1:
        #če smo izbrali končno kategorijo, izberemo atribute za predmet:
        
        for i in cleanquery:
            cur.execute("SELECT attributeid,attributename,attributeclass FROM cat_attrib WHERE categoryid = %s",[cleanquery[str(i)]])
            seznam_atributov+= cur.fetchall()
        formname=None
        values[0] = request.forms.get("itemname")
        values[1] = request.forms.get("message")
        values[2] = request.forms.get("bidprice") or None
        values[3] = request.forms.get("buyoutprice") or None
        values[4] = request.forms.get("expiration") or '89'
        image = request.files.get("uploaded")
        for atribut in seznam_atributov:
            formname="a"+str(atribut[0])
            print(formname,request.forms.get(formname))
            values.append(request.forms.get(formname))
            
        print(seznam_atributov)

        #napake:
        if values[2] is None and values[3] is None:
            napaka = "At least one price must be specified!"
        if values[2] is not None and values[3] is not None:
            if int(values[2]) >= int(values[3]):
                napaka = "Bid price must be lower than the buyout price!"
            
            
                
        if not napaka:
            cur.execute("INSERT INTO items(itemname, categoryid, ownerid, starting_bid, buyout_price,expires,description) VALUES (%s,%s,%s,%s,%s,now()+%s::interval,%s)",
                (values[0],cleanquery[max(cleanquery)],curuser[0],values[2],values[3],values[4]+" days",values[1]))
            cur.execute("SELECT last_value FROM items_itemid_seq")
            itemid=cur.fetchone()
            for i in range(6,len(values)):
                if values[i] is not None:
                    cur.execute("INSERT INTO attributes(itemid,attributeid,value) VALUES (%s,%s,%s)",
                                (itemid[0],seznam_atributov[i-6][0],values[i]))
                          
            if image is not None:
                name, ext = os.path.splitext(image.filename)
                if ext.lower() not in ('.png','.jpg','.jpeg'):
                    napaka = 'Image file extension not allowed.'
                else:
                    save_path = os.getcwd()+"\\static\\images\\uploads"            
                    filename = str(itemid[0]) + ext            
                    image.filename = filename
                    image.save(save_path) # appends upload.filename automatically

        if napaka is None:
            napaka = "Item successfully submitted!"
        print(napaka)
        return template("new.html",
                           values=values,
                           attrib = attrib,
                           seznam=seznam_kategorij,
                           seznam_atributov = seznam_atributov,
                           query=query,
                           stanje=curuser[3],
                           username=None,
                           ime=None,
                           napaka=napaka,
                           logged=curuser[2])
    
    
@get("/logout/")
def logout():
    """Pobriši cookie in preusmeri na login."""
    response.set_cookie('username',value="bai",secret=secret,path='/', max_age=0)
    redirect('/shop/')



run(host='localhost', port=8080, debug=True)
