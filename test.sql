drop table IF EXISTS users CASCADE;
drop TABLE IF EXISTS categories CASCADE;
drop table IF EXISTS subcategories CASCADE;
drop table IF EXISTS items CASCADE;
drop table IF EXISTS sold_expired CASCADE;
drop table IF EXISTS transactions CASCADE;

create table users(
    userID serial PRIMARY KEY NOT NULL,
    username TEXT NOT NULL UNIQUE,
    name TEXT NOT NULL,
    surname TEXT NOT NULL,
    email TEXT NOT NULL UNIQUE,
    password TEXT NOT NULL,
    balance numeric(7,2) NOT NULL,
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
    starting_bid numeric(7,2),
    buyout_price numeric(7,2),
    posted_date TIMESTAMP DEFAULT now() NOT NULL,
    expires TIMESTAMP NOT NULL,
    description TEXT NOT NULL,
    CONSTRAINT expires_too_fast CHECK (expires >= posted_date + interval '24 hours'), /*bid<buyout constraint v .py */
    CONSTRAINT expires_too_late CHECK (expires <= posted_date + interval '3 months'),
    CONSTRAINT no_price CHECK(starting_bid IS NOT NULL OR buyout_price IS NOT NULL)
    );
    
    
CREATE TABLE sold_expired(
    itemID serial primary key NOT NULL,
    itemname TEXT NOT NULL,
    categoryID int NOT NULL REFERENCES categories(categoryID) ON DELETE CASCADE,
    ownerID int NOT NULL REFERENCES users(userID) ON DELETE CASCADE,
    starting_bid numeric(7,2),
    buyout_price numeric(7,2),
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
    sold_for numeric(7,2) NOT NULL,
    date_sold TIMESTAMP NOT NULL,
    purchase_method TEXT NOT NULL
    )
    