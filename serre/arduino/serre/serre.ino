// Mini serre - Arduino Nano
// DHT22 -> D2 | Capteur sol capacitif -> A0 | Ventilateur (MOSFET) -> D5
// Pompe (MOSFET/relais) -> D6 | LED culture (MOSFET) -> D9
// Bibliotheque: "DHT sensor library" (Adafruit)
#include <DHT.h>

const uint8_t PIN_DHT = 2, PIN_SOL = A0, PIN_VENT = 5, PIN_POMPE = 6, PIN_LED = 9;
const float T_VENT_ON = 28.0, T_VENT_OFF = 26.0;      // hysteresis ventilateur (C)
const int SOL_SEC = 600;          // valeur brute > seuil = sol sec (a calibrer)
const unsigned long POMPE_MS = 3000;           // duree arrosage
const unsigned long ATTENTE_MS = 600000UL;     // 10 min entre 2 arrosages
const unsigned long LECTURE_MS = 5000;

DHT dht(PIN_DHT, DHT22);
bool vent = false;
unsigned long tLecture = 0, tArrosage = 0;
bool arrose = false;

void setup() {
  Serial.begin(9600);
  pinMode(PIN_VENT, OUTPUT);
  pinMode(PIN_POMPE, OUTPUT);
  pinMode(PIN_LED, OUTPUT);
  analogWrite(PIN_LED, 180);        // lumiere ~70 %
  dht.begin();
  tArrosage = millis() - ATTENTE_MS; // autorise un arrosage au demarrage
}

void loop() {
  unsigned long now = millis();

  if (arrose && now - tArrosage >= POMPE_MS) {   // fin arrosage
    digitalWrite(PIN_POMPE, LOW);
    arrose = false;
  }

  if (now - tLecture >= LECTURE_MS) {
    tLecture = now;
    float t = dht.readTemperature();
    float h = dht.readHumidity();
    int sol = analogRead(PIN_SOL);

    if (!isnan(t)) {
      if (t >= T_VENT_ON) vent = true;
      else if (t <= T_VENT_OFF) vent = false;
      digitalWrite(PIN_VENT, vent);
    }
    if (!arrose && sol > SOL_SEC && now - tArrosage >= ATTENTE_MS) {
      digitalWrite(PIN_POMPE, HIGH);
      arrose = true;
      tArrosage = now;
    }
    Serial.print("T="); Serial.print(t);
    Serial.print(" H="); Serial.print(h);
    Serial.print(" sol="); Serial.print(sol);
    Serial.print(" vent="); Serial.print(vent);
    Serial.print(" pompe="); Serial.println(arrose);
  }
}
