import paho.mqtt.client as mqtt
import pymysql
from datetime import datetime
import os

broker = "test.mosquitto.org"
topic = "IUT/Colmar2024/SAE2.04/Maison1"
port = 1883

db_host = "10.252.7.133"
db_user = "toto"
db_password = "toto"
db_name = "test21"
backup_file = os.path.expanduser("C:\\Users\\khali\\Desktop\\Cours\\Cours\\SAE 24\\backup.txt")

def connect_db():
    try:
        db = pymysql.connect(
            host=db_host,
            user=db_user,
            password=db_password,
            database=db_name
        )
        cursor = db.cursor()
        return db, cursor
    except pymysql.Error as e:
        print(f"Erreur de connexion à la base de données : {e}")
        return None, None

db, cursor = connect_db()

sensors = {}


def on_connect(client, userdata, flags, rc):
    print("Connecté avec le code de retour: " + str(rc))
    client.subscribe(topic)


def on_message(client, userdata, msg):
    message = msg.payload.decode('utf-8')
    print(f"Message reçu sur le topic {msg.topic}: {message}")
    process_message(message)


def process_message(message):
    data = {}
    for item in message.split(','):
        key, value = item.split('=')
        data[key.strip()] = value.strip()

    sensor_id = data['Id']
    piece = data['piece']
    timestamp = datetime.strptime(f"{data['date']} {data['time']}", "%d/%m/%Y %H:%M:%S")
    value = float(data['temp'])


    if sensor_id not in sensors:
        sensors[sensor_id] = {
            'nom': sensor_id,
            'piece': piece,
            'emplacement': ''
        }

    if db is not None and cursor is not None:
        try:
            cursor.execute("SELECT nom FROM myapp_capteur WHERE nom = %s AND piece = %s", (sensor_id, piece))
            existing_sensor = cursor.fetchone()

            if existing_sensor:
                print(f"Capteur {sensor_id} pour la pièce {piece} existe déjà dans la base de données.")
            else:
                cursor.execute("INSERT INTO myapp_capteur (nom, piece, emplacement) VALUES (%s, %s, %s)",
                               (sensor_id, piece, ''))
                db.commit()
                print(f"Capteur {sensor_id} inséré dans la base de données pour la pièce {piece}")

            cursor.execute(
                "INSERT INTO myapp_donnee (capteur_id, timestamp, temperature) VALUES (%s, %s, %s)",
                (sensor_id, timestamp, value))
            db.commit()
            print("Données insérées avec succès")

        except pymysql.Error as e:
            print(f"Erreur lors de l'insertion ou vérification du capteur/données : {e}")
            try:
                db.rollback()
            except pymysql.err.InterfaceError:
                print("La connexion à la base de données a été perdue. Sauvegarde des données dans le fichier.")
            backup_data(sensor_id, piece, timestamp, value)
    else:
        backup_data(sensor_id, piece, timestamp, value)

def backup_data(sensor_id, piece, timestamp, value):
    with open(backup_file, 'a') as f:
        f.write(f"{sensor_id},{piece},{timestamp},{value}\n")
    print(f"Données sauvegardées dans le fichier : {backup_file}")


client = mqtt.Client()
client.on_connect = on_connect
client.on_message = on_message
client.connect(broker, port, 60)


try:
    print("Démarrage de la boucle MQTT. Appuyez sur Ctrl+C pour arrêter.")
    client.loop_forever()
except KeyboardInterrupt:
    print("Interruption par l'utilisateur. Arrêt du programme.")
    client.disconnect()
    if cursor:
        cursor.close()
    if db:
        db.close()
