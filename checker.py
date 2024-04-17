import mysql.connector
import configparser
import pika
import schedule
import time


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
def check_database():
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
                query = f"SELECT email, license_number, license_type, expires_at, language FROM {table_name.strip()} WHERE expires_at <= (NOW() + INTERVAL 2 WEEK)"
                cursor.execute(query)
                results = cursor.fetchall()
                for email, license_number, license_type, expires_at, language in results:
                    license_data.append((email, license_number, license_type, expires_at, language))

            return license_data

    except mysql.connector.Error as err:
        print(f"MySQL Error: {err}")

    finally:
        if 'connection' in locals() and connection.is_connected():
            cursor.close()  # Close the cursor
            connection.close()
            print("Connection closed")


# Initialize RabbitMQ connection parameters
rabbitmq_host = config['RabbitMQ']['host']
rabbitmq_port = int(config['RabbitMQ']['port'])
rabbitmq_username = config['RabbitMQ']['username']
rabbitmq_password = config['RabbitMQ']['password']
rabbitmq_queue_name = config['RabbitMQ']['queue_name']


def send_to_queue(data):
    connection = None  # Initialize connection variable
    try:
        connection = pika.BlockingConnection(pika.ConnectionParameters(host=rabbitmq_host, port=rabbitmq_port,
                                                                       virtual_host='/',
                                                                       credentials=pika.PlainCredentials(
                                                                           rabbitmq_username, rabbitmq_password)))
        channel = connection.channel()
        channel.queue_declare(queue=rabbitmq_queue_name, durable=True)

        # Publish each license data as a message to the queue
        for item in data:
            channel.basic_publish(exchange='', routing_key=rabbitmq_queue_name, body=str(item))
            print(f" [x] Sent {item} to RabbitMQ")

    except Exception as e:
        print(f"Error sending data to RabbitMQ: {e}")

    finally:
        if connection is not None:
            connection.close()

def process_license_expiry():

    license_data = check_database()


    if license_data:
        send_to_queue(license_data)


schedule.every().tuesday.at("11:12").do(process_license_expiry)

while True:
    schedule.run_pending()
    time.sleep(1)
