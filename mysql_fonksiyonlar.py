import mysql.connector

mysql_baglanti = mysql.connector.connect(
    host = "localhost",
    user = "root",
    password = "",
    database = "orpheus"
)

def select(sorgu):
    imlec = mysql_baglanti.cursor()
    imlec.execute(sorgu)
    # sorgu sonucu gelen kayıtlar
    kayitlar = imlec.fetchall()
    return kayitlar

def insert(sorgu):
    imlec = mysql_baglanti.cursor()
    imlec.execute(sorgu)
    mysql_baglanti.commit()

def delete(sorgu):
    imlec = mysql_baglanti.cursor()
    imlec.execute(sorgu)
    mysql_baglanti.commit()

def update(sorgu):
    imlec = mysql_baglanti.cursor()
    imlec.execute(sorgu)
    mysql_baglanti.commit()


