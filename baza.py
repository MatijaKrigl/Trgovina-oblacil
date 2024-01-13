import csv
import sqlite3
from sqlite3 import IntegrityError

PARAM_FMT = ":{}" # za SQLite
# PARAM_FMT = "%s({})" # za PostgreSQL/MySQL

class Tabela:
    """
    Razred, ki predstavlja tabelo v bazi.

    Polja razreda:
    - ime: ime tabele
    - podatki: ime datoteke s podatki ali None
    """
    ime = None
    podatki = None

    def __init__(self, conn):
        """
        Konstruktor razreda.
        """
        self.conn = conn

    def ustvari(self):
        """
        Metoda za ustvarjanje tabele.
        Podrazredi morajo povoziti to metodo.
        """
        raise NotImplementedError

    def izbrisi(self):
        """
        Metoda za brisanje tabele.
        """
        self.conn.execute(f"DROP TABLE IF EXISTS {self.ime};")

    def uvozi(self, encoding="UTF-8"):
        """
        Metoda za uvoz podatkov.

        Argumenti:
        - encoding: kodiranje znakov
        """
        if self.podatki is None:
            return
        with open(self.podatki, encoding=encoding) as datoteka:
            podatki = csv.reader(datoteka)
            stolpci = next(podatki)
            for vrstica in podatki:
                vrstica = {k: None if v == "" else v for k, v in zip(stolpci, vrstica)}
                self.dodaj_vrstico(**vrstica)

    def izprazni(self):
        """
        Metoda za praznjenje tabele.
        """
        self.conn.execute(f"DELETE FROM {self.ime};")

    def dodajanje(self, stolpci=None):
        """
        Metoda za gradnjo poizvedbe.

        Argumenti:
        - stolpci: seznam stolpcev
        """
        return f"""
            INSERT INTO {self.ime} ({", ".join(stolpci)})
            VALUES ({", ".join(PARAM_FMT.format(s) for s in stolpci)});
        """

    def dodaj_vrstico(self, **podatki):
        """
        Metoda za dodajanje vrstice.

        Argumenti:
        - poimenovani parametri: vrednosti v ustreznih stolpcih
        """
        podatki = {kljuc: vrednost for kljuc, vrednost in podatki.items()
                   if vrednost is not None}
        poizvedba = self.dodajanje(podatki.keys())
        cur = self.conn.execute(poizvedba, podatki)
        return cur.lastrowid

class Stranka(Tabela):
    """
    Tabela za stranke.
    """
    ime = "stranka"
    podatki = "podatki/stranka.csv"

    def ustvari(self):
        """
        Ustvari tabelo stranka.
        """
        self.conn.execute("""
            CREATE TABLE stranka (
                id          INTEGER PRIMARY KEY AUTOINCREMENT,
                first_name   TEXT NOT NULL,
                last_name   TEXT NOT NULL,
                email       TEXT NOT NULL,
                gender      TEXT NOT NULL,
                ip_address  TEXT NOT NULL
            );
        """)

class Oblacila(Tabela):
    """
    Tabela za oblacila.
    """
    ime = "oblacilo"
    podatki = "podatki/oblacila.csv"

    def ustvari(self):
        """
        Ustvari tabelo oblačilo.
        """
        self.conn.execute("""
            CREATE TABLE oblacilo (
                clothing_type     TEXT NOT NULL,
                size              TEXT NOT NULL,
                color             TEXT NOT NULL,
                brand             TEXT NOT NULL,
                material          TEXT NOT NULL,
                price             INTEGER NOT NULL,
                season            TEXT NOT NULL,
                ID        TEXT PRIMARY KEY
            );
        """)

class Zaloga(Tabela):
    """
    Tabela za dobavo in zalogo.
    """
    ime = "zaloga"
    podatki = "podatki/zaloga.csv"

    def ustvari(self):
        """
        Ustvari tabelo zaloga oz. dobava.
        """
        self.conn.execute("""
            CREATE TABLE zaloga (
                id_dobave            TEXT PRIMARY KEY,
                id_izdelka           TEXT REFERENCES oblacila(ID),
                price                REAL NOT NULL,
                quantity             INTEGER NOT NULL,
                date_of_launch       DATE
            );
        """)

class Kosarica(Tabela):
    """
    Tabela za košarico.
    """
    ime = "kosarica"
    podatki = "podatki/kosarica.csv"

    def ustvari(self):
        """
        Ustvari tabelo kosarica.
        """
        self.conn.execute("""
            CREATE TABLE kosarica (
                cart_id        INTEGER PRIMARY KEY AUTOINCREMENT,
                product_id          TEXT REFERENCES oblacila(ID),
                discount           REAL
            );
        """)

class Narocilo(Tabela):
    """
    Tabela za naročilo.
    """
    ime = "narocilo"
    podatki = "podatki/narocilo.csv"

    def ustvari(self):
        """
        Ustvari tabelo narocilo.
        """
        self.conn.execute("""
            CREATE TABLE narocilo (
                id_kosarice      TEXT REFERENCES kosarica(id_kosarice),
                ID               TEXT REFERENCES stranka(id),
                status           BOOLEAN,
                status_2         BOOLEAN
            )
        """)


def ustvari_tabele(tabele):
    """
    Ustvari podane tabele.
    """
    for t in tabele:
        t.ustvari()

def izbrisi_tabele(tabele):
    """
    Izbriši podane tabele.
    """
    for t in tabele:
        t.izbrisi()


def uvozi_podatke(tabele):
    """
    Uvozi podatke v podane tabele.
    """
    for t in tabele:
        print("uvozi v tabelo", t.ime)
        t.uvozi()


def izprazni_tabele(tabele):
    """
    Izprazni podane tabele.
    """
    for t in tabele:
        t.izprazni()


def ustvari_bazo(conn):
    """
    Izvede ustvarjanje baze.
    """
    tabele = pripravi_tabele(conn)
    izbrisi_tabele(tabele)
    ustvari_tabele(tabele)
    uvozi_podatke(tabele)


def pripravi_tabele(conn):
    """
    Pripravi objekte za tabele.
    """
    stranka = Stranka(conn)
    oblacilo = Oblacila(conn)
    zaloga = Zaloga(conn)
    kosarica = Kosarica(conn)
    narocilo = Narocilo(conn)
    return [stranka, oblacilo, zaloga, kosarica, narocilo]


def ustvari_bazo_ce_ne_obstaja(conn):
    """
    Ustvari bazo, če ta še ne obstaja.
    """
    with conn:
        cur = conn.execute("SELECT COUNT(*) FROM sqlite_master")
        # if cur.fetchone() == (0, ):
        ustvari_bazo(conn)

BAZA = 'oblacila.db'
conn = sqlite3.connect(BAZA)
ustvari_bazo_ce_ne_obstaja(conn)
conn.execute("SELECT * FROM stranka")
conn.execute("SELECT * FROM oblacilo")
conn.execute("SELECT * FROM zaloga")
conn.execute("SELECT * FROM kosarica")
conn.execute("SELECT * FROM narocilo")


conn.close()
# conn.execute('PRAGMA foreign_keys = ON') #delovanje tujih kljucev