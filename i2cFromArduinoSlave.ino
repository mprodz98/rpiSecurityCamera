

// Include the Wire library for I2C
#include <Wire.h>
#include "SR04.h" //library for ultrasonic sensor
#include <EEPROM.h>
#define TRIG_PIN 2
#define ECHO_PIN 4
SR04 sr04 = SR04(ECHO_PIN,TRIG_PIN);
volatile unsigned long a=0;//variable to store ultrasonic sensor reading
int b=0;//variable to store sound detector boolean value
byte arr[5]={0,0,0,0,0};//array to store bits to transmit arr[0] through arr[3] 
//are storing ultrasonic sensor values and arr[5] stores sound detector values
void setup() {
   pinMode(3,INPUT); //This is the pin of the sound detector
  // Join I2C bus as slave with address 8
  Wire.begin(0x8);

  Wire.setClock(10000);//this sets freq of i2c communication on slave side
   
  while(1==1){ 

    // Call receiveEvent when data received        
      Wire.onReceive(receiveEvent);
      a=sr04.Distance();
      b=digitalRead(3);
    arr[0] = a & 0xFF; // Least significant byte of ultrasonic sensor reading
  arr[1] = (a >> 8) & 0xFF; 
  arr[2] = (a >> 16) & 0xFF; 
  arr[3] = (a >> 24) & 0xFF; // Most significant byte of ultrasonic sensor reading
  arr[4]=b;
   EEPROM.put(0, arr);
  // Call sendData when data received                
  Wire.onRequest(sendData);      
  }


}

// Function that executes whenever data is received from master
void receiveEvent(int howMany) {
  while (Wire.available()) { 
//The arduino is never receiving info but is only requested info
//this function is only here for additions that could be made

  }
  
  
}
void sendData(int howMany) {
//since the master side reads the whole entire register of register 0
//this is not necessary but it does not hurt to include it
   Wire.write(arr,5);
    
  } 
    
  }
void loop() {
  delay(100);
}
