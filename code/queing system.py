import tkinter as tk
from tkinter import ttk
import firebase_admin
from firebase_admin import credentials, db
import threading
import socket
from PIL import Image, ImageTk
import os
import pygame
import cv2
import requests
import time 

# Add a global dictionary to track last event time for each counter
last_event_time = {}
DEBOUNCE_DELAY = 0.5  # 500 milliseconds

# Initialize Firebase
cred = credentials.Certificate(r"D:\aluta\FYP\code\beqs-651fc-firebase-adminsdk-fbsvc-f3a854902a.json")  # Replace with your Firebase service account key
firebase_admin.initialize_app(cred, {
    'databaseURL': 'https://beqs-651fc-default-rtdb.firebaseio.com/'  # Replace with your Firebase Realtime Database URL
})

# Firebase Database References
counters_ref = db.reference('counters')
tokens_ref = db.reference('tokens')
returned_tokens_ref = db.reference('returned_tokens')

def update_token_labels():
    def on_counter_change(event):
        counter_data = event.data
        if counter_data:
            for counter_id, data in counter_data.items():
                # Check if data is a dictionary and has 'token' key
                if isinstance(data, dict) and data.get('token') is not None:
                    counter_index = int(counter_id.split('counter')[1]) - 1
                    token_number_labels[counter_index].config(text=str(data['token']))
    
    counters_ref.listen(on_counter_change)

# Call this function before root.mainloop()
update_token_labels()

# Function to get the next token number
def get_next_token():
    tokens = tokens_ref.get()
    if tokens:
        last_token = max(int(token_id) for token_id in tokens.keys())
        return last_token + 1
    return 101  # Starting token number

# Function to insert a new token
def insert_token(token_number):
    tokens_ref.child(str(token_number)).set({
        'status': 'waiting',
        'assigned_counter': None
    })

# Function to update a counter with a new token
def update_counter(counter_id, token_number):
    counters_ref.child(counter_id).update({
        'token': token_number,
        'status': 'serving'
    })
    tokens_ref.child(str(token_number)).update({
        'assigned_counter': counter_id
    })
    # Schedule label update in main thread
    root.after(0, lambda: update_token_label(counter_id, token_number))
def update_token_label(counter_id, token_number):
    counter_index = int(counter_id.split('counter')[1]) -1
    token_number_labels[counter_index].config(text=str(token_number))

# Function to reset a counter
def reset_counter(counter_id):
    counters_ref.child(counter_id).update({
        'token': None,
        'status': 'waiting'
    })
    print(f"Counter {counter_id} has been reset.")
    
    # Clear the token number label in the GUI
    counter_index = int(counter_id[-1]) - 1  # Extract counter number (e.g., "counter1" -> 0)
    token_number_labels[counter_index].config(text="")
    
# Function to reset the entire database
def reset_database():
    counters_ref.set({
        'counter1': {'token': None, 'status': 'waiting'},
        'counter2': {'token': None, 'status': 'waiting'}
    })
    tokens_ref.set({})
    returned_tokens_ref.set({})

# Function to handle the "Next" button click
def handle_next_button(counter_id):
    next_token = get_next_token()
    insert_token(next_token)
    update_counter(counter_id, next_token)
    print(f"Counter {counter_id} now serving token {next_token}")

# Function to mark a token as returned
def mark_as_returned(counter_id):
    counter_data = counters_ref.child(counter_id).get()
    if counter_data and counter_data['token']:
        token_number = counter_data['token']
        returned_tokens_ref.child(str(token_number)).set({
            'status': 'returned'
        })
        tokens_ref.child(str(token_number)).update({
            'status': 'returned'
        })
        reset_counter(counter_id)
        print(f"Token {token_number} marked as returned")

# Function to serve a returned token
def serve_returned_token(counter_id):
    returned_tokens = returned_tokens_ref.get()
    if returned_tokens:
        for token_number in returned_tokens.keys():
            token_data = tokens_ref.child(token_number).get()
            if token_data and token_data['status'] == 'returned':
                update_counter(counter_id, int(token_number))
                returned_tokens_ref.child(token_number).delete()
                print(f"Counter {counter_id} serving returned token {token_number}")
                break

