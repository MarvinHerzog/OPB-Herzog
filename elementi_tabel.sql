INSERT INTO categories(category_name,parentid) VALUES ('Home Computers',2);
INSERT INTO categories(category_name,parentid) VALUES ('Laptops',2);
INSERT INTO categories(category_name,parentid) VALUES ('Components',2);
INSERT INTO categories(category_name,parentid) VALUES ('Peripherals and Accessories',2);
INSERT INTO categories(category_name,parentid) VALUES ('Keyboards',26);
INSERT INTO categories(category_name,parentid) VALUES ('Mice',26);
INSERT INTO categories(category_name,parentid) VALUES ('Monitors',26);
INSERT INTO categories(category_name,parentid) VALUES ('RAM',25);
/* jj */
INSERT INTO categories(category_name,parentid) VALUES ('Commercial',4);
INSERT INTO categories(category_name,parentid) VALUES ('Land',4);
INSERT INTO categories(category_name,parentid) VALUES ('Residental',4);
INSERT INTO categories(category_name,parentid) VALUES ('Other Real Estate',4);
INSERT INTO categories(category_name,parentid) VALUES ('Cottages',33);
INSERT INTO categories(category_name,parentid) VALUES ('Garages',31);
INSERT INTO categories(category_name,parentid) VALUES ('Houses',33);
INSERT INTO categories(category_name,parentid) VALUES ('Appartments',33);
INSERT INTO categories(category_name,parentid) VALUES ('Offices',31);
INSERT INTO categories(category_name,parentid) VALUES ('Farms and Rural Properties',32);
INSERT INTO categories(category_name,parentid) VALUES ('Sport Properties',32);
INSERT INTO categories(category_name,parentid) VALUES ('Motorcycles',1);

INSERT INTO categories(category_name,parentid) VALUES ('Birds',5);
INSERT INTO categories(category_name,parentid) VALUES ('Fish',5);
INSERT INTO categories(category_name,parentid) VALUES ('Exotic Animals',5);
INSERT INTO categories(category_name,parentid) VALUES ('Rodents',5);
INSERT INTO categories(category_name,parentid) VALUES ('Reptiles',5);
INSERT INTO categories(category_name,parentid) VALUES ('Dogs',5);
INSERT INTO categories(category_name,parentid) VALUES ('Other',5);


INSERT INTO categories(category_name,parentid) VALUES ('Guitars & Basses',49);
INSERT INTO categories(category_name,parentid) VALUES ('Strings',49);
INSERT INTO categories(category_name,parentid) VALUES ('Brass',49);
INSERT INTO categories(category_name,parentid) VALUES ('Pianos, Keyboards & Organs',49);
INSERT INTO categories(category_name,parentid) VALUES ('Accordions',49);




/*Pri dodajanju atributov za kategorije VEDNO daj atribut staršu,
 če je to mogoče (tj. če ustreza vsem otrokom starša).
npr. "color" dodaš kategoriji "vehicles" ne pa k "Mitsubishi",
 ker imajo vsa vozila atribut barvo */
 
 /* attributeclass (katerega podatkovnega tipa je atribut?): npr. int, numeric(n,d), text, itd.*/
 INSERT INTO cat_attrib(attributename,attributeclass,categoryid) VALUES ('Color','TEXT',1); 
 INSERT INTO cat_attrib(attributename,attributeclass,categoryid) VALUES ('kW','INTEGER',1); 
 INSERT INTO cat_attrib(attributename,attributeclass,categoryid) VALUES ('Number of pages','INTEGER',20);
 INSERT INTO cat_attrib(attributename,attributeclass,categoryid) VALUES ('Age','INTEGER',1);
 INSERT INTO cat_attrib(attributename,attributeclass,categoryid) VALUES ('Maximum Resolution','TEXT',29);
 INSERT INTO cat_attrib(attributename,attributeclass,categoryid) VALUES ('Screen size (")','INTEGER',29); 
 INSERT INTO cat_attrib(attributename,attributeclass,categoryid) VALUES ('Refresh rate','TEXT',29);
 /* jj */
INSERT INTO cat_attrib(attributename,attributeclass,categoryid) VALUES ('Size (m^2)', 'INTEGER', 4);
 INSERT INTO cat_attrib(attributename,attributeclass,categoryid) VALUES ('Location','TEXT', 4);
 INSERT INTO cat_attrib(attributename,attributeclass,categoryid) VALUES ('Age (years)', 'INTEGER', 4);
INSERT INTO cat_attrib(attributename,attributeclass,categoryid) VALUES ('Mileage', 'INTEGER', 1);
INSERT INTO cat_attrib(attributename,attributeclass,categoryid) VALUES ('Fuel Type', 'text', 1);


INSERT INTO cat_attrib(attributename,attributeclass,categoryid) VALUES ('Age(years)','INTEGER',5);
 INSERT INTO cat_attrib(attributename,attributeclass,categoryid) VALUES ('Breed','TEXT',7);
 INSERT INTO cat_attrib(attributename,attributeclass,categoryid) VALUES ('Breed','TEXT',39);
 INSERT INTO cat_attrib(attributename,attributeclass,categoryid) VALUES ('Fur Color','TEXT',39);
 INSERT INTO cat_attrib(attributename,attributeclass,categoryid) VALUES ('Fur Color','TEXT',7);
 
 