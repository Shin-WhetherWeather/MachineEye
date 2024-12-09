#include <Wire.h>
#include <SPI.h>
#include <Adafruit_GFX.h>
#include <Adafruit_SSD1305.h>

// Used for software SPI
#define OLED_CLK 6
#define OLED_MOSI 8

// Used for software or hardware SPI
#define OLED_CS 10
#define OLED_DC 8

// Used for I2C or SPI
#define OLED_RESET 9

// software SPI

Adafruit_SSD1305 display(128, 32, &SPI, OLED_DC, OLED_RESET, OLED_CS);
// hardware SPI - use 7Mhz (7000000UL) or lower because the screen is rated for 4MHz, or it will remain blank!
// Adafruit_SSD1305 display(128, 64, &SPI, OLED_DC, OLED_RESET, OLED_CS, 7000000UL);


//#define TEXT "    Hello, world! I am hungry and tired and upside down!    "

String displayText = "";

int16_t x, y;
uint16_t w, h;
int16_t scrollX;
uint32_t scrollTime;
uint32_t updateTime;

void renderText(String text){
  displayText = text;
  int16_t  x1, y1;
  display.getTextBounds(displayText, x,y, &x1, &y1, &w, &h);
}

void printText(uint16_t scrollInterval){
  if( (millis() - scrollTime) < scrollInterval){
    return;
  }
  scrollTime = millis();
  
  display.clearDisplay();

  //automatically scroll text if it is longer than the screen
  if(w > 128){
    display.setCursor(x + scrollX,y);
    scrollX--;
    if(scrollX < (128-w)){
        scrollX = 0;
    }
  }else{
    display.setCursor(x,y);
  }

  display.println(displayText);
  display.display();
}


void setup() {
  Serial.begin(115200);
  Serial1.begin(115200, SERIAL_8N1, 0, 1); 
  
  display.begin(0x3C);

  display.clearDisplay();
  display.display();
  display.setTextWrap(false);
  display.setTextSize(1);
  display.setTextColor(WHITE);

  x = 0;
  y = 10;

  renderText("    Hello world! I am hungry and tired and upside down!!    ");

  scrollTime = millis();
  updateTime = millis();

}




void loop() {
  if(Serial1.available() > 0 ){
    String incomingData;
    incomingData = Serial1.readString();

    if(incomingData.length() > 0){
      renderText(incomingData);
    }
  }

  printText(40);
}