# UDP Listener for ESP32 communication
def udp_listener():
    # Set up the socket to listen on the specified IP and port
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    esp32_ip = "0.0.0.0"  # Listen on all available interfaces
    port = 12345  # Replace with the port number you're using
    sock.bind((esp32_ip, port))
    print(f"UDP Listener started on {esp32_ip}:{port}.")

    while True:
        try:
            # Receive data from the socket
            data, _ = sock.recvfrom(1024)

            if len(data) >= 2:
                counter_id = f"counter{data[0]}"  # First byte is the counter ID
                key = chr(data[1])  # Second byte is the custom key
                current_time = time.time()

                # Check if enough time has passed since last event for this counter
                if (counter_id not in last_event_time or 
                    current_time - last_event_time.get(counter_id, 0) > DEBOUNCE_DELAY):
                    
                    print(f"Received data from counter: {counter_id}, key: {key}")
                    last_event_time[counter_id] = current_time  # Update last event time for this counter

                    # Handle the key press based on the received key
                    if key == 'D':  # Next token
                        handle_next_button(counter_id)
                    elif key == '1':  # Reset counter
                        reset_counter(counter_id)
                    elif key == '2':  # Reset database
                        reset_database()
                    elif key == 'C':  # Serve returned token
                        serve_returned_token(counter_id)
                    elif key == 'B':  # Mark token as returned
                        mark_as_returned(counter_id)
                else:
                    print(f"Ignoring duplicate event from {counter_id} due to debounce.")
            else:
                print("Incomplete data received")

        except Exception as e:
            print(f"UDP Listener error: {e}")
# GUI Setup (unchanged)
root = tk.Tk()
root.title("Queue Management System")
root.attributes('-fullscreen', False)
root.configure(bg='white')

# Get screen width and height
screen_width = root.winfo_screenwidth()
screen_height = root.winfo_screenheight()

# Define frame styles
frame_style = {"bd": 0, "relief": "flat", "highlightthickness": 1, "highlightbackground": "lightgray"}

# Customer message frame
customer_message_width = int(screen_width * 0.98)
customer_message_padding = 0
customer_message = tk.Frame(root, width=customer_message_width, height=int(screen_height ))
customer_message.place(x=customer_message_padding, y=int(screen_height * 0.93))

message_label = tk.Label(customer_message, text="  DEAR CUSTOMER, WE ARE PLEASED TO SERVE YOU. KINDLY SIT AND WAIT WHILE WE ARE SERVING OTHER CUSTOMERS  ",font=("roboto", int(screen_height * 0.025), "bold"), fg="white", bg="green", justify="center")
message_label.pack(fill=tk.BOTH, expand=True)

# Counter frames
num_counters = 4
counter_frame_width = int(screen_width * 0.1)
counter_frame_height = int(screen_height * 0.1)
counter_spacing = int(screen_width * 0.03)
counter_x_start = screen_width - counter_frame_width*1.1 
counter_y = 0

token_number_labels = []

def create_counter_frame(counter_id):
    counter_frame = tk.Frame(root, width=counter_frame_width, height=counter_frame_height, bg = "lightgreen")
    counter_frame.place(x=counter_x_start - (counter_id - 1) * (counter_frame_width + counter_spacing), y=counter_y+50)

    counter_label = tk.Label(counter_frame, text=f"Counter\n{num_counters - (counter_id - 1)}", font=("calibri", int(screen_height * 0.03), "bold"), fg="black", bg="lightgreen")
    counter_label.pack(fill=tk.BOTH, expand=True)
    counter_label.place(relx=0.5, rely=0.5, anchor=tk.CENTER)

    now_serving_frame = tk.Frame(root, width=counter_frame_width, height=int(counter_frame_height / 2), bg="lightgreen")
    now_serving_frame.place(x=counter_x_start - (counter_id - 1) * (counter_frame_width + counter_spacing), y=counter_y + counter_frame_height +65)

    now_serving_label = tk.Label(now_serving_frame, text="NOW SERVING", fg="white", font=("Arial", int(screen_height * 0.018), "bold"), bg="green")
    now_serving_label.pack(fill=tk.BOTH, expand=True)
      # Add frames for displaying token numbers
    token_frame = tk.Frame(root, width=counter_frame_width, height=int(counter_frame_height * 1.5), **frame_style)
    token_frame.place(x=counter_x_start - (counter_id - 1) * (counter_frame_width + counter_spacing), y=counter_y + counter_frame_height * 2.5)
    
    # Create a label to display the token number received
    token_number_label = tk.Label(token_frame, text="", font=("calibri", int(screen_height * 0.07), "bold"), fg="black")
    token_number_label.pack(fill=tk.BOTH, expand=True)
    token_number_label.place(relx=0.5, rely=0.5, anchor=tk.CENTER)
    token_number_labels.append(token_number_label)
    
    """token_frame = tk.Frame(root, width=counter_frame_width, height=int(counter_frame_height * 1.5), bg = "white")`1`
    token_frame.place(x=counter_x_start - (counter_id - 1) * (counter_frame_width + counter_spacing), y=counter_y + counter_frame_height * 2.5)
    
    token_number_label = tk.Label(token_frame, text="", font=("calibri", int(screen_height * 0.07), "bold"), fg="black")
    token_number_label.pack(fill=tk.BOTH, expand=True)
    token_number_label.place(relx=0.5, rely=0.5, anchor=tk.CENTER)"""

    next_button = tk.Button(root, text="Next", command=lambda: handle_next_button(counter_id))
   # next_button.place(x=counter_x_start - (counter_id - 1) * (counter_frame_width + counter_spacing), y=counter_y + counter_frame_height * 4)

    reset_button = tk.Button(root, text=f"Reset Counter {counter_id}", command=lambda: reset_counter(counter_id), font=("Arial", int(screen_height * 0.02), "bold"), bg="orange", fg="white")
    #reset_button.place(x=counter_x_start - (counter_id - 1) * (counter_frame_width + counter_spacing), y=counter_y + counter_frame_height * 1.5 + int(counter_frame_height * 1.5), width=counter_frame_width, height=int(screen_height * 0.05))

    token_number_labels.append(token_number_label)

