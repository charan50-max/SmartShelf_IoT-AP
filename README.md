# SmartShelf 📚

**SmartShelf** is an RFID-based library management system that helps manage books and student borrowing records. It combines an Arduino and RC522 RFID reader with a Python desktop application built using Tkinter and an SQLite database.

The system can register students and books, issue and return books by scanning RFID tags, track due dates, send email notifications, and export transaction history as a PDF report.

## Features

- **RFID-based identification:** Read card/tag UIDs using an RC522 reader connected to an Arduino.
- **Student management:** Register, view, edit, and delete student records.
- **Book management:** Register books, search the inventory, view availability, and delete books.
- **Book checkout:** Scan a student card followed by a book tag to record an issue.
- **Book returns:** Scan an issued book to mark it as available again.
- **Due-date tracking:** Configure the return period; the default is 7 days.
- **Email notifications:** Optionally send welcome emails and book issue confirmations.
- **Transaction history:** View borrowing activity and pending returns.
- **PDF reports:** Export transaction history to a PDF file.
- **Local database:** Store book, student, and transaction data in SQLite.

## Technology Stack

| Component | Technology |
|---|---|
| RFID hardware | Arduino Uno (or compatible board) |
| RFID reader | MFRC522 / RC522 |
| Hardware communication | SPI |
| Desktop application | Python, Tkinter |
| Serial communication | `pyserial` |
| Database | SQLite |
| Image handling | Pillow |
| Email | SMTP over SSL |
| PDF reports | ReportLab |
| Time zone handling | `pytz` |

## Hardware Requirements

- Arduino Uno or a compatible Arduino board
- MFRC522 RFID reader module
- Compatible RFID cards or tags
- USB cable for connecting the Arduino to the computer
- Jumper wires and a breadboard, if needed
- Computer running Python

## Wiring: RC522 to Arduino Uno

| RC522 pin | Arduino Uno pin |
|---|---|
| SDA / SS | D10 |
| SCK | D13 |
| MOSI | D11 |
| MISO | D12 |
| RST | D9 |
| GND | GND |
| 3.3V | 3.3V |

**Important:** The RC522 module is a 3.3 V device. Connect its power pin to **3.3 V, not 5 V**. Check your specific module's pin labels before wiring it.

## Software Requirements

- Python 3
- Arduino IDE
- Git (optional, for cloning the repository)
- Python packages listed below

Install the required Python packages from a terminal:

```bash
python -m pip install pyserial pillow pytz reportlab
```

The Python application also uses standard-library modules such as `tkinter`, `sqlite3`, `smtplib`, and `csv`. Tkinter may need to be installed separately on some Linux distributions.

## Arduino Setup

1. Install the **MFRC522** library in Arduino IDE using the Library Manager.
2. Connect the RC522 reader to the Arduino according to the wiring table.
3. Open the Arduino sketch in the repository.
4. Select the correct Arduino board and port in **Tools**.
5. Upload the sketch.
6. Open Serial Monitor at **9600 baud** and scan a tag to confirm that its UID is printed.

The sketch uses these pin definitions:

```cpp
#define SS_PIN 10
#define RST_PIN 9
```

It prints each scanned UID in hexadecimal, with bytes separated by colons. The Python application reads UIDs from the Arduino's serial output, so the Arduino sketch and Python application must use the same UID format.

## Python Application Setup

1. Clone or download this repository.
2. Open a terminal in the project directory.
3. Install the required Python packages.
4. Open the Python application and set `ARDUINO_PORT` to the serial port used by your computer. For example:

   ```python
   ARDUINO_PORT = "COM3"
   ARDUINO_BAUD = 9600
   ```

   On Linux, the port may look like `/dev/ttyACM0` or `/dev/ttyUSB0`.

5. Configure email credentials using the secure configuration approach described in the **Email Configuration and Security** section.
6. Ensure any required image asset (such as `nhitm.jpeg`) is in the expected location, or adjust the image path in the application.
7. Run the Python application:

   ```bash
   python main.py
   ```

   Replace `main.py` with the actual filename of your Python application.

The application creates `smartshelf.db` and its tables when it starts, provided it can write to the project directory.

## How to Use

### 1. Register a student

- Open **Add Student**.
- Scan the student's RFID card.
- Enter the student's name and unique IEN number.
- Add phone and email details if required.
- Save the record.

### 2. Register a book

- Open **Register Book**.
- Scan the RFID tag assigned to the book.
- Enter the book title and save it.

### 3. Issue a book

- Open **Checkout Book**.
- Scan the registered student's RFID card first.
- Scan the book's RFID tag next.
- The application records the issue and calculates the due date using the configured return duration.
- If an email address is available and SMTP is configured, an issue confirmation can be sent.

### 4. Return a book

- Open **Return Book**.
- Scan the book's RFID tag.
- The application marks the book as available and records a return transaction.

### 5. View records and export a report

Use the **Menu** to access transaction history, student records, pending returns, return-duration settings, and PDF transaction export.

## Database Overview

The application uses a local SQLite database named `smartshelf.db`.

| Table | Purpose |
|---|---|
| `books` | Stores each book's RFID UID, title, and availability status |
| `students` | Stores student IEN number, RFID UID, name, phone, and email |
| `transactions` | Records issue and return events, timestamps, and due dates |

The application also uses `return_config.txt` to store the configured return period in days. If that file is absent or cannot be read, the application defaults to **7 days**.

## Email Configuration and Security

Email notifications use Gmail SMTP over SSL. Configure the sender address and credentials outside the source code, preferably through environment variables or a local `.env` file that is excluded from Git.

**Never commit email passwords, Gmail App Passwords, API keys, or other secrets to a public repository.** If a real credential has already been committed or shared, revoke it and generate a replacement.

The application needs valid SMTP credentials and a recipient email address for email notifications to work. Email delivery can fail even when the library functions work correctly.

## Troubleshooting

- **Arduino not detected:** Check the USB cable, selected COM/serial port, and whether another application is using the port.
- **No UID appears:** Verify the RC522 wiring, 3.3 V power supply, MFRC522 library, and Serial Monitor baud rate (9600).
- **UID not recognized:** Register the card first and make sure the UID format produced by the Arduino matches the format stored in SQLite.
- **Serial port access denied:** Close Arduino Serial Monitor and any other program using the same port.
- **Email notification fails:** Verify the sender address, Gmail App Password, SMTP settings, network access, and recipient address.
- **Logo is missing:** Check the image filename and path used by the application.
- **PDF export fails:** Confirm that ReportLab is installed and that the chosen output folder is writable.

## Limitations and Notes

- This is a local desktop application; the SQLite database is stored on the computer running it.
- The application must be able to connect to the Arduino for RFID scanning features.
- The current implementation uses RFID UIDs for identification. A UID alone should not be treated as strong authentication because some tags can be cloned or emulated.
- Test issue/return flows and back up the database before using the application with important records.
- Ensure that the return and transaction logic is tested for your intended library workflow before production use.

## Future Improvements

- Add role-based login for librarians and administrators.
- Add automated overdue reminders.
- Improve transaction validation and handling of multiple outstanding loans.
- Add database backups and data import/export.
- Move email credentials to environment variables and add a sample configuration file.
- Add automated tests for book issue, return, and inventory status.

## Contributing

Contributions, bug reports, and suggestions are welcome. Create a branch for your changes and submit a pull request with a clear description of the update.

## License

Add a license file before describing this project as open source. If no license is included, all rights remain with the copyright holder by default.
