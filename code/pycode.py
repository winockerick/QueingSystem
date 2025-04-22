import tkinter as tk
import mysql.connector

# Connect to the MySQL database
db = mysql.connector.connect(
    host="localhost",              # Database server address (localhost for local server)
    user="root",                   # Username for MySQL (default for XAMPP)
    password="",                  # Password for MySQL (default for XAMPP is usually empty)
    database="trial"  # Name of the database to connect to
)

cursor = db.cursor()  # Create a cursor object to interact with the database

def get_next_token():
    """
    Retrieve the next token number by finding the highest token number
    in the database and incrementing it by 1.
    """
    cursor.execute("SELECT MAX(token_number) FROM tokens")  # Query to get the highest token number
    result = cursor.fetchone()  # Fetch the result of the query
    next_token = (result[0] or 0) + 1  # Calculate the next token number
    return next_token

def update_counter(counter_id, token_number):
    """
    Update the specified counter with the new token number.

    Args:
    counter_id (int): ID of the counter to update.
    token_number (int): The new token number to assign.
    """
    cursor.execute("UPDATE counters SET current_token = %s WHERE id = %s", (token_number, counter_id))
    db.commit()  # Commit the transaction to save changes

def insert_token(token_number):
    """
    Insert a new token number into the tokens table.

    Args:
    token_number (int): The token number to insert.
    """
    cursor.execute("INSERT INTO tokens (token_number) VALUES (%s)", (token_number,))
    db.commit()  # Commit the transaction to save changes

def handle_next_button(counter_id):
    """
    Simulate the "Next" button press for a counter. This function generates
    the next token number, inserts it into the database, and updates the
    specified counter with the new token number.

    Args:
    counter_id (int): ID of the counter that pressed the "Next" button.
    """
    next_token = get_next_token()  # Get the next token number
    insert_token(next_token)       # Insert the new token into the database
    update_counter(counter_id, next_token)  # Update the counter with the new token
    token_number_labels[counter_id - 1].config(text=str(next_token))  # Update the token number display
    print(f"Counter {counter_id} now serving token {next_token}")  # Print the result

# Create the main window
root = tk.Tk()
root.title("Queue Management System")

# Set window to full-screen mode
root.attributes('-fullscreen', True)

# Get screen width and height
screen_width = root.winfo_screenwidth()
screen_height = root.winfo_screenheight()

# Define frame styles
frame_style = {"bd": 2, "relief": "raised"}

# Customer message frame
customer_message_width = int(screen_width * 0.98)  # 98% of window width
customer_message_padding = int(screen_width * 0.01)  # 1% padding from both sides
customer_message = tk.Frame(root, width=customer_message_width, height=int(screen_height * 0.1), **frame_style)
customer_message.place(x=customer_message_padding, y=int(screen_height * 0.85))

# Add label inside the customer message frame
message_label = tk.Label(customer_message, text="DEAR CUSTOMER, WE ARE PLEASED TO SERVE YOU. KINDLY SIT AND WAIT WHILE WE ARE SERVING OTHER CUSTOMERS",
                         font=("Poppins", int(screen_height * 0.02), "bold"), bg="lightgreen", justify="center")
message_label.pack(fill=tk.BOTH, expand=True)

# Counter frames
num_counters = 4
counter_frame_width = int(screen_width * 0.1)  # 10% of window width
counter_frame_height = int(screen_height * 0.1)  # 10% of window height
counter_spacing = int(screen_width * 0.01)  # Horizontal spacing between counters
counter_x_start = screen_width - counter_frame_width  # Starting X coordinate for the first counter frame
counter_y = 0  # Y coordinate for all counter frames

# List to store references to token number labels and button callbacks
token_number_labels = []
next_buttons = []

