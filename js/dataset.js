// dataset.js — Fake identity + bank account dataset generator
// Generates a complete personal dataset for each generated IBAN:
// identity (name, DOB, address, phone, email, occupation, nationality),
// documents (passport, national ID, driving licence, vehicle reg, social security),
// bank account (bank from swift_codes.json, branch, IBAN, SWIFT/BIC).
// Pure client-side. All data is fictional and random.
(function() {
  'use strict';

  // ── Loaded bank database (filled via loadBanks) ────────────────
  var BANKS = {};       // country code -> array of {bic, bankName, city}
  var BANKS_LOADED = false;

  // ── Name pools by culture/locale ────────────────────────────────
  var LOCALES = {
    DE: { first: ['Anna','Max','Julia','Lukas','Sophie','Leon','Marie','Felix','Emma','Jonas','Lea','Tim','Lena','Paul','Mia','David','Hannah','Nico','Laura','Simon'], last: ['Müller','Schmidt','Schneider','Fischer','Weber','Meyer','Wagner','Becker','Hoffmann','Schäfer','Koch','Bauer','Richter','Klein','Wolf','Neumann','Schwarz','Zimmermann','Braun','Krüger'] },
    FR: { first: ['Léa','Hugo','Chloé','Louis','Emma','Gabriel','Camille','Jules','Manon','Arthur','Sarah','Lucas','Inès','Adam','Julia','Nathan','Alice','Tom','Maëlys','Enzo'], last: ['Martin','Bernard','Thomas','Petit','Robert','Richard','Durand','Dubois','Moreau','Laurent','Simon','Michel','Lefebvre','Garcia','David','Bertrand','Roux','Vincent','Fournier','Morel'] },
    ES: { first: ['Lucía','Hugo','Martina','Mateo','Sofía','Leo','Valeria','Daniel','Paula','Pablo','Julia','Álvaro','Sara','Adrián','Carla','Diego','Alba','Mario','Elena','Marcos'], last: ['García','Rodríguez','González','Fernández','López','Martínez','Sánchez','Pérez','Gómez','Martín','Jiménez','Ruiz','Hernández','Díaz','Moreno','Álvarez','Romero','Alonso','Gutiérrez','Navarro'] },
    IT: { first: ['Sofia','Lorenzo','Giulia','Leonardo','Aurora','Francesco','Alice','Alessandro','Ginevra','Matteo','Emma','Gabriele','Giorgia','Riccardo','Beatrice','Tommaso','Chiara','Federico','Vittoria','Antonio'], last: ['Rossi','Russo','Ferrari','Esposito','Bianchi','Romano','Colombo','Ricci','Marino','Greco','Bruno','Gallo','Conti','De Luca','Mancini','Costa','Giordano','Rizzo','Lombardi','Moretti'] },
    GB: { first: ['Oliver','Amelia','George','Isla','Harry','Ava','Noah','Charlotte','Jack','Sophia','Leo','Mia','Oscar','Grace','Arthur','Freya','Charlie','Florence','Henry','Poppy'], last: ['Smith','Jones','Williams','Taylor','Brown','Davies','Evans','Wilson','Thomas','Roberts','Johnson','Lewis','Walker','Robinson','Wood','Thompson','White','Watson','Jackson','Wright'] },
    NL: { first: ['Daan','Emma','Sem','Julia','Lucas','Tess','Finn','Sophie','Milan','Lotte','Levi','Zoë','Bram','Fleur','Lars','Noor','Jesse','Sanne','Thijs','Evi'], last: ['de Jong','Jansen','de Vries','van den Berg','van Dijk','Bakker','Janssen','Visser','Smit','Meijer','de Boer','Mulder','de Groot','Bos','Vos','Peters','Hendriks','van Leeuwen','Dekker','Brouwer'] },
    SE: { first: ['Erik','Maja','Oscar','Astrid','Lucas','Ebba','William','Alice','Hugo','Elsa','Axel','Maja','Viktor','Signe','Gustav','Alma','Nils','Klara','Emil','Linnea'], last: ['Andersson','Johansson','Karlsson','Nilsson','Eriksson','Larsson','Olsson','Persson','Svensson','Gustafsson','Pettersson','Jonsson','Jansson','Hansson','Bengtsson','Jönsson','Lindberg','Jakobsson','Magnusson','Olofsson'] },
    NO: { first: ['Olav','Emma','Magnus','Nora','Lars','Maja','Anders','Sofie','Henrik','Ida','Eirik','Ingrid','Sondre','Thea','Markus','Astrid','Jonas','Mari','Kristian','Amalie'], last: ['Hansen','Johansen','Olsen','Larsen','Andersen','Pedersen','Nilsen','Kristiansen','Jensen','Karlsen','Johnsen','Pettersen','Eriksen','Berg','Haugen','Hagen','Dahl','Lund','Bakke','Moen'] },
    DK: { first: ['William','Emma','Noah','Ida','Carl','Freja','Oscar','Clara','Elias','Alma','Oliver','Mille','Magnus','Sofie','August','Frida','Emil','Lærke','Mikkel','Agnes'], last: ['Jensen','Nielsen','Hansen','Pedersen','Andersen','Christensen','Larsen','Sørensen','Rasmussen','Jørgensen','Petersen','Madsen','Kristensen','Olsen','Thomsen','Christiansen','Poulsen','Johansen','Møller','Lund'] },
    FI: { first: ['Onni','Aino','Elias','Aada','Leo','Helmi','Eino','Enni','Väinö','Lumi','Emil','Aurora','Oliver','Iida','Daniel','Venla','Julius','Nea','Matias','Linnea'], last: ['Korhonen','Virtanen','Mäkinen','Nieminen','Mäkelä','Hämäläinen','Laine','Heikkinen','Koskinen','Järvinen','Lehtonen','Lehtinen','Saarinen','Salminen','Heinonen','Niemi','Heikkilä','Kinnunen','Salonen','Turunen'] },
    PL: { first: ['Jakub','Zuzanna','Szymon','Julia','Jan','Maja','Antoni','Hanna','Filip','Aleksandra','Michał','Natalia','Bartosz','Wiktoria','Mateusz','Oliwia','Kacper','Amelia','Tymoteusz','Zofia'], last: ['Nowak','Kowalski','Wiśniewski','Wójcik','Kowalczyk','Kamiński','Lewandowski','Zieliński','Szymański','Woźniak','Dąbrowski','Kozłowski','Jankowski','Mazur','Krawczyk','Wojciechowski','Piotrowski','Grabowski','Pawłowski','Kaczmarek'] },
    CH: { first: ['Luca','Mia','Noah','Emma','Liam','Lina','Elias','Lea','Julian','Sofia','Leon','Anna','Nico','Laura','David','Sara','Jan','Elena','Samuel','Clara'], last: ['Müller','Meier','Schmid','Keller','Weber','Huber','Schneider','Meyer','Steiner','Fischer','Brun','Gerber','Baumann','Frei','Moser','Zimmermann','Roth','Aebi','Stalder','Widmer'] },
    AT: { first: ['Lukas','Anna','Felix','Marie','David','Sophie','Max','Lea','Jakob','Lena','Simon','Julia','Florian','Laura','Paul','Nina','Jonas','Katharina','Fabian','Sarah'], last: ['Gruber','Huber','Bauer','Wagner','Müller','Pichler','Steiner','Moser','Mayer','Hofer','Leitner','Berger','Fuchs','Eder','Fischer','Winkler','Schwarz','Weber','Reiter','Schmid'] },
    BE: { first: ['Lucas','Emma','Arthur','Louise','Louis','Camille','Noah','Juliette','Adam','Maud','Victor','Léa','Jules','Chloé','Maxime','Marie','Nathan','Ella','Simon','Alice'], last: ['Peeters','Janssens','Maes','Jacobs','Mertens','Willems','Claes','Goossens','Wouters','De Smet','Dubois','Lambert','Martin','Dupont','Simon','Leroy','Moreau','Laurent','Van Damme','Vermeulen'] },
    PT: { first: ['João','Maria','Francisco','Leonor','Santiago','Matilde','Afonso','Beatriz','Tomás','Carolina','Miguel','Mariana','Duarte','Inês','Gonçalo','Margarida','Pedro','Ana','Tiago','Sofia'], last: ['Silva','Santos','Ferreira','Pereira','Oliveira','Costa','Rodrigues','Martins','Jesus','Sousa','Fernandes','Gonçalves','Gomes','Lopes','Marques','Alves','Almeida','Ribeiro','Pinto','Carvalho'] },
    IE: { first: ['Jack','Aoife','James','Grace','Conor','Ella','Sean','Lucy','Oisín','Sophie','Cian','Chloe','Darragh','Ciara','Fionn','Hannah','Liam','Niamh','Patrick','Sarah'], last: ['Murphy','Kelly','O\'Brien','Walsh','O\'Connor','Ryan','Byrne','O\'Neill','O\'Reilly','Doyle','McCarthy','Gallagher','O\'Doherty','Kennedy','Lynch','Murray','Quinn','Moore','McLoughlin','O\'Donnell'] },
    GR: { first: ['Giorgos','Maria','Dimitris','Eleni','Nikos','Katerina','Costas','Sofia','Yannis','Georgia','Panos','Anna','Vasilis','Eva','Kostas','Dimitra','Takis','Niki','Spyros','Marina'], last: ['Papadopoulos','Papadakis','Nikolaou','Dimitriou','Georgiou','Vasileiou','Karagiannis','Papageorgiou','Makris','Oikonomou','Christodoulou','Antoniou','Katsaros','Alexandrou','Panagiotopoulos','Stavropoulos','Papanikolaou','Kapsalis','Vlachos','Roussos'] },
    HU: { first: ['Bence','Lili','Máté','Anna','Levente','Zsófia','Ádám','Réka','Dániel','Eszter','Balázs','Luca','Péter','Boglárka','Gergő','Nóra','Márk','Fanni','Tamas','Kata'], last: ['Nagy','Kovács','Tóth','Szabó','Horváth','Varga','Kiss','Molnár','Németh','Farkas','Balogh','Papp','Lakatos','Takács','Juhász','Sándor','Oláh','Szalai','Kelemen','Bognár'] },
    CZ: { first: ['Jakub','Eliška','Tomáš','Anna','Adam','Tereza','Matěj','Karolína','Jan','Adéla','Vojtěch','Barbora','Ondřej','Veronika','Filip','Kateřina','Lukáš','Lucie','David','Natálie'], last: ['Novák','Svoboda','Novotný','Dvořák','Černý','Procházka','Kučera','Veselý','Horák','Němec','Marek','Pospíšil','Pokorný','Hájek','Král','Jelínek','Růžička','Beneš','Fiala','Sedláček'] },
    HR: { first: ['Ivan','Ana','Marko','Iva','Luka','Mia','Ante','Petra','Filip','Sara','Matej','Lucija','Josip','Karla','Petar','Ema','Domagoj','Nika','Toni','Lea'], last: ['Horvat','Kovačević','Babić','Marić','Jurić','Novak','Kovačić','Knežević','Vuković','Božić','Pavlović','Matić','Tomić','Kralj','Perić','Mijatović','Grgić','Marković','Milić','Petrović'] },
    RO: { first: ['Andrei','Maria','Alexandru','Elena','Mihai','Ioana','Ionut','Ana','George','Andreea','Stefan','Cristina','Daniel','Gabriela','Adrian','Raluca','Marius','Diana','Florin','Simona'], last: ['Popa','Popescu','Ionescu','Stan','Dumitrescu','Constantin','Stoica','Radu','Dobre','Gheorghe','Marin','Ilie','Ursu','Tudor','Florea','Enache','Anghel','Dinu','Cristea','Munteanu'] },
    BG: { first: ['Georgi','Maria','Ivan','Elena','Dimitar','Ralitsa','Nikolay','Viktoria','Petar','Gergana','Krasimir','Tsvetelina','Stoyan','Desislava','Hristo','Silvia','Vladimir','Magdalena','Plamen','Petya'], last: ['Ivanov','Georgiev','Dimitrov','Petrov','Hristov','Stoyanov','Nikolov','Todorov','Iliev','Atanasov','Vasilev','Angelov','Kolev','Pavlov','Popov','Kanev','Borisov','Marinov','Kostov','Radev'] },
    IS: { first: ['Jón','Guðrún','Sigurður','Anna','Björn','Helga','Ólafur','Kristín','Einar','Margrét','Gunnar','Sigrún','Davíð','Jóhanna','Magnús','Katrín','Stefán','Ragnheiður','Aron','Sólveig'], last: ['Jónsdóttir','Jónsson','Guðmundsdóttir','Guðmundsson','Sigurðardóttir','Sigurðsson','Gunnarsdóttir','Gunnarsson','Ólafsdóttir','Ólafsson','Einarsdóttir','Einarsson','Stefánsdóttir','Stefánsson','Magnúsdóttir','Magnússon','Björnsdóttir','Björnsson','Kristinsdóttir','Kristinsson'] },
    LV: { first: ['Jānis','Anna','Mārtiņš','Laura','Artūrs','Ieva','Rihards','Elīna','Marks','Līga','Edgars','Kristīne','Roberts','Zane','Gustavs','Aija','Daniels','Marta','Emīls','Sintija'], last: ['Bērziņš','Kalniņš','Ozoliņš','Liepiņš','Jansons','Krūmiņš','Eglītis','Vītols','Pētersons','Ozols','Grīnbergs','Vasiļjevs','Miezis','Ābele','Zariņš','Krastiņš','Ivanovs','Bērziņa','Kalniņa','Ozoliņa'] },
    LT: { first: ['Lukas','Ugnė','Matas','Emilija','Domantas','Gabija','Jonas','Miglė','Rokas','Austėja','Karolis','Rugilė','Dovydas','Meda','Tomas','Kotryna','Jokūbas','Vakarė','Nedas','Liepa'], last: ['Kazlauskas','Petrauskas','Jankauskas','Stankevičius','Vasiliauskas','Butkus','Paulauskas','Urbonas','Kavaliauskas','Rutkauskas','Žukauskas','Baranauskas','Vaitkus','Šimkus','Rimkus','Navickas','Urbonavičius','Sakalauskas','Morkūnas','Pocius'] },
    EE: { first: ['Marten','Liis','Rasmus','Grete','Karl','Kerttu','Jaan','Annika','Oliver','Mari','Hendrik','Elisabeth','Mikk','Kadri','Robin','Triin','Taaniel','Laura','Kevin','Sandra'], last: ['Tamm','Mägi','Sepp','Kask','Rebane','Ilves','Saar','Kukk','Jõgi','Pärn','Koppel','Kuusk','Oja','Lepp','Õun','Mets','Peterson','Laas','Karu','Toom'] },
    CY: { first: ['Andreas','Maria','Christos','Eleni','George','Anna','Michael','Sofia','Panayiotis','Marina','Constantinos','Christina','Nicos','Andri','Savvas','Evi','Kyriakos','Ioanna','Petros','Georgia'], last: ['Christodoulou','Georgiou','Constantinou','Papadopoulos','Ioannou','Kyriakou','Andreou','Michael','Antoniou','Nikolaou','Panayiotou','Savva','Chrysostomou','Demetriou','Hadjipavlou','Papaioannou','Pavlou','Xenofontos','Neophytou','Charalambous'] },
    LU: { first: ['Luc','Sophie','Marc','Laura','Paul','Anna','Jean','Julia','Pierre','Marie','Thomas','Sarah','Nicolas','Camille','Patrick','Julie','Eric','Nina','David','Léa'], last: ['Schmit','Muller','Wagner','Thill','Weber','Hoffmann','Klein','Fischer','Schroeder','Reuter','Jung','Lentz','Bauer','Schneider','Krier','Goergen','Wirtz','Eicher','Schroeder','Meyer'] },
    MT: { first: ['Jean Paul','Maria','Matthew','Sarah','Luke','Emily','Daniel','Jessica','Andrew','Michelle','Kurt','Francesca','Mark','Stephanie','David','Martina','Stefan','Nicole','Christian','Rebecca'], last: ['Borg','Camilleri','Vella','Farrugia','Zammit','Galea','Micallef','Grech','Attard','Spiteri','Azzopardi','Schembri','Fenech','Cutajar','Agius','Gatt','Mizzi','Cassar','Portelli','Vassallo'] },
    SI: { first: ['Luka','Maja','Jan','Eva','Nejc','Ana','Marko','Nina','Matej','Sara','Žiga','Lana','Tim','Kaja','Urban','Maša','Aleš','Tina','Blaž','Nika'], last: ['Novak','Horvat','Kovačič','Krajnc','Zupančič','Potočnik','Kovač','Mlakar','Vidmar','Kos','Golob','Turk','Božič','Korošec','Rozman','Kotnik','Erjavec','Kavčič','Petek','Jelen'] },
    SK: { first: ['Jakub','Ema','Martin','Nina','Tomáš','Sofia','Adam','Katarína','Samuel','Laura','Filip','Viktória','Matej','Barbora','Lukáš','Simona','Michal','Terézia','Peter','Zuzana'], last: ['Horváth','Kováč','Varga','Tóth','Szabó','Molnár','Nagy','Baláž','Kollár','Lukáč','Pavlík','Bartoš','Dudáš','Krajčí','Michalík','Petráš','Marek','Šimko','Hudák','Gajdoš'] },
    TR: { first: ['Mehmet','Ayşe','Mustafa','Fatma','Ahmet','Elif','Ali','Zeynep','Hüseyin','Merve','İbrahim','Derya','Murat','Gamze','Osman','Büşra','Emre','Selin','Yusuf','Ece'], last: ['Yılmaz','Kaya','Demir','Şahin','Çelik','Yıldız','Yıldırım','Öztürk','Aydın','Özdemir','Arslan','Doğan','Kılıç','Aslan','Çetin','Kara','Koç','Kurt','Özkan','Şimşek'] },
    AE: { first: ['Mohammed','Fatima','Ahmed','Aisha','Omar','Maryam','Ali','Zainab','Khalid','Salma','Hamad','Noura','Abdullah','Hessa','Saeed','Mariam','Rashid','Latifa','Yousef','Amina'], last: ['Al Maktoum','Al Nahyan','Al Hashimi','Al Marri','Al Mansouri','Al Falasi','Al Zaabi','Al Darmaki','Al Marzooqi','Al Shehhi','Al Hameli','Al Blooshi','Al Ketbi','Al Nuaimi','Al Sharji','Al Dhaheri','Al Habsi','Al Suwaidi','Al Ameri','Al Rashedi'] },
    SA: { first: ['Mohammed','Fatima','Ahmed','Aisha','Abdullah','Noura','Omar','Sara','Khalid','Maha','Fahad','Reem','Abdulaziz','Lama','Sultan','Nada','Mansour','Joud','Bandar','Dana'], last: ['Al-Saud','Al-Harbi','Al-Otaibi','Al-Qahtani','Al-Dossari','Al-Zahrani','Al-Ghamdi','Al-Mutairi','Al-Anazi','Al-Shammari','Al-Subaie','Al-Malki','Al-Rashidi','Al-Hazmi','Al-Asmari','Al-Juhani','Al-Shehri','Al-Ruwaili','Al-Ahmadi','Al-Thunayan'] },
    BR: { first: ['João','Maria','Pedro','Ana','Lucas','Julia','Gabriel','Camila','Matheus','Larissa','Rafael','Beatriz','Thiago','Mariana','Gustavo','Leticia','Bruno','Amanda','Felipe','Carolina'], last: ['Silva','Santos','Oliveira','Souza','Rodrigues','Ferreira','Alves','Pereira','Lima','Gomes','Ribeiro','Martins','Carvalho','Almeida','Lopes','Soares','Fernandes','Vieira','Barbosa','Rocha'] },
  };

  // ── City pools (fallback per continent, plus localized where available) ──
  var CITIES = {
    DE: ['Berlin','Munich','Hamburg','Cologne','Frankfurt','Stuttgart','Düsseldorf','Leipzig','Dortmund','Essen','Bremen','Dresden','Hanover','Nuremberg','Mannheim'],
    FR: ['Paris','Marseille','Lyon','Toulouse','Nice','Nantes','Strasbourg','Montpellier','Bordeaux','Lille','Rennes','Reims','Toulon','Grenoble','Dijon'],
    ES: ['Madrid','Barcelona','Valencia','Seville','Zaragoza','Málaga','Murcia','Palma','Las Palmas','Bilbao','Alicante','Córdoba','Valladolid','Vigo','Gijón'],
    IT: ['Rome','Milan','Naples','Turin','Palermo','Genoa','Bologna','Florence','Bari','Catania','Venice','Verona','Messina','Padua','Trieste'],
    GB: ['London','Birmingham','Manchester','Leeds','Glasgow','Liverpool','Newcastle','Sheffield','Bristol','Cardiff','Belfast','Edinburgh','Leicester','Coventry','Brighton'],
    NL: ['Amsterdam','Rotterdam','The Hague','Utrecht','Eindhoven','Groningen','Tilburg','Almere','Breda','Nijmegen','Haarlem','Arnhem','Enschede','Amersfoort','Apeldoorn'],
    SE: ['Stockholm','Gothenburg','Malmö','Uppsala','Västerås','Örebro','Linköping','Helsingborg','Jönköping','Norrköping','Lund','Umeå','Gävle','Borås','Södertälje'],
    NO: ['Oslo','Bergen','Trondheim','Stavanger','Drammen','Fredrikstad','Kristiansand','Sandnes','Tromsø','Sarpsborg','Skien','Ålesund','Sandefjord','Haugesund','Bodø'],
    DK: ['Copenhagen','Aarhus','Odense','Aalborg','Esbjerg','Randers','Kolding','Horsens','Vejle','Roskilde','Herning','Silkeborg','Næstved','Fredericia','Viborg'],
    FI: ['Helsinki','Espoo','Tampere','Vantaa','Oulu','Turku','Jyväskylä','Lahti','Kuopio','Pori','Kouvola','Joensuu','Lappeenranta','Hämeenlinna','Vaasa'],
    PL: ['Warsaw','Kraków','Łódź','Wrocław','Poznań','Gdańsk','Szczecin','Bydgoszcz','Lublin','Białystok','Katowice','Gdynia','Częstochowa','Radom','Toruń'],
    CH: ['Zurich','Geneva','Basel','Lausanne','Bern','Winterthur','Lucerne','St. Gallen','Lugano','Biel','Thun','Köniz','Fribourg','La Chaux-de-Fonds','Schaffhausen'],
    AT: ['Vienna','Graz','Linz','Salzburg','Innsbruck','Klagenfurt','Villach','Wels','Sankt Pölten','Dornbirn','Wiener Neustadt','Steyr','Feldkirch','Bregenz','Leoben'],
    BE: ['Brussels','Antwerp','Ghent','Charleroi','Liège','Bruges','Namur','Leuven','Mons','Aalst','Mechelen','Kortrijk','Ostend','Hasselt','Sint-Niklaas'],
    PT: ['Lisbon','Porto','Amadora','Braga','Coimbra','Funchal','Setúbal','Almada','Vila Nova de Gaia','Aveiro','Évora','Cascais','Portimão','Guimarães','Viseu'],
    IE: ['Dublin','Cork','Limerick','Galway','Waterford','Drogheda','Dundalk','Swords','Bray','Navan','Kilkenny','Ennis','Tralee','Carlow','Sligo'],
    GR: ['Athens','Thessaloniki','Patras','Piraeus','Larissa','Heraklion','Volos','Rhodes','Ioannina','Chania','Kavala','Kalamata','Serres','Alexandroupoli','Trikala'],
    HU: ['Budapest','Debrecen','Szeged','Miskolc','Pécs','Győr','Nyíregyháza','Kecskemét','Székesfehérvár','Szombathely','Szolnok','Tatabánya','Kaposvár','Érd','Veszprém'],
    CZ: ['Prague','Brno','Ostrava','Plzeň','Liberec','Olomouc','České Budějovice','Hradec Králové','Ústí nad Labem','Pardubice','Zlín','Havířov','Kladno','Most','Opava'],
    HR: ['Zagreb','Split','Rijeka','Osijek','Zadar','Slavonski Brod','Pula','Sesvete','Karlovac','Varaždin','Šibenik','Dubrovnik','Bjelovar','Vinkovci','Koprivnica'],
    RO: ['Bucharest','Cluj-Napoca','Timișoara','Iași','Constanța','Craiova','Brașov','Galați','Ploiești','Oradea','Brăila','Arad','Pitești','Sibiu','Bacău'],
    BG: ['Sofia','Plovdiv','Varna','Burgas','Ruse','Stara Zagora','Pleven','Sliven','Dobrich','Shumen','Pernik','Haskovo','Yambol','Pazardzhik','Blagoevgrad'],
    IS: ['Reykjavík','Kópavogur','Hafnarfjörður','Akureyri','Reykjanesbær','Garðabær','Mosfellsbær','Akranes','Selfoss','Ísafjörður'],
    LV: ['Riga','Daugavpils','Liepāja','Jelgava','Jūrmala','Ventspils','Rēzekne','Valmiera','Ogre','Jēkabpils','Tukums','Salaspils','Cēsis','Kuldīga','Olaine'],
    LT: ['Vilnius','Kaunas','Klaipėda','Šiauliai','Panevėžys','Alytus','Marijampolė','Mažeikiai','Jonava','Utena','Kėdainiai','Telšiai','Visaginas','Tauragė','Ukmergė'],
    EE: ['Tallinn','Tartu','Narva','Pärnu','Kohtla-Järve','Viljandi','Maardu','Rakvere','Kuressaare','Sillamäe','Valga','Võru','Jõhvi','Haapsalu','Keila'],
    CY: ['Nicosia','Limassol','Larnaca','Paphos','Famagusta','Kyrenia','Protaras','Paralimni','Ayia Napa','Peyia'],
    LU: ['Luxembourg','Esch-sur-Alzette','Differdange','Dudelange','Ettelbruck','Diekirch','Wiltz','Echternach','Rumelange','Grevenmacher'],
    MT: ['Valletta','Birkirkara','Mosta','Qormi','Sliema','St. Julian\'s','Rabat','Naxxar','Zabbar','Fgura','Attard','Marsaskala','Paola','San Ġwann','Swieqi'],
    SI: ['Ljubljana','Maribor','Celje','Kranj','Koper','Velenje','Novo Mesto','Ptuj','Trbovlje','Kamnik','Jesenice','Domžale','Nova Gorica','Škofja Loka','Murska Sobota'],
    SK: ['Bratislava','Košice','Prešov','Žilina','Nitra','Banská Bystrica','Trnava','Martin','Trenčín','Poprad','Prievidza','Zvolen','Považská Bystrica','Michalovce','Nové Zámky'],
    TR: ['Istanbul','Ankara','Izmir','Bursa','Antalya','Adana','Konya','Gaziantep','Mersin','Kayseri','Eskişehir','Diyarbakır','Samsun','Denizli','Şanlıurfa'],
    AE: ['Dubai','Abu Dhabi','Sharjah','Al Ain','Ajman','Ras Al Khaimah','Fujairah','Umm Al Quwain'],
    SA: ['Riyadh','Jeddah','Mecca','Medina','Dammam','Taif','Tabuk','Buraydah','Khobar','Abha','Yanbu','Dhahran','Jubail','Hail','Najran'],
    BR: ['São Paulo','Rio de Janeiro','Brasília','Salvador','Fortaleza','Belo Horizonte','Manaus','Curitiba','Recife','Porto Alegre','Belém','Goiânia','Guarulhos','Campinas','Natal'],
  };

  // ── Random helpers ─────────────────────────────────────────────
  function pick(arr) {
    return arr[Math.floor(Math.random() * arr.length)];
  }
  function randInt(min, max) {
    return Math.floor(Math.random() * (max - min + 1)) + min;
  }
  function randDigits(n) {
    var s = '';
    for (var i = 0; i < n; i++) s += Math.floor(Math.random() * 10).toString();
    return s;
  }
  function randDate(startYear, endYear) {
    var y = randInt(startYear, endYear);
    var m = randInt(1, 12);
    var d = randInt(1, 28);
    var mm = m < 10 ? '0' + m : '' + m;
    var dd = d < 10 ? '0' + d : '' + d;
    return { yyyy: '' + y, mm: mm, dd: dd, iso: y + '-' + mm + '-' + dd, disp: dd + '/' + mm + '/' + y };
  }
  function randAge() {
    return randInt(22, 68);
  }
  function randOccupation() {
    var occ = ['Software Engineer','Teacher','Nurse','Accountant','Sales Manager','Architect','Electrician','Marketing Specialist','Pharmacist','Mechanical Engineer','Lawyer','Chef','Graphic Designer','Logistics Coordinator','Financial Analyst','Dentist','Civil Engineer','Translator','Data Scientist','Retail Manager'];
    return pick(occ);
  }
  function randPhone(cc, national) {
    // national: e.g. "6" mobile prefix for DE -> +49 176 XXXXXXX
    return '+' + cc + ' ' + national + ' ' + randDigits(7);
  }
  function randEmail(nameParts, domain) {
    var domains = ['gmail.com','yahoo.com','outlook.com','hotmail.com','mail.com'];
    var d = domain || pick(domains);
    var first = (nameParts[0] || '').toLowerCase().replace(/[^a-z]/g, '');
    var last = (nameParts[1] || '').toLowerCase().replace(/[^a-z]/g, '');
    var sep = pick(['.', '', '_', '-']);
    var variants = [first + sep + last, first, last + sep + randDigits(2), first + '.' + last + randInt(1, 99)];
    return pick(variants) + '@' + d;
  }
  function randAddress(city) {
    var streetNames = ['Station Road','High Street','Main Street','Church Road','Mill Lane','Park Avenue','Oak Street','London Road','King Street','Victoria Road','Queen Street','Manor Road','Springfield Road','Grove Road','Elm Street'];
    var street = pick(streetNames);
    return randInt(1, 120) + ' ' + street;
  }
  function randPostcode(cc) {
    switch (cc) {
      case 'GB': return pick(['SW1A','EC1','M1','B1','LS1','NE1','EH1','CF1','BS1','G1']) + ' ' + randInt(1, 9) + (function(){ var s=''; for(var i=0;i<2;i++) s+=String.fromCharCode(65+Math.floor(Math.random()*26)); return s; })();
      case 'DE': return randDigits(5);
      case 'FR': return randDigits(5);
      case 'ES': return randDigits(5);
      case 'IT': return randDigits(5);
      case 'NL': return pick(['10','20','30','40','50','60','70','80','90','100']) + randDigits(2) + ' ' + (function(){ var s=''; for(var i=0;i<2;i++) s+=String.fromCharCode(65+Math.floor(Math.random()*26)); return s; })();
      case 'SE': return randDigits(3) + ' ' + randDigits(2);
      case 'NO': return randDigits(4);
      case 'DK': return randDigits(4);
      case 'FI': return randDigits(5);
      case 'PL': return randDigits(2) + '-' + randDigits(3);
      case 'CH': return randDigits(4);
      case 'AT': return randDigits(4);
      case 'BE': return randDigits(4);
      case 'PT': return randDigits(4) + '-' + randDigits(3);
      case 'IE': return pick(['D01','D02','D03','D04','D06','D07','D08','D09','D10','D11','D12','D13','D15','D16','D17','D18','D20','D22','D24','T12']) + ' ' + (function(){ var s=''; for(var i=0;i+2<=2;i++) s+=''; var x=''; x+=String.fromCharCode(65+Math.floor(Math.random()*26)); x+=String.fromCharCode(65+Math.floor(Math.random()*26)); x+=randInt(0,9); x+=String.fromCharCode(65+Math.floor(Math.random()*26)); x+=String.fromCharCode(65+Math.floor(Math.random()*26)); return x; })();
      case 'CZ': return randDigits(3) + ' ' + randDigits(2);
      case 'TR': return randDigits(5);
      case 'BR': return randDigits(5) + '-' + randDigits(3);
      default: return randDigits(5);
    }
  }
  function randVehicleReg(cc) {
    switch (cc) {
      case 'DE': return pick(['B','M','HH','K','S','F','D','H','N','A']) + ' ' + pick(['A','B','C','D','E','F','G','H','J','K']) + ' ' + randDigits(randInt(2,4));
      case 'GB': return pick(['A','B','C','D','E','F','G','H','J','K']) + randDigits(2) + ' ' + pick(['AA','AB','AC','AD','AE','BA','BB','BC','CA','CB']) + ' ' + randDigits(3);
      case 'FR': return pick(['AA','AB','AC','AD','BA','BB','BC','CA','CB','CC']) + '-' + randDigits(3) + '-' + randDigits(2);
      case 'ES': return randDigits(4) + ' ' + pick(['AAA','BBB','CCC','DDD','EEE','FFF','GGG','HHH','JJJ','KKK']);
      case 'IT': return pick(['AA','AB','AC','BA','BB','BC','CA','CB','CC','CD']) + randDigits(3) + pick(['A','B','C','D','E','F','G','H','J','K']) + pick(['A','B','C','D','E','F','G','H','J','K']);
      case 'NL': return randDigits(2) + '-' + randDigits(2) + '-' + randDigits(2);
      case 'SE': return pick(['A','B','C','D','E','F','G','H','J','K']) + randDigits(3) + randDigits(2);
      default: return randDigits(4) + ' ' + randDigits(3);
    }
  }

  // ── Country phone config ───────────────────────────────────────
  var PHONE = {
    DE: {cc:'49', mobile:'17', fixed:'30'}, FR:{cc:'33', mobile:'6', fixed:'1'},
    ES:{cc:'34', mobile:'6', fixed:'91'}, IT:{cc:'39', mobile:'3', fixed:'06'},
    GB:{cc:'44', mobile:'7', fixed:'20'}, NL:{cc:'31', mobile:'6', fixed:'20'},
    SE:{cc:'46', mobile:'7', fixed:'8'}, NO:{cc:'47', mobile:'9', fixed:'2'},
    DK:{cc:'45', mobile:'2', fixed:'3'}, FI:{cc:'358', mobile:'4', fixed:'9'},
    PL:{cc:'48', mobile:'5', fixed:'22'}, CH:{cc:'41', mobile:'7', fixed:'44'},
    AT:{cc:'43', mobile:'6', fixed:'1'}, BE:{cc:'32', mobile:'4', fixed:'2'},
    PT:{cc:'351', mobile:'9', fixed:'21'}, IE:{cc:'353', mobile:'8', fixed:'1'},
    GR:{cc:'30', mobile:'69', fixed:'21'}, HU:{cc:'36', mobile:'30', fixed:'1'},
    CZ:{cc:'420', mobile:'6', fixed:'2'}, HR:{cc:'385', mobile:'9', fixed:'1'},
    RO:{cc:'40', mobile:'7', fixed:'21'}, BG:{cc:'359', mobile:'8', fixed:'2'},
    IS:{cc:'354', mobile:'8', fixed:'5'}, LV:{cc:'371', mobile:'2', fixed:'6'},
    LT:{cc:'370', mobile:'6', fixed:'5'}, EE:{cc:'372', mobile:'5', fixed:'6'},
    CY:{cc:'357', mobile:'9', fixed:'22'}, LU:{cc:'352', mobile:'6', fixed:'2'},
    MT:{cc:'356', mobile:'7', fixed:'21'}, SI:{cc:'386', mobile:'4', fixed:'1'},
    SK:{cc:'421', mobile:'9', fixed:'2'}, TR:{cc:'90', mobile:'5', fixed:'21'},
    AE:{cc:'971', mobile:'5', fixed:'4'}, SA:{cc:'966', mobile:'5', fixed:'11'},
    BR:{cc:'55', mobile:'9', fixed:'11'},
  };

  // ── Document formats ───────────────────────────────────────────
  function randPassport(cc) {
    switch (cc) {
      case 'GB': return randDigits(9);
      case 'DE': return pick(['C','D','E','F','G']) + randDigits(8);
      case 'FR': return randDigits(2) + pick(['AA','AB','AC','AD','BA','BB','BC','CA','CB','CC']) + randDigits(6);
      case 'ES': return pick(['AA','AB','AC','AD','BA','BB','BC','CA','CB','CC']) + randDigits(6);
      case 'IT': return pick(['AA','AB','AC','AD','BA','BB','BC','CA','CB','CC']) + randDigits(7);
      case 'US': return randDigits(9);
      default: return randDigits(9);
    }
  }
  function randNationalID(cc) {
    switch (cc) {
      case 'DE': return randDigits(9);
      case 'FR': return randDigits(12) + randInt(0,9);
      case 'ES': return randDigits(8) + (function(){ var l='TRWAGMYFPDXBNJZSQVHLCKE'; return l[randInt(0,22)]; })();
      case 'IT': return pick(['RSS','MRT','BNC','GLL','VRD']) + randInt(1,99) + (function(){ var s=''; for(var i=0;i<3;i++) s+=String.fromCharCode(65+Math.floor(Math.random()*26)); return s; })() + randDigits(5) + pick(['A','B','C','D','E','F','G','H','J','K','L','M','N','P','Q','R','S','T','U','V','W','X','Y','Z']);
      case 'GB': return 'AB' + randDigits(6) + pick(['A','B','C','D']);
      default: return randDigits(9);
    }
  }
  function randDrivingLicence(cc) {
    switch (cc) {
      case 'DE': return pick(['B072','M672','D991','K542','S112']) + randDigits(6);
      case 'FR': return randDigits(12);
      case 'ES': return randDigits(8) + pick(['AA','AB','AC','AD','BA','BB','BC','CA','CB','CC']);
      case 'IT': return pick(['A','B','C','D','E','F','G','H','J','K','L','M','N','P','Q','R','S','T','U','V']) + randInt(1,9) + randDigits(7) + randDigits(6);
      case 'GB': return pick(['MORG','JONE','SMIT','TAYL','WILS','BROW']) + randInt(1,9) + randDigits(6) + pick(['A','B','C','D','E','F','G','H','J','K']);
      default: return randDigits(10);
    }
  }
  function randSocialSecurity(cc) {
    switch (cc) {
      case 'GB': return 'QQ' + randDigits(6) + pick(['A','B','C','D']);
      case 'FR': return randDigits(2) + randInt(1,2) + randDigits(2) + randDigits(2) + randDigits(3) + randDigits(3) + randDigits(2);
      case 'DE': return randDigits(11);
      default: return randDigits(9);
    }
  }

  // ── Nationality names ──────────────────────────────────────────
  function nationalityName(cc) {
    var n = {
      DE:'German', FR:'French', ES:'Spanish', IT:'Italian', GB:'British', NL:'Dutch',
      SE:'Swedish', NO:'Norwegian', DK:'Danish', FI:'Finnish', PL:'Polish', CH:'Swiss',
      AT:'Austrian', BE:'Belgian', PT:'Portuguese', IE:'Irish', GR:'Greek', HU:'Hungarian',
      CZ:'Czech', HR:'Croatian', RO:'Romanian', BG:'Bulgarian', IS:'Icelandic', LV:'Latvian',
      LT:'Lithuanian', EE:'Estonian', CY:'Cypriot', LU:'Luxembourgish', MT:'Maltese',
      SI:'Slovenian', SK:'Slovak', TR:'Turkish', AE:'Emirati', SA:'Saudi', BR:'Brazilian'
    };
    return n[cc] || 'European';
  }

  // ── Main generator ─────────────────────────────────────────────
  function generateDataset(countryCode, ibanRaw, banksForCountry) {
    var cc = countryCode;
    var locale = LOCALES[cc] || LOCALES.DE;
    var fullName = pick(locale.first) + ' ' + pick(locale.last);
    var nameParts = fullName.split(' ');
    var dob = randDate(1958, 2004);
    var age = 2026 - parseInt(dob.yyyy, 10);

    var city = (CITIES[cc] && pick(CITIES[cc])) || 'City';
    var address = randAddress(city);
    var postcode = randPostcode(cc);
    var phone = randPhone(PHONE[cc].cc, PHONE[cc].mobile);
    var email = randEmail(nameParts);
    var occupation = randOccupation();

    // Bank from swift_codes.json if available
    var bank = null;
    if (banksForCountry && banksForCountry.length) {
      bank = pick(banksForCountry);
    }

    var fmtIban = IBAN.format(ibanRaw);
    var bic = bank ? bank.bic : null;
    var bankName = bank ? bank.bankName : null;
    var bankCity = bank ? bank.city : null;
    var bankUrl = bankName ? 'https://' + bankName.toLowerCase().replace(/[^a-z0-9]+/g,'') + '.example.com' : null;

    return {
      iban: fmtIban,
      ibanRaw: ibanRaw,
      swiftBic: bic,
      valid: true,

      identity: {
        fullName: fullName,
        dob: dob.disp,
        age: age,
        country: nationalityName(cc),
        city: city,
        address: address,
        postcode: postcode,
        phone: phone,
        email: email,
        occupation: occupation,
      },

      documents: {
        passport: randPassport(cc),
        nationalId: randNationalID(cc),
        drivingLicence: randDrivingLicence(cc),
        vehicleReg: randVehicleReg(cc),
        socialSecurity: randSocialSecurity(cc),
      },

      bank: {
        bankName: bankName,
        bankBic: bic,
        bankCity: bankCity,
        bankUrl: bankUrl,
        accountType: 'Personal Current Account',
      },
    };
  }

  // ── Load banks from swift_codes.json ──────────────────────────
  function loadBanks(callback) {
    if (BANKS_LOADED) { callback(); return; }
    var xhr = new XMLHttpRequest();
    xhr.open('GET', '/swift_codes.json', true);
    xhr.onload = function() {
      if (xhr.status === 200) {
        try {
          var data = JSON.parse(xhr.responseText);
          BANKS = {};
          for (var i = 0; i < data.length; i++) {
            var b = data[i];
            if (!BANKS[b.country]) BANKS[b.country] = [];
            BANKS[b.country].push(b);
          }
          BANKS_LOADED = true;
        } catch(e) {}
      }
      callback();
    };
    xhr.onerror = function() { callback(); };
    xhr.send();
  }

  function getBanks(countryCode) {
    return BANKS[countryCode] || null;
  }

  // ── Public API ─────────────────────────────────────────────────
  window.Dataset = {
    generate: generateDataset,
    loadBanks: loadBanks,
    getBanks: getBanks,
    isLoaded: function() { return BANKS_LOADED; },
    randInt: randInt
  };
})();
