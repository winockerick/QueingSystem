import tkinter as tk
from tkinter import ttk
from PIL import Image, ImageTk
import os
import pygame
import cv2
import requests
import mysql.connector
import socket
import threading

# Connect to the MySQL database
db = mysql.connector.connect(
    host="localhost",
    user="root",
    password="",
    database="trial"
)

cursor = db.cursor()  # Create a cursor object to interact with the database

def get_next_token():
    cursor.execute("SELECT MAX(token_number) FROM tokens")
    result = cursor.fetchone()
    next_token = (result[0] or 0) + 1
    return next_token

def update_counter(counter_id, token_number):
    cursor.execute("UPDATE counters SET current_token = %s WHERE id = %s", (token_number, counter_id))
    db.commit()

def insert_token(token_number):
    cursor.execute("INSERT INTO tokens (token_number) VALUES (%s)", (token_number,))
    db.commit()

def handle_next_button(counter_id):
    next_token = get_next_token()
    insert_token(next_token)
    update_counter(counter_id, next_token)
    token_number_labels[counter_id - 1].config(text=str(next_token))
    print(f"Counter {counter_id} now serving token {next_token}")

def mark_as_returned(counter_id):
    cursor.execute("SELECT current_token FROM counters WHERE id = %s", (counter_id,))
    result = cursor.fetchone()

    if result and result[0]:
        return_token(result[0])
        reset_counter(counter_id)
    else:
        print("no token is currently being served at this counter")

def return_token(token_number):
    cursor.execute("INSERT INTO returned_tokens(token_number) VALUES (%s)", (token_number,))
    db.commit()
    print(f"Token {token_number} has been marked as returned.")

def serve_returned_token(counter_id):
    cursor.execute("SELECT token_number FROM returned_tokens ORDER BY id LIMIT 1")
    result = cursor.fetchone()

    if result:
        returned_token = result[0]
        update_counter(counter_id, returned_token)
        token_number_labels[counter_id - 1].config(text=str(returned_token))
        cursor.execute("DELETE FROM returned_tokens ORDER BY id LIMIT 1")
        db.commit()
        print(f"Counter {counter_id} is now serving returned token {returned_token}")
    else:
        print("No returned tokens to serve.")

def reset_database():
    cursor.execute("TRUNCATE TABLE tokens")
    cursor.execute("TRUNCATE TABLE counters")
    db.commit()
    print("Database has been reset.")

def reset_counter(counter_id):
    cursor.execute("UPDATE counters SET current_token = NULL WHERE id = %s", (counter_id,))
    db.commit()
    token_number_labels[counter_id - 1].config(text="")
    print(f"Counter {counter_id} has been reset.")

def udp_listener():
    # Set up the socket to listen on the specified IP and port
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    esp32_ip = "0.0.0.0"  # Replace with the IP address of the ESP32
    port = 12345  # Replace with the port number you're using

    try:
        # Bind the socket to the specified IP and port
        sock.bind((esp32_ip, port))
        print(f"UDP Listener started on {esp32_ip}:{port}.")
    except Exception as e:
        print(f"Failed to bind the socket: {e}")
        return

    while True:
        try:
            # Receive data from the socket
            data, _ = sock.recvfrom(1024)

            # Ensure we have at least 2 bytes (1 for counterId, 1 for customKey)
            if len(data) >= 2:
                counterId = data[0]  # First byte is the counterId
                key = chr(data[1])  # Second byte is the customKey (convert to character)

                # Print the received data for debugging
                print(f"Received data from counter: {counterId}, key: {key}")

                # Call a function to handle the key and counterId
                handle_udp_key(key, counterId)
            else:
                print("Incomplete data received")

        except Exception as e:
            print(f"UDP Listener error: {e}")

def handle_udp_key(key, counterId):
    if key == 'D':
        handle_next_button(counterId)
    elif key == '1':
        reset_counter(counterId)
    elif key == '2':
        reset_database()
    elif key == 'C':  # Serve the returned token
        serve_returned_token(counterId)
    elif key == 'B':  # Mark the current token as returned
        mark_as_returned(counterId)

pygame.init()
# Create the main window
root = tk.Tk()
root.title("Queue Management System")
root.attributes('-fullscreen', False)
root.configure(bg='white')
# Get screen width and height
screen_width = root.winfo_screenwidth()
screen_height = root.winfo_screenheight()

# Customer message frame
customer_message_width = int(screen_width * 0.98)
customer_message_padding = 0
customer_message = tk.Frame(root, width=customer_message_width, height=int(screen_height))
customer_message.place(x=customer_message_padding, y=int(screen_height * 0.93))

message_label = tk.Label(customer_message, text="  DEAR CUSTOMER, WE ARE PLEASED TO SERVE YOU. KINDLY SIT AND WAIT WHILE WE ARE SERVING OTHER CUSTOMERS  ",
                         font=("Poppins", int(screen_height * 0.022), "bold"), bg="white", justify="center")
message_label.pack(fill=tk.BOTH, expand=True)

# Counter frames
num_counters = 4
counter_frame_width = int(screen_width * 0.1)
counter_frame_height = int(screen_height * 0.1)
counter_spacing = int(screen_width * 0.03)
counter_x_start = screen_width - counter_frame_width * 1.1
counter_y = 0

