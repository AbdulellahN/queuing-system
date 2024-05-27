import mysql.connector
import configparser
import pika
import schedule
import time
from datetime import datetime, timedelta

def read_config(configini):
    config = configparser.ConfigParser()
    config.read(configini)
    return config

config = read_config('config.ini')

db_host = config['Database']['db_host']
db_user = config['Database']['db_user']
db_password = config['Database']['db_password']
db_database = config['Database']['db_database']
db_port = int(config['Database']['db_port'])

def check_database(custom_interval_days=14):
    try:
        connection = mysql.connector.connect(
            host=db_host,
            user=db_user,
            password=db_password,
            database=db_database,
            port=db_port
        )

        if connection.is_connected():
            print("Connected to the database")

            cursor = connection.cursor()
            table_names = config.get('Database', 'table_names').split(',')
            license_data = []

            for table_name in table_names:
                query = f"SELECT email, license_number, license_type, expires_at, language FROM {table_name.strip()} " \
                        f"WHERE expires_at <= (NOW() + INTERVAL {custom_interval_days} DAY)"
                
                cursor.execute(query)
                results = cursor.fetchall()
                
                for email, license_number, license_type, expires_at, language in results:
                    license_data.append((email, license_number, license_type, expires_at, language))

            return license_data

    except mysql.connector.Error as err:
        print(f"MySQL Error: {err}")

    finally:
        if 'connection' in locals() and connection.is_connected():
            cursor.close()
            connection.close()
            print("Connection closed")

def send_to_queue(data):
    try:
        connection = pika.BlockingConnection(pika.ConnectionParameters(host=config['RabbitMQ']['host'],
                                                                       port=int(config['RabbitMQ']['port']),
                                                                       virtual_host='/',
                                                                       credentials=pika.PlainCredentials(
                                                                           config['RabbitMQ']['username'],
                                                                           config['RabbitMQ']['password'])))
        channel = connection.channel()
        channel.queue_declare(queue=config['RabbitMQ']['queue_name'], durable=True)

        for item in data:
            channel.basic_publish(exchange='', routing_key=config['RabbitMQ']['queue_name'], body=str(item))
            print(f" [x] Sent {item} to RabbitMQ")

    except Exception as e:
        print(f"Error sending data to RabbitMQ: {e}")

def process_license_expiry():
    license_data = check_database()
    if license_data:
        send_to_queue(license_data)

# Schedule tasks
schedule.every(3).seconds.do(process_license_expiry)

# Main loop to run the scheduler
while True:
    schedule.run_pending()
    time.sleep(1)
