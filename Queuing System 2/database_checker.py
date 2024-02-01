# database_checker.py
import mysql.connector
import schedule
import time

host = "localhost"
user = "root"
password = "Q@5mk8wK"
database = "dba"
port = 3307

def license_data():
    try:
        connection = mysql.connector.connect(
            host=host,
            user=user,
            password=password,
            database=database,
            port=port
        )

        if connection.is_connected():
            print("Connected to the database")

            # Fetch licenses that will expire in 2 weeks or less
            cursor = connection.cursor()
            query = "SELECT C_email, idclients, Expiry_date FROM clients WHERE Expiry_date <= (NOW() + INTERVAL 2 WEEK)"
            cursor.execute(query)
            results = cursor.fetchall()

            license_data = []  # Store the license data to be processed in the second file

            for C_email, idclients, expiry_date in results:
                license_data.append((C_email, idclients, expiry_date))

            # Process the license data and send notifications
            process_license_data(license_data)

    except mysql.connector.Error as err:
        print(f"MySQL Error: {err}")

    finally:
        if 'connection' in locals() and connection.is_connected():
            connection.close()
            print("Connection closed")

def process_license_data(license_data):
    # Process license data and send notifications
    for C_email, idclients, expiry_date in license_data:
        print(f"Processing license data for {C_email}, ID: {idclients}, Expiry Date: {expiry_date}")

if __name__ == "__main__":
    # Schedule the check_database function to run every Thursday at 12:41
    schedule.every().thursday.at("12:48").do(license_data())

    # Keep the script running to allow the scheduler to work
    while True:
        schedule.run_pending()
        time.sleep(1)
