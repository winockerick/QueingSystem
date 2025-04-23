#include <WiFi.h>
#include <WiFiUdp.h>
#include <Keypad.h>
#include <WiFiClient.h>
#include <LiquidCrystal_I2C.h>

// WiFi and UDP Settings
const char* ssid = "INNO DON";
const char* password = "Tanzania2023";
const char* udpAddress = "192.168.100.246"; // Raspberry Pi IP
const int udpPort = 12345;
WiFiUDP udp;

// Keypad Setup
const byte ROWS = 4;
const byte COLS = 4;
char hexaKeys[ROWS][COLS] = {
  {'1', '2', '3', '3'},
  {'4', '5', '6', '6'},
  {'7', '8', '9', '9'},
  {'*', '0', '#', 'D'}
};
byte rowPins[ROWS] = {33, 25, 26, 14};
byte colPins[COLS] = {27, 13, 16, 4};
Keypad customKeypad = Keypad(makeKeymap(hexaKeys), rowPins, colPins, ROWS, COLS);

// LCD Setup
LiquidCrystal_I2C lcd(0x27, 16, 2);

// Token Variables
String phoneNumber = "";
int globalToken = 0; // Shared counter for all tokens

void setup() {
  // Initialize Serial Monitor
  Serial.begin(115200);

  // Initialize LCD
  lcd.init();
  lcd.backlight();
  lcd.print("Enter Phone No:");

  // Connect to WiFi
  WiFi.begin(ssid, password);
  while (WiFi.status() != WL_CONNECTED) {
    delay(500);
    lcd.setCursor(0, 1);
    lcd.print("Connecting...");
  }
  lcd.clear();
  lcd.print("WiFi Connected!");
  delay(2000);
  lcd.clear();
  lcd.print("Enter Phone No:");
}