API_KEY = 'fca_live_mYsEF4trK4HJtYz6voDrrO5663krEJewkSMnRYMY'

def update_prices():
    headers = {'apikey': API_KEY}
    api_endpoint = 'https://api.freecurrencyapi.com/v1/latest'
    params = {'apikey': API_KEY, 'currencies': ','.join(currencies)}
    response = requests.get(api_endpoint, headers=headers, params=params)
    data = response.json()
    
    print("API Response:", data)
    
    if 'data' in data:
        currency_data = data['data']
        
        usd_to_tzs = 2600  # 1 USD to TZS conversion rate
        spread_percentage = 2.0 / 100.0
        
        for i, currency in enumerate(currencies):
            if currency in currency_data:
                exchange_rate_to_usd = currency_data[currency]
                
                # print(f"Exchange Rate for {currency}: {exchange_rate_to_usd}")
                
                # Convert the exchange rate to TZS
                if currency == 'USD':
                    base_price_tzs = usd_to_tzs
                else:
                    base_price_tzs = usd_to_tzs / exchange_rate_to_usd
                
                buy_price_tzs = base_price_tzs * (1 - spread_percentage)
                sell_price_tzs = base_price_tzs * (1 + spread_percentage)
                
                print(f"Currency: {currency}")
                print(f"Base Price (TZS): {base_price_tzs}")
                print(f"Buy Price (TZS): {buy_price_tzs}")
                print(f"Sell Price (TZS): {sell_price_tzs}")
                
                buy_labels[i].config(text=f"{buy_price_tzs:.2f} ")
                sell_labels[i].config(text=f"{sell_price_tzs:.2f} ")
            else:
                print(f"No exchange rate data found for currency {currency}")
    else:
        print("Invalid API response format")
    
    root.after(300000, update_prices)


for i in range(1, num_counters + 1):
    create_counter_frame(i)

currency_frame_width = int(screen_width )
currency_frame_height = int(screen_height * 0.48)
currency_frame = tk.Frame(root, width=currency_frame_width, height=currency_frame_height, bg="white")
currency_frame.place(x=0, y=screen_height * 0.43)

column_width = currency_frame_width // 3

currency_label = tk.Label(currency_frame, text="CURRENCY", bg="green", font=("Arial", int(screen_height * 0.026), "bold"), fg="black")
currency_label.place(x=0, y=0, width=column_width)

buy_label = tk.Label(currency_frame, text="BUY", bg="green", font=("Arial", int(screen_height * 0.026), "bold"), fg="black")
buy_label.place(x=column_width, y=0, width=column_width)

sell_label = tk.Label(currency_frame, text="SELL", bg="green", font=("Arial", int(screen_height * 0.026), "bold"), fg="black")
sell_label.place(x=2 * column_width, y=0, width=column_width)

