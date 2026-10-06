# TCP Chat Application

A command-line chat application built in Python. Clients connect to a threaded TCP server, register or log in, send messages, and view recent chat history. User accounts and messages are stored in SQLite through SQLAlchemy.

This was built as a Seneca course final project.

## Features

- Multiple clients can connect to the server
- User registration and login
- Salted PBKDF2 password hashes
- SQLite storage for accounts and chat messages
- Recent message history
- Docker image for running the server

## Requirements

- Python 3.10 or later
- Docker (optional, for running the server in a container)

SQLite is included with Python. SQLAlchemy is installed from `requirements.txt`.

## Run locally

Open a terminal in the project folder and install the dependency:

```bash
python -m pip install -r requirements.txt