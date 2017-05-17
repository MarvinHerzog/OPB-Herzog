drop table IF EXISTS users CASCADE;
drop TABLE IF EXISTS categories CASCADE;
drop table IF EXISTS subcategories CASCADE;
drop table IF EXISTS items CASCADE;
drop table IF EXISTS sold_expired CASCADE;
drop table IF EXISTS transactions CASCADE;
drop table IF EXISTS attributes CASCADE;
drop table IF EXISTS cat_attrib CASCADE;

create table users(
    userID serial PRIMARY KEY NOT NULL,
    username TEXT NOT NULL UNIQUE,
    name TEXT NOT NULL,
    surname TEXT NOT NULL,
    email TEXT NOT NULL UNIQUE,
    password TEXT NOT NULL,
    balance numeric(9,2) NOT NULL,
    address TEXT
    );

create table categories(
    categoryID serial primary key NOT NULL,
    category_name TEXT NOT NULL
    );

create table subcategories(
    childID int REFERENCES categories (categoryID) ON DELETE CASCADE,
    parentID int REFERENCES categories (categoryID) ON DELETE CASCADE,
    PRIMARY KEY(childID, parentID),
    CONSTRAINT IDs_are_identical CHECK (childID <> parentID)
    );
	
	
	


create table items(
    itemID serial primary key NOT NULL,
    itemname TEXT NOT NULL,
    categoryID int NOT NULL REFERENCES categories(categoryID) ON DELETE CASCADE,
    ownerID int NOT NULL REFERENCES users(userID) ON DELETE CASCADE,
    bid numeric(9,2),
    buyout numeric(9,2),
    posted_date TIMESTAMP DEFAULT now() NOT NULL,
    expires TIMESTAMP NOT NULL,
    description TEXT NOT NULL,
	current_bidder INT REFERENCES users(userID),
    CONSTRAINT expires_too_fast CHECK (expires >= posted_date + interval '24 hours'), /*bid<buyout constraint v .py */
    CONSTRAINT expires_too_late CHECK (expires <= posted_date + interval '3 months'),
    CONSTRAINT no_price CHECK(starting_bid IS NOT NULL OR buyout_price IS NOT NULL)
    );
    
create table attributes(
	itemID int NOT NULL REFERENCES items(itemID) ON DELETE CASCADE,
	attributeID int NOT NULL,
	value TEXT NOT NULL,
	PRIMARY KEY(itemID, attributeID)
	); /*poskrbi v aplikaciji da ne shranjujes NULL atributov.. ali pac?*/
	
create table cat_attrib(
	attributeID SERIAL PRIMARY KEY NOT NULL,
	attributename TEXT NOT NULL,
	attributeclass TEXT NOT NULL,
	categoryID int REFERENCES categories(categoryID) ON DELETE CASCADE
	); /*podkategorija naj implicitno deduje atribute vseh svojih starsev */
	
CREATE TABLE images (
	itemID int REFERENCES items(ITEMID) NOT NULL,
	imagename TEXT NOT NULL UNIQUE);
    
CREATE TABLE sold_expired(
    itemID serial primary key NOT NULL,
    itemname TEXT NOT NULL,
    categoryID int NOT NULL REFERENCES categories(categoryID) ON DELETE CASCADE,
    ownerID int NOT NULL REFERENCES users(userID) ON DELETE CASCADE,
    starting_bid numeric(9,2),
    buyout_price numeric(9,2),
    posted_date TIMESTAMP DEFAULT now() NOT NULL,
    expires TIMESTAMP NOT NULL,
    description TEXT NOT NULL,
    CONSTRAINT expires_too_fast CHECK (expires >= posted_date + interval '24 hours'), /*bid<buyout constraint v .py */
    CONSTRAINT expires_too_late CHECK (expires <= posted_date + interval '3 months'),
    CONSTRAINT no_price CHECK(starting_bid IS NOT NULL OR buyout_price IS NOT NULL)
    );
    
CREATE TABLE transactions(
    itemID int REFERENCES items(itemID) NOT NULL,
    buyerID int REFERENCES users(userID) NOT NULL,
    transaction numeric(9,2) NOT NULL,
    tr_date TIMESTAMP NOT NULL,
    tr_method TEXT NOT NULL /*bid/buyout/deposit*/
    );

GRANT ALL ON ALL TABLES IN SCHEMA public TO martinp;
GRANT ALL ON ALL SEQUENCES IN SCHEMA public TO martinp;
GRANT ALL ON ALL TABLES IN SCHEMA public TO jakobj;
GRANT ALL ON ALL SEQUENCES IN SCHEMA public TO jakobj;
GRANT SELECT, UPDATE, INSERT ON ALL TABLES IN SCHEMA public TO javnost;
GRANT ALL ON ALL SEQUENCES IN SCHEMA public TO javnost;
























    