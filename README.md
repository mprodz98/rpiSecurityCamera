# rpiSecurityCamera
This is a personal project in which I turned a raspberry pi into a security camera that both sends texts to you when a detection is made and uploads data to aws using DynamoDB

Steps to run:
1.Upload arduino code to an arduino MEGA with pins 2 and 4 used for the ultrasonic sensor according to the SR04 library and use pin 3 as the digital input from the ky-038 sound detector module
2.The sound detector module will have to be tuned to detect sound correctly
2.Make sure raspberry pi is functioning with opencv, awscli, and twilio installed
3.Edit the python file so that lines 16, 18, and 166 contain your own twilio account information and phone number
4.Create table in DynamoDB with same title and parameters as in the python code
5.Run python program
