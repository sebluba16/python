// Mini serre - Arduino Nano + SG90 (aération) + DHT22 + sol capacitif + LDR
// Libs : "DHT sensor library" (Adafruit) ; Servo (incluse)
#include <Servo.h>
#include <DHT.h>

#define PIN_DHT   2
#define PIN_SERVO 9
#define PIN_SOL   A0
#define PIN_LDR   A1

const float T_OPEN  = 28.0;   // °C : ouvre la ventilation
const float T_CLOSE = 25.0;   // °C : referme (hystérésis)
const int   SERVO_CLOSED = 0, SERVO_OPEN = 80;
const int   SOL_SEC = 600, SOL_HUMIDE = 300; // à calibrer (valeurs ADC)

DHT dht(PIN_DHT, DHT22);
Servo vent;
bool ouvert = false;

void setup() {
  Serial.begin(9600);
  dht.begin();
  vent.attach(PIN_SERVO);
  vent.write(SERVO_CLOSED);
}

void loop() {
  float t = dht.readTemperature(), h = dht.readHumidity();
  int sol = analogRead(PIN_SOL), lum = analogRead(PIN_LDR);

  if (!isnan(t)) {
    if (!ouvert && t > T_OPEN)  { vent.write(SERVO_OPEN);   ouvert = true; }
    if (ouvert  && t < T_CLOSE) { vent.write(SERVO_CLOSED); ouvert = false; }
  }
  Serial.print("T="); Serial.print(t); Serial.print(" H="); Serial.print(h);
  Serial.print(" sol="); Serial.print(sol); Serial.print(sol > SOL_SEC ? " SEC" : "");
  Serial.print(" lum="); Serial.print(lum); Serial.print(" vent="); Serial.println(ouvert);
  delay(2000);
}
