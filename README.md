# MBRS Project

## Overview

The **MBRS Project** is a Python-based booking and reservation management system designed to manage bookings efficiently while supporting user authentication, reservation management, cancellations, and no-show tracking.

The project demonstrates fundamental software engineering concepts including modular programming, data management, authentication, testing, and version control using Git and GitHub.

---

## Objectives

The project aims to:

- Provide a simple reservation management solution.
- Demonstrate modular Python programming.
- Implement secure user authentication.
- Manage bookings and cancellations.
- Record and monitor customer no-shows.
- Serve as a collaborative academic group project.

---

## Features

- User Authentication
- Booking Management
- Reservation Cancellation
- No-show Tracking
- Data Storage
- Automated Unit Testing
- Modular Architecture

---

## Project Structure

```
MBRS-Project/
│
├── auth.py
├── booking.py
├── cancellation.py
├── data_store.py
├── main.py
├── manifest.py
├── models.py
├── noshow.py
├── test_mbrs.py
├── utils.py
│
├── README.md
├── LICENSE
└── .gitignore
```

---

## Module Description

### `main.py`

Acts as the application's entry point.

Responsibilities include:

- Starting the application
- Calling different system modules
- Managing overall workflow

---

### `auth.py`

Handles authentication functionality.

Possible responsibilities include:

- User login
- User verification
- Authentication validation

---

### `booking.py`

Responsible for booking operations including:

- Creating bookings
- Viewing reservations
- Updating reservation records

---

### `cancellation.py`

Handles reservation cancellations.

Responsibilities:

- Cancel reservations
- Update booking status
- Maintain reservation integrity

---

### `noshow.py`

Manages customers who fail to honour reservations.

Possible functions include:

- Recording no-shows
- Updating reservation history
- Reporting missed bookings

---

### `models.py`

Defines the application's data structures and models.

---

### `data_store.py`

Responsible for storing and retrieving application data.

Depending on implementation, this may involve:

- Files
- JSON
- SQLite
- In-memory storage

---

### `utils.py`

Contains reusable helper functions used throughout the project.

---

### `manifest.py`

Contains project configuration or application metadata.

---

### `test_mbrs.py`

Contains automated tests used to verify application functionality.

---

## Technologies Used

- Python 3
- Git
- GitHub
- Visual Studio Code

---

## Requirements

Before running the project ensure you have:

- Python 3.10+
- Git
- Visual Studio Code (recommended)

---

## Installation

Clone the repository:

```bash
git clone https://github.com/Kabaka-dev/MBRS-Project.git
```

Navigate into the project directory:

```bash
cd MBRS-Project
```

(Optional) Create a virtual environment:

```bash
python -m venv venv
```

Activate it.

Windows

```bash
venv\Scripts\activate
```

Linux/macOS

```bash
source venv/bin/activate
```

---

## Running the Project

Run:

```bash
python main.py
```

---

## Running Tests

Execute:

```bash
python test_mbrs.py
```

or

```bash
pytest
```

if pytest is being used.

---


## Version Control Workflow

Typical workflow:

```bash
git pull

git add .

git commit -m "Describe your changes"

git push
```

---

## Future Improvements

Potential enhancements include:

- Web-based interface 
- Email notifications 
- Reporting dashboard 
- User role management 
- Reservation analytics 
- REST API implementation 

---

## Contributors

Project developed collaboratively by members of the group.

GitHub repository collaborators are listed under:

**Settings → Collaborators**

Project contributors can also be viewed from:

**Insights → Contributors**

---

## License

This project is licensed under the MIT License.

See the `LICENSE` file for details.

---

## Repository

GitHub Repository:

https://github.com/Kabaka-dev/MBRS-Project

---