def create_counter_frame(counter_id):
    """
    Create and place a counter frame with a 'Next' button and token number display.

    Args:
    counter_id (int): ID of the counter.
    """
    # Add frame to display counters
    counter_frame = tk.Frame(root, width=counter_frame_width, height=counter_frame_height, **frame_style)
    counter_frame.place(x=counter_x_start - (counter_id - 1) * (counter_frame_width + counter_spacing), y=counter_y)

    # Add label to display counter ID
    counter_label = tk.Label(counter_frame, text=f"Counter\n{num_counters - (counter_id - 1)}", font=("calibri", int(screen_height * 0.03), "bold"), fg="white", bg="green")
    counter_label.pack(fill=tk.BOTH, expand=True)
    # Center the label vertically and horizontally
    counter_label.place(relx=0.5, rely=0.5, anchor=tk.CENTER)

    # Add "NOW SERVING" frames below counters
    now_serving_frame = tk.Frame(root, width=counter_frame_width, height=int(counter_frame_height / 2), bg="white")
    now_serving_frame.place(x=counter_x_start - (counter_id - 1) * (counter_frame_width + counter_spacing), y=counter_y + counter_frame_height)

    # Add label with "NOW SERVING" text
    now_serving_label = tk.Label(now_serving_frame, text="NOW SERVING", fg="green", font=("Arial", int(screen_height * 0.02), "bold"), bg="white")
    now_serving_label.pack(fill=tk.BOTH, expand=True)

    # Add frames for displaying token numbers
    token_frame = tk.Frame(root, width=counter_frame_width, height=int(counter_frame_height * 1.5), **frame_style)
    token_frame.place(x=counter_x_start - (counter_id - 1) * (counter_frame_width + counter_spacing), y=counter_y + counter_frame_height * 1.5)
    
    # Create a label to display the token number received
    token_number_label = tk.Label(token_frame, text="", font=("calibri", int(screen_height * 0.07), "bold"), fg="black")
    token_number_label.pack(fill=tk.BOTH, expand=True)
    token_number_label.place(relx=0.5, rely=0.5, anchor=tk.CENTER)

    # Add "Next" button
    next_button = tk.Button(counter_frame, text="Next", command=lambda: handle_next_button(counter_id))
    next_button.pack(fill=tk.BOTH, expand=True)
    next_button.place(relx=0.5, rely=1.0, anchor=tk.S)

    # Append the label and button to the lists
    token_number_labels.append(token_number_label)
    next_buttons.append(next_button)

# Create all counter frames
for i in range(1, num_counters + 1):
    create_counter_frame(i)

# Frame for currency operations (not used in this example, but kept for layout purposes)
currency_frame_width = int(screen_width * 0.55)
currency_frame_height = int(screen_height * 0.25)
currency_frame = tk.Frame(root, width=currency_frame_width, height=currency_frame_height, bg="lightgray")
currency_frame.place(x=0, y=int(screen_height * 0.55))  # Place below token frames

# Define column widths for currency operations
column_width = currency_frame_width // 3

# Labels for headings
currency_label = tk.Label(currency_frame, text="CURRENCY", bg="green", font=("Arial", int(screen_height * 0.02), "bold"), fg="white")
currency_label.place(x=0, y=0, width=column_width)

buy_label = tk.Label(currency_frame, text="BUY", bg="green", font=("Arial", int(screen_height * 0.02), "bold"), fg="white")
buy_label.place(x=column_width, y=0, width=column_width)

sell_label = tk.Label(currency_frame, text="SELL", bg="green", font=("Arial", int(screen_height * 0.02), "bold"), fg="white")
sell_label.place(x=2 * column_width, y=0, width=column_width)

# Labels for currency names
currencies = ['USD', 'EUR', 'GBP', 'JPY', 'CAD', 'CNY', 'CHF', 'AUD']
currency_labels = []
for i, currency in enumerate(currencies):
    label = tk.Label(currency_frame, text=currency, bg="lightgreen", font=("Arial", int(screen_height * 0.015), "bold"))
    label.place(x=0, y=int(screen_height * 0.025) * (i+1), width=column_width)
    currency_labels.append(label)
    
    
# Labels for buy prices
buy_labels = []
for i in range(len(currencies)):
    label = tk.Label(currency_frame, text="", bg="lightgreen", font=("Arial", int(screen_height * 0.015), "bold"))
    label.place(x=column_width, y=int(screen_height * 0.025) * (i+1), width=column_width)
    buy_labels.append(label)

# Labels for sell prices
sell_labels = []
for i in range(len(currencies)):
    label = tk.Label(currency_frame, text="", bg="lightgreen", font=("Arial", int(screen_height * 0.015), "bold"))
    label.place(x=2 * column_width, y=int(screen_height * 0.025) * (i+1), width=column_width)
    sell_labels.append(label)


# Start the main event loop
root.mainloop()