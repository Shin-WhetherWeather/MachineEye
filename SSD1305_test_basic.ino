#include <Wire.h>
#include <SPI.h>
#include <Adafruit_GFX.h>
#include <Adafruit_SSD1305.h>

#define OLED_CS 10
#define OLED_DC 8
#define OLED_RESET 9

Adafruit_SSD1305 display(128, 32, &SPI, OLED_DC, OLED_RESET, OLED_CS);


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
  Serial1.begin(115200, SERIAL_8N1, 1, 0); 
  Serial1.setTimeout(20);

  //Gyroscope setup
  //------------------------------------------------------------------
  SPI.begin();
  SPI.beginTransaction(SPISettings(1000000, MSBFIRST, SPI_MODE3));
  
  pinMode(7, OUTPUT);
  digitalWrite(7, HIGH);
  delay(250);

  //Sets full range to 4G
  spiWrite(0x01, 0b00000000);
  spiWrite(0x12, 0b00000001);
  spiWrite(0x10, 0b10011010);

  digitalWrite(7, LOW);
  delayMicroseconds(250);
  
  SPI.transfer(0x0F | 0b10000000);
  int val = SPI.transfer(0x00);
  //Serial.println(val);
  
  delayMicroseconds(250);
  digitalWrite(7, HIGH);
  SPI.endTransaction();
  delay(25);
  //------------------------------------------------------------------

  //Display Setup
  //------------------------------------------------------------------

  display.begin(0x3C);
  display.clearDisplay();
  display.display();
  display.setTextWrap(false);
  display.setTextSize(1);
  display.setTextColor(WHITE);

  x = 0;
  y = 10;

  renderText("                   Welcome to Machine Eye! I try to make sense of the world around me.                      ");

  scrollTime = millis();
  updateTime = millis();

  //------------------------------------------------------------------
}

void spiWrite(byte addr, byte dat){
  //Hard coded SPI transfer function for the gyroscope
  digitalWrite(7, LOW);
  delayMicroseconds(1);
  SPI.transfer(addr);
  SPI.transfer(dat);
  digitalWrite(7, HIGH);
  delayMicroseconds(500); 
}

void read6(byte addr, int *val){
  //Hard coded function to read all the X, Y, and Z accelerations
  SPI.beginTransaction(SPISettings(1000000, MSBFIRST, SPI_MODE3));
  digitalWrite(7, LOW);
  delayMicroseconds(1);
  SPI.transfer(addr | 0b10000000);
  for(byte i = 0; i < 3; i++){
    val[i] = SPI.transfer(0xff) | (SPI.transfer(0x00) << 8);
    if(val[i] >= 32768){
      val[i] -= 65536;
    }  
  }
  digitalWrite(7, HIGH);
  delayMicroseconds(1);
  SPI.endTransaction();
}

void loop() {
  String cmd = Serial1.readStringUntil('\n');

  if(cmd.length()){
    //strips the first character off the serial input
    char code = cmd.charAt(0);
    switch(code){
      case 'T':{
        //print text
        //-------------------------------------------------------
        cmd = cmd.substring(1);
        renderText("                   " + cmd + "                      ");
        Serial.println(cmd);
        //-------------------------------------------------------
      }break;
      case 'G':{
        //fetch gyro
        //-------------------------------------------------------
        int val[] = {0,0,0};
        int valAvg[] = {0,0,0};

        //Samples 4x and summed
        //Averaging is done on the Raspberry Pi
        for(int i = 0; i < 4; i++){
          read6(0x28, val);
          for(int i = 0; i < 3; i++){
            valAvg[i] = valAvg[i] + val[i];
          }
        }

        //Sends the gyroscope values over over Serial
        Serial1.print(valAvg[0]);
        Serial1.print(" ");
        Serial1.print(valAvg[1]);
        Serial1.print(" ");
        Serial1.println(valAvg[2]);
        Serial1.flush();
        //-------------------------------------------------------
      }break;
    }
  }

  printText(40);


}
