#include <FastLED.h>

#if defined(ESP8266)
#include <ESP8266WiFi.h>
#include <WiFiUdp.h>
#elif defined(ESP32)
#include <WiFi.h>
#else
#error "This is not a ESP8266 or ESP32!"
#endif

// Set to the number of LEDs in your LED strip
#define NUM_LEDS 240
// Maximum number of packets to hold in the buffer. Don't change this.
#define BUFFER_LEN 1024
// Toggles FPS output (1 = print FPS over serial, 0 = disable output)
#define PRINT_FPS 0

// make sure to set this to the correct pin, ignored for Esp8266(set to 3 by default for DMA)
#define LED_DT D5

CRGB leds[NUM_LEDS];

// Wifi and socket settings
const char* ssid     = "YOUR_WIFI_SSID";
const char* password = "YOUR_WIFI_PASSWORD";
unsigned int localPort = 7777;
char packetBuffer[BUFFER_LEN];
bool WifiStatus = true;

uint8_t N = 0;

WiFiUDP port;

void setup() {
    pinMode(LED_BUILTIN, OUTPUT);
    Serial.begin(115200);

    FastLED.addLeds<NEOPIXEL, LED_DT>(leds, NUM_LEDS);
    FastLED.setMaxPowerInVoltsAndMilliamps(5,3000);
    FastLED.setCorrection(TypicalPixelString);

    WiFi.mode(WIFI_STA);
    WiFi.begin(ssid, password);
    Serial.println("");

    FastLED.clear();
    FastLED.show();
    fill_solid(leds, NUM_LEDS, CRGB(255,255,255));
    FastLED.show();
    
    // Connect to wifi and print the IP address over serial
    while (WiFi.status() != WL_CONNECTED) {
        delay(250);
        digitalWrite(LED_BUILTIN, !digitalRead(LED_BUILTIN));
    }
    
    digitalWrite(LED_BUILTIN, LOW);
    port.begin(localPort);
}

#if PRINT_FPS
    uint16_t fpsCounter = 0;
    uint32_t secondTimer = 0;
#endif

void loop() {
    if (WiFi.status() == WL_CONNECTED && !WifiStatus) {
        WifiStatus = true;
        digitalWrite(LED_BUILTIN, !digitalRead(LED_BUILTIN));
        fill_solid(leds, NUM_LEDS, CRGB(255,255,255));
        FastLED.show();
    }
    if (WiFi.status() != WL_CONNECTED && WifiStatus) {
        WifiStatus = false;
        digitalWrite(LED_BUILTIN, !digitalRead(LED_BUILTIN));
        FastLED.clear();
        for (int i = 0; i < NUM_LEDS; i += 4) {
            leds[i] = CRGB(0, 0, 2);
            FastLED.show();
        }
    }
    // Read data over socket
    int packetSize = port.parsePacket();
    // If packets have been received, interpret the command
    if (packetSize) {
        int len = port.read(packetBuffer, BUFFER_LEN);
        if (len == 4 && (String)packetBuffer == "server") {
          port.beginPacket(port.remoteIP(), port.remotePort());
          port.write(packetBuffer);
          port.endPacket();
        } else {
          for(int i = 0; i < len; i+=4) {
            packetBuffer[len] = 0;
            N = packetBuffer[i];
            leds[N] = CRGB((uint8_t)packetBuffer[i+1], (uint8_t)packetBuffer[i+2], (uint8_t)packetBuffer[i+3]);
          } 
          FastLED.show();
        }
        #if PRINT_FPS
            fpsCounter++;
            Serial.print("/");//Monitors connection(shows jumps/jitters in packets)
        #endif
    }
    #if PRINT_FPS
        if (millis() - secondTimer >= 1000U) {
            secondTimer = millis();
            Serial.printf("FPS: %d\n", fpsCounter);
            fpsCounter = 0;
        }   
    #endif
}