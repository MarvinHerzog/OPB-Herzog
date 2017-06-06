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


def get_cat_parents(catid):
    #rekurzivna funkcija, ki dobi starše do največje možne globine
    #opomba: podobna funkcija je definirana v phppgadmin med functions, le da slednje vrne vse otroke, vnuke,...
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




@route("/")
def main():
    redirect("/shop/")

@route("/static/<filename:path>")
def static(filename):
    """Splošna funkcija, ki servira vse statične datoteke iz naslova
       /static/..."""
    return static_file(filename, root=static_dir)

@get("/shop/")
def shop_get():
    curuser = get_user()
    cur.execute("SELECT * FROM categories WHERE parentid is NULL")
    podkategorije=cur.fetchall()
    query = dict(request.query)
    qstring = str(request.query_string)
    qstring = re.sub('&?page=\d','', qstring, flags=re.IGNORECASE)
    pagenr = request.query.page or 1
    #iz query stringov poberemo vse (filtri in št strani)

    #zaradi dinamične narave poizvedbe sestavimo SQL poizvedbo po kosih AND/OR
    ORstring='''
        SELECT items.itemid,itemname,categoryid,ownerid,bid,buyout,posted_date,expires FROM items         
        WHERE 1=1\n'''  
    parameters = [] #vektor parametrov za sql stavke
    #Query za cene
    for i in ['bidmin','bidmax','bomin','bomax','search']:
        try:
            krnekaj = query[i] #ali je uporabnik sploh filtriral oz je None?
        except:
            query[i] = '' 


    #stavki za bid/buyout filtre
    if query['bidmin'] != '' and query['bidmax'] != '':
        ORstring += 'AND (bid >= %s AND bid <= %s)\n'
        parameters = parameters + [query['bidmin'],query['bidmax']]
    elif query['bidmin'] != '': 
        ORstring += 'AND (bid >= %s)\n'
        parameters = parameters + [query['bidmin']]
    elif query['bidmax'] != '': 
        ORstring += 'AND (bid <= %s OR (bid IS NULL AND buyout <= %s))\n'
        parameters = parameters + [query['bidmax'],query['bidmax']]

    if query['bomin'] != '' and query['bomax'] != '':
        ORstring += 'AND (buyout >= %s AND buyout <= %s)\n'
        parameters = parameters + [query['bomin'],query['bomax']]
    elif query['bomin'] != '': 
        ORstring += 'AND (buyout >= %s)\n'
        parameters = parameters + [query['bomin']]
    elif query['bomax'] != '': 
        ORstring += 'AND (buyout <= %s)\n'
        parameters = parameters + [query['bomax']]

    if query['search'] != '': 
        ORstring += '''AND (LOWER(itemname) LIKE LOWER(%s) )'''
        parameters = parameters + ['%'+query['search']+'%']
        print('%'+query['search']+'%')

        
    ORstring += "ORDER BY posted_date DESC"  #novi predmeti prikazani najprej           
    cur.execute(ORstring,parameters)
    predmeti=cur.fetchall()

    #ta tabela je potrebna zaradi razlicnih koncnic (jpg, png, etc.)
    cur.execute("SELECT * FROM images WHERE itemid = ANY(%s) ",[[i[0] for i in predmeti]])
    slike = cur.fetchall()
    slike = {i[0]:i[1] for i in slike}
    
    return template("shop.html",
                           pagenr=int(pagenr),
                           qstring=qstring,                    
                           predmeti=predmeti,
                           slike=slike,                    
                           query=query,
                           atributi = [],
                           starsi=[],
                           napaka=None,
                           podkategorije = podkategorije,
                           stanje=curuser[3],
                           logged=curuser[2])