void loop() {
  // Get the key pressed on the keypad
  char key = customKeypad.getKey();

  if (key) {
    // Handle submission of phone number
    if (key == '*' || key == '#') {
      if (phoneNumber.length() == 10) { // Validate phone number length
        globalToken++; // Increment global token counter
        lcd.clear();
        String tokenType = (key == '*') ? "regular" : "priority";

        // Display token and type on LCD
        lcd.print("Token: " + String(globalToken));
        lcd.setCursor(0, 1);
        lcd.print("Type: " + tokenType);

        // Prepare data to send via UDP
        String data = phoneNumber + "," + String(globalToken) + "," + tokenType;

        // Send data to Raspberry Pi
        udp.beginPacket(udpAddress, udpPort);
        udp.print(data);
        if (udp.endPacket()) {
          Serial.println("UDP packet sent successfully!");
        } else {
          Serial.println("Failed to send UDP packet.");
        }

        // Reset phone number for the next customer
        phoneNumber = "";
        delay(3000);
        lcd.clear();
        lcd.print("Enter Phone No:");
      } else {
        // Handle invalid phone number
        lcd.clear();
        lcd.print("Invalid Number!");
        delay(2000);
        lcd.clear();
        lcd.print("Enter Phone No:");
      }
    } else if (key == 'D') {
      // Clear the phone number input
      phoneNumber = "";
      lcd.clear();
      lcd.print("Enter Phone No:");
    } else if (isdigit(key)) {
      // Append digit to phone number
      phoneNumber += key;
      lcd.setCursor(0, 1);
      lcd.print(phoneNumber);
    }
  }
}
/*#include <WiFi.h>
#include <WiFiUdp.h>
#include <Keypad.h>

#include <LiquidCrystal_I2C.h>

// Network credentials
const char* ssid = "3D & Robotics Lab";
const char* password = "3DRobotics";

WiFiUDP udp;
// UDP settings
const char* udpAddress = "192.168.0.218";
const int udpPort = 12345;

// Keypad settings
const byte ROWS = 4;
const byte COLS = 4;
char hexakeys[ROWS][COLS] = {
  { '1', '2', '3', 'A' },
  { '4', '5', '6', 'B' },
  { '7', '8', '9', 'C' },
  { '*', '0', '#', 'D' }

};
byte rowPins[ROWS] = { 33, 25, 26, 14 };
byte colPins[COLS] = { 27, 13, 16, 4 };
Keypad customKeypad = Keypad(makeKeymap(hexakeys), rowPins, colPins, ROWS, COLS);

// Define variables for current state of the system
String inputToken = "";
int currentToken = 0;
int counterId = 2;

void transmitData(int token, int counter);
void transmitData(char key, int counterId);
void printMessage(const char* message);
void scrollMessage(const char* message, int row);

//Initializing the Lcd
LiquidCrystal_I2C lcd(0x27, 16, 2);

void setup() {
  Serial.begin(115200);
  Serial.println("Initializing...");

  // Connect to Wi-Fi
  WiFi.begin(ssid, password);
  Serial.print("Connecting to Wi-Fi");
  lcd.init();
    lcd.backlight();
    lcd.clear();

  
  // Wait for connection
  int attempts = 0;
  while (WiFi.status() != WL_CONNECTED && attempts < 20) {
    delay(500);  // Wait for 0.5 seconds
    lcd.setCursor(0,0);
    lcd.print("Waiting...");
    Serial.print(".");
    attempts++;
  }

  

  if (WiFi.status() == WL_CONNECTED) {
    Serial.println("\nConnected to Wi-Fi");
    Serial.print("IP Address: ");
 printMessage("INVALID");
    lcd.clear();
    Serial.println(WiFi.localIP());
  } else {
    Serial.println("\nFailed to connect to Wi-Fi");
    lcd.setCursor(0,0);
    lcd.print("NO CONNECTION");
    while (true) {
      delay(1000);  // Stay here if Wi-Fi connection fails
    }
  }

    
  // Initialize UDP
  udp.begin(udpPort);
  Serial.print("UDP Listening on port ");
  Serial.println(udpPort);
}


void loop() {

  // Get key pressed from keypad
  char customKey = customKeypad.getKey();

  // Check if a key is pressed
  if (customKey) {
    Serial.println(customKey);  // Debug: print key to Serial Monitor
   
    // Display the pressed key on the LCD
    lcd.clear();
    lcd.setCursor(0, 0);
    lcd.print("Key: ");
    lcd.print(customKey); 
   

    // Handle specific key actions
    if (customKey == 'D') {
      lcd.clear();
      printMessage("NEXT");
     // scrollMessage(" umeita mteja anaefuata ahsante",0);
      //delay(5000);
      //lcd.clear();
    } else if (customKey == '*') {
      printMessage("WAITING PERIOD");
    } else {
      Serial.println("Invalid key press!");
      printMessage("INVALID");

    }
     
      udp.beginPacket(udpAddress, udpPort);
    udp.write(counterId);
    udp.write(customKey);
    udp.endPacket();
    

    // Check if the packet was successfully sent
if (udp.endPacket()) {
  Serial.println("UDP packet sent successfully!");
} else {
  Serial.println("Failed to send UDP packet.");
}
  }


 // delay(1000); // Debounce delay
}

  
/*void loop() {
  char customKey = Keypad.getKey();
  if (customKey == 'A') {
    Serial.print("Key pressed: ");
    Serial.println(customKey);
    printMessage("" ,0);
    
    

    // Send key over UDP
    udp.beginPacket(udpAddress, udpPort);
    udp.write(customKey);
    udp.endPacket();
  }
}*
void printMessage(const char* message){
    lcd.clear();
    scrollMessage(message,0);
}

void scrollMessage(const char* message, int row){
  int len = strlen(message);
  if (len <= 16){
    lcd.setCursor(0, row);
    lcd.print(message);
    return;
  }

  for(int i = 0; i < len-16+1; i++){
    lcd.setCursor(0, row);
    lcd.print(message + 1);
    delay(300);
  }
  delay(1000);
  for(int i = 0; i < 16; i++){
    lcd.scrollDisplayLeft();
    delay(300);
  }
  lcd.clear();
}
*/

