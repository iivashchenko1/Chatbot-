"""Threaded TCP chat server with SQLite-backed accounts and message history."""

import logging
import os
import socket
import threading

from database import (
    authenticate_user,
    create_user,
    get_recent_messages,
    init_db,
    save_message,
)

HOST = os.environ.get("CHAT_HOST", "0.0.0.0")
PORT = int(os.environ.get("CHAT_PORT", "5000"))

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(message)s",
)
logger = logging.getLogger(__name__)

clients: list[dict[str, object]] = []
clients_lock = threading.Lock()


def send_line(connection: socket.socket, message: str) -> None:
    """Send one UTF-8 line to a client."""
    connection.sendall((message + "\n").encode("utf-8"))


def broadcast_message(username: str, content: str) -> None:
    """Save a message, then send it to each connected client."""
    save_message(username, content)
    message = f"[{username}] {content}"

    with clients_lock:
        current_clients = list(clients)

    for client in current_clients:
        connection = client["conn"]
        try:
            send_line(connection, message)  # type: ignore[arg-type]
        except OSError:
            logger.info("Could not send to a disconnected client.")


def handle_client(connection: socket.socket, address: tuple[str, int]) -> None:
    """Handle registration/login and chat messages for one client."""
    username: str | None = None
    reader = connection.makefile("r", encoding="utf-8")

    logger.info("Connection opened from %s", address)

    try:
        send_line(connection, "Welcome to the chat server!")
        send_line(connection, "Type 'register' to create an account or 'login' to sign in:")

        while username is None:
            command = reader.readline()
            if not command:
                return

            command = command.strip().lower()

            if command == "register":
                send_line(connection, "Choose a username:")
                requested_username = reader.readline()
                if not requested_username:
                    return

                send_line(connection, "Choose a password:")
                password = reader.readline()
                if not password:
                    return

                requested_username = requested_username.strip()
                password = password.rstrip("\r\n")

                if not requested_username or not password:
                    send_line(connection, "Username and password cannot be empty.")
                elif create_user(requested_username, password):
                    send_line(connection, "Account created. Type 'login' to sign in.")
                else:
                    send_line(connection, "That username is already taken.")

            elif command == "login":
                send_line(connection, "Username:")
                requested_username = reader.readline()
                if not requested_username:
                    return

                send_line(connection, "Password:")
                password = reader.readline()
                if not password:
                    return

                requested_username = requested_username.strip()
                password = password.rstrip("\r\n")

                if authenticate_user(requested_username, password):
                    username = requested_username
                    send_line(connection, f"Login successful. Welcome, {username}!")
                else:
                    send_line(connection, "Invalid username or password. Try again.")

            else:
                send_line(connection, "Please type 'register' or 'login'.")

        with clients_lock:
            clients.append({"conn": connection, "username": username})

        send_line(connection, "--- Recent messages ---")
        for old_username, content, created_at in get_recent_messages():
            send_line(connection, f"[{created_at}] {old_username}: {content}")
        send_line(connection, "--- End of history ---")

        broadcast_message("SYSTEM", f"{username} joined the chat.")
        send_line(connection, "You are now in the chat. Type '/quit' to leave.")

        while True:
            line = reader.readline()
            if not line:
                break

            message = line.strip()
            if not message:
                continue

            if message == "/quit":
                send_line(connection, "Goodbye!")
                break

            broadcast_message(username, message)

    except (OSError, UnicodeError):
        logger.info("Client %s disconnected.", address)
    except Exception:
        logger.exception("Unexpected error while handling client %s", address)
    finally:
        reader.close()

        if username is not None:
            with clients_lock:
                clients[:] = [
                    client for client in clients
                    if client["conn"] is not connection
                ]
            try:
                broadcast_message("SYSTEM", f"{username} left the chat.")
            except Exception:
                logger.exception("Could not save the departure message.")

        connection.close()
        logger.info("Connection closed for %s", address)


def main() -> None:
    """Initialize storage and accept incoming TCP connections."""
    init_db()

    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as server_socket:
        server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        server_socket.bind((HOST, PORT))
        server_socket.listen()
        logger.info("Chat server listening on %s:%s", HOST, PORT)

        try:
            while True:
                connection, address = server_socket.accept()
                thread = threading.Thread(
                    target=handle_client,
                    args=(connection, address),
                    daemon=True,
                )
                thread.start()
        except KeyboardInterrupt:
            logger.info("Server shutting down.")


if __name__ == "__main__":
    main()