import socket
import os
import time


def check_db_connection():
    host = os.getenv("DB_HOST", "127.0.0.1")
    port = int(os.getenv("DB_PORT", 3306))
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        while True:
            try:
                conn = s.connect((host, port))
                if conn is None:
                    print("Success to connect to db...")
                    break
            except socket.error:
                print("Fail to connect to db...")
                time.sleep(1)


if __name__ == "__main__":
    check_db_connection()