#include <SPI.h>
#include <MFRC522.h>

#define SS_PIN 10
#define RST_PIN 9

MFRC522 mfrc522(SS_PIN, RST_PIN);

void setup() {
  Serial.begin(9600);

  SPI.begin();
  mfrc522.PCD_Init();

  Serial.println("Ready - Scan an RFID tag...");
}

void loop() {

  // Look for a new card
  if (!mfrc522.PICC_IsNewCardPresent()) {
    return;
  }

  // Read the card
  if (!mfrc522.PICC_ReadCardSerial()) {
    return;
  }

  // Print UID in HEX format
  for (byte i = 0; i < mfrc522.uid.size; i++) {

    if (mfrc522.uid.uidByte[i] < 0x10) {
      Serial.print("0");
    }

    Serial.print(mfrc522.uid.uidByte[i], HEX);

    if (i < mfrc522.uid.size - 1) {
      Serial.print(":");
    }
  }

  Serial.println();

  mfrc522.PICC_HaltA();
  mfrc522.PCD_StopCrypto1();

  delay(500);
}