@get("/shop/<catid>/")
def shop_get(catid):
    #vse isto kot zgoraj, tokrat za specificno podkategorijo
    curuser = get_user()

    #funkcija nam rekurzivno da vse 'nadkategorije'
    starsi = list(reversed(get_cat_parents(catid)))
    cur.execute("SELECT * FROM categories WHERE parentid = %s",[catid])
    podkategorije=cur.fetchall()
    cur.execute("SELECT * FROM cat_attrib WHERE categoryid = ANY(%s)",[[i[0] for i in starsi]])
    atributi = cur.fetchall()
    cur.execute("SELECT * FROM attributes WHERE attributeid = ANY(%s)",[[i[0] for i in atributi]])
    vrednosti_atributov = cur.fetchall()
    vrednosti_atributov = list(set([(i[1],i[2]) for i in vrednosti_atributov]))
    query = dict(request.query)
    try:
        del query['page']
    except:
        pass

    #V html ne gre (brez js) zamenjati samo dela query stringa brez da bi izgubil ostale, zato:
    qstring = str(request.query_string)
    qstring = re.sub('&?page=\d','', qstring, flags=re.IGNORECASE)    
    pagenr = request.query.page or 1 #stran

    
    cleanquery= {i:query[i] for i in query if query[i]!=''}

    #ločimo posebej atribute (številske/tekstovne), ki so specifični za kategorijo
    textquery = tuple([(i,cleanquery[i]) for i in cleanquery if 'max' not in i and 'min' not in i and 'search' not in i])
    intquery =  {i:cleanquery[i] for i in cleanquery if ('max'  in i or 'min'  in i) and ('bo' not in i and 'bid' not in i)}






    ### Tu sestavimo query za filtracijo predmetov
    parameters = []
    
    length = 0
    ORstring='''
            SELECT items.itemid,itemname,categoryid,ownerid,bid,buyout,posted_date,expires FROM items
            '''

    if len(intquery)+len(textquery)>0:
        ORstring+= '''
            RIGHT JOIN (           
            SELECT itemid from attributes where attributeid = -1\n'''     #ne vrne nič, na to vežemo OR stavke da dobimo željene rezultate
            
    

    
    #Tekstovni parametri
    if textquery:
        parameters.append(textquery)
        length += len(textquery)
        ORstring += '''OR (attributeid,value) IN %s\n'''

    #Številčni parametri, ki niso cena
    for i in [t[0] for t in atributi if t[2] == 'INTEGER']:
              try:
                  krneki = query[str(i)+'min']
              except:
                  query[str(i)+'min'] = ''
              try:
                  krneki = query[str(i)+'max']
              except:
                  query[str(i)+'max'] = ''
                  
              if query[str(i)+'min'] != '' and query[str(i)+'max'] != '':
                length+=1
                ORstring += 'OR (attributeid =%s AND value::integer >= %s AND value::integer <= %s)\n'
                parameters = parameters + [i,intquery[str(i)+'min'],intquery[str(i)+'max']]
              elif query[str(i)+'min'] != '': 
                length+=1
                ORstring += 'OR (attributeid =%s AND value::integer >= %s)\n'
                parameters = parameters + [i,intquery[str(i)+'min']]
              elif query[str(i)+'max'] != '': 
                length+=1
                ORstring += 'OR (attributeid =%s AND value::integer <= %s)\n'
                parameters = parameters + [i,intquery[str(i)+'max']]

   
    if length>0:
        parameters.append(length)
        ORstring+='''
                GROUP BY attributes.itemid
                HAVING count(attributes.itemid) = %s
                ) AS filter on items.itemid = filter.itemid
                '''   
    ORstring +='''
            WHERE (categoryid = ANY(get_all_children_array(%s)) OR categoryid = %s)\n'''
    
    parameters=parameters+[catid,catid]   
    #Query za cene
    for i in ['bidmin','bidmax','bomin','bomax','search']:
        try:
            krnekaj = query[i]
        except:
            query[i] = ''

    
    if query['bidmin'] != '' and query['bidmin'] != '':
        ORstring += 'AND (bid >= %s AND bid <= %s)\n'
        parameters = parameters + [query['bidmin'],query['bidmax']]
    elif query['bidmin'] != '': 
        ORstring += 'AND (bid >= %s)\n'
        parameters = parameters + [query['bidmin']]
    elif query['bidmax'] != '': 
        ORstring += 'AND (bid <= %s OR (bid IS NULL AND buyout <= %s))\n'
        parameters = parameters + [query['bidmax'],query['bidmax']]

    if query['bomin'] != '' and query['bomin'] != '':
        ORstring += 'AND (buyout >= %s AND buyout <= %s)\n'
        parameters = parameters + [query['bomin'],query['bomax']]
    elif query['bomin'] != '': 
        ORstring += 'AND (buyout >= %s)\n'
        parameters = parameters + [query['bomin']]
    elif query['bomax'] != '': 
        ORstring += 'AND (buyout <= %s)\n'
        parameters = parameters + [query['bomax']]
                  
    if query['search'] != '': 
        ORstring += '''AND (LOWER(itemname) LIKE LOWER(%s) )'''
        parameters = parameters + ['%'+query['search']+'%']
        print('%'+query['search']+'%')


  
  
    ORstring += "ORDER BY posted_date DESC"       
    cur.execute(
        ORstring,parameters) #Izberemo tiste predmete, ki ustrezajo vsem filtrom

    
    predmeti=cur.fetchall()

    ## dobi slike
    cur.execute("SELECT * FROM images WHERE itemid = ANY(%s)",[[i[0] for i in predmeti]])
    slike = cur.fetchall()
    slike = {i[0]:i[1] for i in slike}
    
    return template("shop.html",
                           pagenr=int(pagenr),
                           qstring=qstring, 
                           slike=slike,                     
                           predmeti=predmeti,
                           query=query,
                           vrednosti_atributov=vrednosti_atributov,
                           atributi = atributi,
                           starsi=starsi,
                           napaka=None,
                           podkategorije = podkategorije,
                           stanje=curuser[3],
                           logged=curuser[2])