token_number_labels = []

def create_counter_frame(counter_id):
    counter_frame = tk.Frame(root, width=counter_frame_width, height=counter_frame_height, bg="dark blue")
    counter_frame.place(x=counter_x_start - (counter_id - 1) * (counter_frame_width + counter_spacing), y=counter_y + 50)

    counter_label = tk.Label(counter_frame, text=f"Counter\n{num_counters - (counter_id - 1)}",
                             font=("calibri", int(screen_height * 0.03), "bold"), fg="white", bg="dark blue")
    counter_label.pack(fill=tk.BOTH, expand=True)
    counter_label.place(relx=0.5, rely=0.5, anchor=tk.CENTER)

    now_serving_frame = tk.Frame(root, width=counter_frame_width, height=int(counter_frame_height / 2), bg="dark blue")
    now_serving_frame.place(x=counter_x_start - (counter_id - 1) * (counter_frame_width + counter_spacing), y=counter_y + counter_frame_height + 65)

    now_serving_label = tk.Label(now_serving_frame, text="NOW SERVING", fg="white", font=("Arial", int(screen_height * 0.019), "bold"), bg="dark blue")
    now_serving_label.pack(fill=tk.BOTH, expand=True)

    token_frame = tk.Frame(root, width=counter_frame_width, height=int(counter_frame_height * 1.5), bg="light grey")
    token_frame.place(x=counter_x_start - (counter_id - 1) * (counter_frame_width + counter_spacing), y=counter_y + counter_frame_height * 2.5)



    token_number_label = tk.Label(token_frame, text="", font=("calibri", int(screen_height * 0.07), "bold"), fg="black")
    token_number_label.pack(fill=tk.BOTH, expand=True)
    token_number_label.place(relx=0.5, rely=0.5, anchor=tk.CENTER)



    next_button = tk.Button(root, text="Next", command=lambda: handle_next_button(counter_id))

    # next_button.place(x=counter_x_start - (counter_id - 1) * (counter_frame_width + counter_spacing), y=counter_y + counter_frame_height * 4)


    reset_button = tk.Button(root, text=f"Reset Counter {counter_id}", command=lambda: reset_counter(counter_id), font=("Arial", int(screen_height * 0.02), "bold"), bg="orange", fg="white")
    #reset_button.place(x=counter_x_start - (counter_id - 1) * (counter_frame_width + counter_spacing), y=counter_y + counter_frame_height * 1.5 + int(counter_frame_height * 1.5), width=counter_frame_width, height=int(screen_height * 0.05))



    token_number_labels.append(token_number_label)



    for i in range(1, num_counters + 1):

     create_counter_frame(i)



    currency_frame_width = int(screen_width )

    currency_frame_height = int(screen_height * 0.48)

    currency_frame = tk.Frame(root, width=currency_frame_width, height=currency_frame_height, bg="white")

    currency_frame.place(x=0, y=screen_height * 0.45)



    column_width = currency_frame_width // 3



    currency_label = tk.Label(currency_frame, text="CURRENCY", bg="dark blue", font=("Arial", int(screen_height * 0.03), "bold"), fg="white")

    currency_label.place(x=0, y=0, width=column_width)



    buy_label = tk.Label(currency_frame, text="BUY", bg="dark blue", font=("Arial", int(screen_height * 0.03), "bold"), fg="white")

    buy_label.place(x=column_width, y=0, width=column_width)



    sell_label = tk.Label(currency_frame, text="SELL", bg="dark blue", font=("Arial", int(screen_height * 0.03), "bold"), fg="white")

    sell_label.place(x=2 * column_width, y=0, width=column_width)



    currencies = ['USD', 'EUR', 'GBP', 'JPY', 'CAD', 'CNY', 'CHF', 'AUD']

    currency_labels = []
    for i, currency in enumerate(currencies):

      label = tk.Label(currency_frame, text=currency, bg="dark blue", font=("Arial", int(screen_height * 0.031)) , fg="white")

      label.place(x=0, y=int(screen_height * 0.055) * (i+1), width=column_width)

      currency_labels.append(label)



      buy_labels = []

    for i in range(len(currencies)):

     label = tk.Label(currency_frame, text="", bg="dark blue", font=("Arial", int(screen_height * 0.031)), fg="white")

     label.place(x=column_width, y=int(screen_height * 0.055) * (i+1), width=column_width)

     buy_labels.append(label)



sell_labels = []

for i in range(len(currencies)):

 label = tk.Label(currency_frame, text="", bg="dark blue", font=("Arial", int(screen_height * 0.031)),  fg="white")

 label.place(x=2 * column_width, y=int(screen_height * 0.055) * (i+1), width=column_width)

 sell_labels.append(label)



reset_db_button = tk.Button(root, text="Reset Database", command=reset_database, font=("Arial", int(screen_height * 0.02), "bold"), bg="red", fg="white")

#reset_db_button.place(x=int(screen_width * 0.05), y=int(screen_height * 0.92), width=int(screen_width * 0.15), height=int(screen_height * 0.05))



# Start the UDP listener in a separate thread

udp_thread = threading.Thread(target=udp_listener, daemon=True)

udp_thread.start()



# Start the main event loop

root.mainloop()