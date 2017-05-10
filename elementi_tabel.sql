INSERT INTO categories(category_name,parentid) VALUES ('Home Computers',2);
INSERT INTO categories(category_name,parentid) VALUES ('Laptops',2);
INSERT INTO categories(category_name,parentid) VALUES ('Components',2);
INSERT INTO categories(category_name,parentid) VALUES ('Peripherals and Accessories',2);
INSERT INTO categories(category_name,parentid) VALUES ('Keyboards',26);
INSERT INTO categories(category_name,parentid) VALUES ('Mice',26);
INSERT INTO categories(category_name,parentid) VALUES ('Monitors',26);
INSERT INTO categories(category_name,parentid) VALUES ('RAM',25);

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
 INSERT INTO cat_attrib(attributename,attributeclass,categoryid) VALUES ('Memory','INTEGER',30);
 