@get("/item/<item_id>/")
def item_get(item_id):
    """Podroben opis predmeta"""
    curuser = get_user()

    #vsi atributi izbranega predmeta
    cur.execute(''' SELECT * FROM attributes
        JOIN cat_attrib on cat_attrib.attributeid = attributes.attributeid
        where itemid = %s''',[item_id])
    atributi = cur.fetchall()
   
    #slika
    cur.execute(''' SELECT * FROM images        
        where itemid = %s''',[item_id])
    slike = cur.fetchall()

    cur.execute(''' SELECT itemid,itemname,categoryid,
                    ownerid,bid,buyout,posted_date::date,expires::date,description,
                    current_bidder,userid,username,name,surname,email,previous_bid FROM items
                    JOIN users ON users.userid=items.ownerid
        where itemid = %s''',[item_id])
    item = cur.fetchone()    
    return template("product-details.html",
                           slike=slike,
                           atributi=atributi,
                           item = item,
                           napaka=None,
                           stanje=curuser[3],
                           logged=curuser[2],
                           username=None)



@post("/item/<item_id>/")
def item_post(item_id):
    """Kupi predmet oz. bid"""
    napaka = None
    curuser = get_user(auto_login = True)

    
    cur.execute(''' SELECT * FROM attributes
        JOIN cat_attrib on cat_attrib.attributeid = attributes.attributeid
        where itemid = %s''',[item_id])
    atributi = cur.fetchall()
   

    cur.execute(''' SELECT * FROM images        
        where itemid = %s''',[item_id])
    slike = cur.fetchall()

    
    cur.execute(''' SELECT itemid,itemname,categoryid,
                    ownerid,bid,buyout,posted_date::date,expires::date,description,
                    current_bidder,userid,username,name,surname,email,previous_bid FROM items
                    JOIN users ON users.userid=items.ownerid
        where itemid = %s''',[item_id])
    item = cur.fetchone()


    ## bid in buyout update

    #Če je uporabnik pritisnil bid ali buyout, dobi ponujeno ceno:
    bid=request.forms.get("bid") #vrednost
    buyout=request.forms.get("buyout") #1 ali 0

    #Če je uporabnik vnesel isto bid ceno, kot je buyout.. kupi predmet
    if bid == item[5]:
        bid = None
        buyout = 1

    #sicer:
    if bid is not None:
        bid = Decimal(bid)
        if curuser[3]<=bid:
            napaka = "You don't have enough funds to do that"
        elif str(curuser[0]) == str(item[9]):
            napaka ="You're already the highest bidder"
        else:
            if item[9]:                                                                 #če prejšnji bidder obstaja:
                cur.execute("UPDATE users SET balance = balance + %s WHERE userID = %s", #prejšnji max bidder dobi denar nazaj
                    [item[15],item[9]])
                
            cur.execute("UPDATE users SET balance = balance - %s WHERE userID = %s", #novi bidder plača
                [bid,curuser[0]])
            cur.execute("UPDATE items SET current_bidder = %s WHERE itemid = %s", #novi max bidder je:
                [curuser[0],item_id])
            cur.execute("UPDATE items SET previous_bid = bid WHERE itemid=%s",[item_id]) #stari bid update
            if round(bid*105)/100 > item[5]:
                cur.execute("UPDATE items SET bid = NULL WHERE itemid=%s",[item_id]) #če nova bid cena preseže buyout se 'bid' nastavi na null
            else:
                cur.execute("UPDATE items SET bid = %s WHERE itemid=%s",[round(bid*105)/100,item_id]) #sicer se poveča za 5% in zaokroži
            redirect("/item/"+item_id+"/")

    if buyout is not None: #buyout je 1 ali None
        if curuser[3]<=item[5]:
            napaka = "You don't have enough funds to do that"
        else:
            if item[9]:                                                                 #če prejšnji bidder obstaja:
                cur.execute("UPDATE users SET balance = balance + %s WHERE userID = %s", #prejšnji max bidder dobi denar nazaj
                    [item[15],item[9]])
            cur.execute("UPDATE users SET balance = balance - %s WHERE userID = %s", #novi kupec plača
                [item[5],curuser[0]])
            cur.execute("INSERT INTO sold_expired (SELECT * FROM ITEMS WHERE itemid=%s)",[item_id]) #shrani predmet v drugo tabelo za namene arhiviranja
            cur.execute("INSERT INTO transactions (itemid,buyerid,transaction,tr_date,tr_method) VALUES (%s,%s,%s,now(),'buyout')",[item_id,curuser[0],item[5]]) #zapiši transakcijo
            cur.execute("DELETE from items WHERE itemid=%s",[item_id]) #odstrani predmet iz tabele items
            redirect("/shop/")


    
    return template("product-details.html",
                           slike=slike,
                           atributi=atributi,
                           item = item,
                           napaka=napaka,
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
def register_get():
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
def account_get():
    curuser = get_user(auto_login=True)

    #Zavihki z podatki o trenutnih bidih, kupljenih predmetih in mojih predmetih
    cur.execute("SELECT itemid,itemname,bid,expires::date from items where current_bidder = %s",[curuser[0]])
    bids = cur.fetchall()
    
    cur.execute('''SELECT transactions.itemid,itemname,transaction,tr_method,tr_date::date FROM transactions
                JOIN sold_expired on sold_expired.itemid=transactions.itemid
                WHERE buyerid = %s''',
                [curuser[0]])
    purchased = cur.fetchall()

    cur.execute('''SELECT itemid,itemname,username,bid,buyout,posted_date,expires FROM items
                LEFT JOIN users ON users.userid = items.current_bidder
                WHERE ownerid = %s''',[curuser[0]])
    myitems = cur.fetchall()
    

        
    
    return template("account.html",
                           bids = bids,
                           purchased = purchased,
                           myitems = myitems,
                           stanje=curuser[3],
                           username=None,
                           ime=None,
                           napaka=None,
                           logged=curuser[2])


@post("/account/")
def account_post():
    """Depozit."""
    curuser = get_user(auto_login=True)
    deposit = Decimal(request.forms.deposit)

    cur.execute("SELECT itemid,itemname,bid,expires::date from items where current_bidder = %s",[curuser[0]])
    bids = cur.fetchall()
    cur.execute('''SELECT transactions.itemid,itemname,transaction,tr_method,tr_date::date FROM transactions
                JOIN sold_expired on sold_expired.itemid=transactions.itemid
                WHERE buyerid = %s''',
                [curuser[0]])
    purchased = cur.fetchall()

    cur.execute('''SELECT itemid,itemname,username,bid,buyout,posted_date,expires FROM items
                LEFT JOIN users ON users.userid = items.current_bidder
                WHERE ownerid = %s''',[curuser[0]])
    myitems = cur.fetchall()
    
    
    if deposit <= 0:
        return template("account.html",
                           bids = bids,
                           purchased = purchased,
                           myitems = myitems,
                           stanje=curuser[3],
                           username=None,
                           ime=None,
                           napaka="Please enter a positive amount",
                           logged=curuser[2])
        
    if deposit + curuser[3] > 999999:
        return template("account.html",
                           bids = bids,
                           purchased = purchased,
                           myitems = myitems,
                           stanje=curuser[3],
                           username=None,
                           ime=None,
                           napaka="Amount would exceed your balance limit (999.999,00€).",
                           logged=curuser[2])

    #če ni napake, dodaj denar uporabniku in prikaži novo stanje
    cur.execute("UPDATE users SET balance = balance + %s WHERE userID = %s", [deposit,curuser[0]])
    return template("account.html",
                           bids = bids,
                           purchased = purchased,
                           myitems = myitems,
                           stanje=curuser[3]+deposit,
                           username=None,
                           ime=None,
                           napaka="Your deposit was successful.",
                           logged=curuser[2])




@get("/new/")
def new_get():
    """Objavi nov predmet."""
    curuser = get_user(auto_login=True)
    query = dict(request.query) #poberemo parametre iz query stringa, shranimo v slovar
    seznam_kategorij = [] #seznam seznamov kategorij (po globinah)
    seznam_atributov = []
    cur.execute("SELECT categoryid,category_name FROM categories WHERE parentid is NULL") #dobi vse kategorije globine 0 in jih spravi v seznam kategorij
    seznam_kategorij.append(cur.fetchall())
    attrib = 0
    cleanquery = {} #tu shranimo samo ustrezne elemente slovarja query
    values = [None]*6
    for i in range(0,5):
        #globina kategorij zaenkrat največ pet
        try:
            ustreznost="krnekaj" #če nimamo izbranih podkategorij
            if i >0:
                #query stringi se lahko pomešajo (če uporabnik na silo spreminja url), napačni inputi itd. Ta if preveri, če hiearhija res drži, sicer vrne napako
                cur.execute("SELECT categoryid,category_name FROM categories WHERE categoryid = %s AND parentid = %s",[query[str(i)],query[str(i-1)]])
                ustreznost=cur.fetchone()
            if ustreznost == None:
                raise
            else:
                #če je vse v redu, dobi vse podkategorije izbrane kategorije in jih spravi v seznam seznamov
                cur.execute("SELECT categoryid,category_name FROM categories WHERE parentid = %s",[int(query[str(i)])])
                result = cur.fetchall()
                cleanquery[str(i)] = query[str(i)]

                #če ni pod-podkategorij za dano podkategorijo:
                if not result:
                    attrib = 1
                    break #prekini zanko, dobi možne atribute
                else:
                    seznam_kategorij.append(result)                   
        except:
            #če pride do napake (npr. query stringa ni bilo za dan 'i') nastavi vrednost v slovarju na 'dummy', da ga html ignorira
            query[str(i)] = "dummy"
            


    if attrib == 1:
        #če smo izbrali končno kategorijo, izberemo atribute za predmet:

        
        for i in cleanquery:
            cur.execute("SELECT attributeid,attributename,attributeclass FROM cat_attrib WHERE categoryid = %s",[cleanquery[str(i)]])
            seznam_atributov+= cur.fetchall()
        for i in seznam_atributov:
            values.append('') #default value za atribut preden ga uporabnik spremeni
            

    return template("new.html",
                           values = values,
                           attrib = attrib,
                           seznam=seznam_kategorij,
                           seznam_atributov = seznam_atributov,
                           query=query,
                           stanje=curuser[3],
                           username=None,
                           ime=None,
                           napaka=None,
                           logged=curuser[2])


@post("/new/")
def post_new():
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
        #prvih nekaj je standardnih atributov ki so skupni za vse predmete
        values[0] = request.forms.get("itemname")
        values[1] = request.forms.get("message")
        values[2] = request.forms.get("bidprice") or None
        values[3] = request.forms.get("buyoutprice") or None
        values[4] = request.forms.get("expiration") or '89'
        image = request.files.get("uploaded")
        for atribut in seznam_atributov:
            formname="a"+str(atribut[0])
            values.append(request.forms.get(formname)) #dobi preostale atribute
            
        #napake:
        if values[2] is None and values[3] is None:
            napaka = "At least one price must be specified!"
        if values[2] is not None and values[3] is not None:
            if int(values[2]) >= int(values[3]):
                napaka = "Bid price must be lower than the buyout price!"
        if len(values[0]) > 100:
            napaka = "Item name is too long!"
               
        if not napaka:
            #če ni napake, zapiši item v bazo
            cur.execute("INSERT INTO items(itemname, categoryid, ownerid, bid, buyout,expires,description,current_bidder,previous_bid) VALUES (%s,%s,%s,%s,%s,now()+%s::interval,%s,NULL,NULL)",
                (values[0],cleanquery[max(cleanquery)],curuser[0],values[2],values[3],values[4]+" days",values[1]))
            cur.execute("SELECT last_value FROM items_itemid_seq") #kateri id bo dobil nov predmet?
            itemid=cur.fetchone()
            for i in range(6,len(values)):
                if values[i] is not None: #uporabnik lahko pusti določen atribut prazen
                    cur.execute("INSERT INTO attributes(itemid,attributeid,value) VALUES (%s,%s,%s)",
                                (itemid[0],seznam_atributov[i-6][0],values[i]))
            if image is not None and napaka is None:
                #todo: max image size
                name, ext = os.path.splitext(image.filename)
                if ext.lower() not in ('.png','.jpg','.jpeg'):
                    napaka = 'Image file extension not allowed.'
                else:
                    save_path = os.getcwd()+"\\static\\images\\uploads"            
                    filename = str(itemid[0]) + ext
                    image.filename = filename
                    image.save(save_path) # appends upload.filename automatically
                    cur.execute("INSERT INTO images (itemid,imagename) values (%s,%s)",[itemid[0],filename])

                
        if napaka is None:
            napaka = "Item successfully submitted!"
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
def logout_get():
    """Pobriši cookie in preusmeri na login."""
    #deluje tako, da nastavi čas do izteka piškotka na 0.
    response.set_cookie('username',value="off",secret=secret,path='/', max_age=0)
    redirect('/shop/')



run(host='localhost', port=8080, debug=True)