currencies = ['USD', 'EUR', 'GBP', 'JPY', 'CAD', 'CNY', 'CHF', 'AUD']
currency_labels = []
for i, currency in enumerate(currencies):
    label = tk.Label(currency_frame, text=currency, bg="lightgreen", font=("Arial", int(screen_height * 0.025)) , fg="black")
    label.place(x=0, y=int(screen_height * 0.055) * (i+1), width=column_width)
    currency_labels.append(label)

buy_labels = []
for i in range(len(currencies)):
    label = tk.Label(currency_frame, text="", bg="lightgreen", font=("Arial", int(screen_height * 0.025)),  fg="black")
    label.place(x=column_width, y=int(screen_height * 0.055) * (i+1), width=column_width)
    buy_labels.append(label)

sell_labels = []
for i in range(len(currencies)):
    label = tk.Label(currency_frame, text="", bg="lightgreen", font=("Arial", int(screen_height * 0.025)),  fg="black")
    label.place(x=2 * column_width, y=int(screen_height * 0.055) * (i+1), width=column_width)
    sell_labels.append(label)

update_prices()
update_token_labels()

# Video frame
video_frame = tk.Label(root, bg = "white")
video_frame.place(x=0, y=0, width=int(screen_width * 0.5), height=int(screen_height * 0.43))

# Set the path to the video file
video_path = r"D:\aluta\FYP\Documentation\videoplayback.mp4"  # Change to your actual video file path

# Open video capture globally
cap = cv2.VideoCapture(video_path)

def play_video():
    ret, frame = cap.read()
    if not ret:
        cap.set(cv2.CAP_PROP_POS_FRAMES, 0)  # Loop video
        return
    
    frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    frame = cv2.resize(frame, (int(screen_width * 0.4999), int(screen_height * 0.44)))
    img = ImageTk.PhotoImage(Image.fromarray(frame))
    
    video_frame.img = img
    video_frame.config(image=img)
    
    root.after(30, play_video)  # Update every 30ms for smooth playback

# Function to play audio sequence corresponding to the received token and counter numbers
def play_audio_sequence(token, counter, language):
    audio_directory = r"D:\aluta\FYP\Documentation\audios"  # specify the path where your audio files are stored
    language_folder = os.path.join(audio_directory, language)
    tens = token // 10 * 10
    units = token % 10

    if 10 < token < 20 and language == 'English':
        audio_sequence = [
            "bell.mp3",
            "MtejaNamba.mp3",
            f"nam{token}.mp3",
            "TafadhaliElekeaDirishaNamba.mp3",
            f"counter_{counter}.mp3",
        ]
    else:
        audio_sequence = [
            "bell.mp3",
            "MtejaNamba.mp3",
            f"nam{tens}.mp3",
            f"nam{units}.mp3",
            "TafadhaliElekeaDirishaNamba.mp3",
            f"counter_{counter}.mp3",
        ]
    
    # Play each audio file in the sequence
    for audio_file in audio_sequence:
        audio_path = os.path.join(language_folder, audio_file)
        pygame.mixer.music.load(audio_path)
        pygame.mixer.music.play()
        
        # Wait until the audio finishes playing before moving to the next
        while pygame.mixer.music.get_busy():
            pygame.time.Clock().tick(10)


# Function to play video
"""def play_video():
    cap = cv2.VideoCapture(video_path)
    while cap.isOpened():
        ret, frame = cap.read()
        if not ret:
            cap.set(cv2.CAP_PROP_POS_FRAMES, 0)  # Loop video
            continue
        frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        frame = cv2.resize(frame, (int(screen_width * 0.5), int(screen_height * 0.45)))
        img = ImageTk.PhotoImage(Image.fromarray(frame))
        video_frame.img = img
        video_frame.config(image=img)
        root.update_idletasks()
    cap.release()"""
play_video()
    
reset_db_button = tk.Button(root, text="Reset Database", command=reset_database, font=("Arial", int(screen_height * 0.02), "bold"), bg="red", fg="white")
#reset_db_button.place(x=int(screen_width * 0.05), y=int(screen_height * 0.92), width=int(screen_width * 0.15), height=int(screen_height * 0.05))

# Start the UDP listener in a separate thread
udp_thread = threading.Thread(target=udp_listener, daemon=True)
udp_thread.start()
# Run video in a separate thread to avoid UI freezing
video_thread = threading.Thread(target=play_video, daemon=True)
video_thread.start()

# Start the main event loop
root.mainloop()
