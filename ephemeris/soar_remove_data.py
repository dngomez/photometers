import mysql.connector

# Database connection
cnx = mysql.connector.connect(user='photometers', password='photometers_sql', host='localhost', database='photometers')
cursor = cnx.cursor()

cursor.execute("DELETE FROM `soar_ephemeris` WHERE `time` < (curdate() - INTERVAL 14 DAY)")
cnx.commit()
cnx.close()