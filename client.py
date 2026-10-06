"""Command-line client for the TCP chat server."""

import os
import socket
import threading

SERVER_HOST = os.environ.get("CHAT_HOST", "127.0.0.1")
SERVER_PORT = int(os.environ.get("CHAT_PORT", "5000"))


def send_line(connection: socket.socket, message: str) -> None:
    """Send one UTF-8 line to the server."""
    connection.sendall((message + "\n").encode("utf-8"))


def listen_to_server(
    connection: socket.socket,
    disconnected: threading.Event,
) -> None:
    """Print messages received from the server until it closes the connection."""
    try:
        with connection.makefile("r", encoding="utf-8") as reader:
            for line in reader:
                print(f"\n{line.rstrip()}")
                print("> ", end="", flush=True)
    except OSError as error:
        print(f"\nConnection error: {error}")
    finally:
        disconnected.set()
        print("\n[INFO] Server connection closed.")


def main() -> None:
    """Connect to the server and send user-entered lines."""
    try:
        connection = socket.create_connection((SERVER_HOST, SERVER_PORT))
    except OSError as error:
        print(f"Could not connect to {SERVER_HOST}:{SERVER_PORT}: {error}")
        return

    print(f"Connected to {SERVER_HOST}:{SERVER_PORT}. Type '/quit' to leave.")

    disconnected = threading.Event()
    listener = threading.Thread(
        target=listen_to_server,
        args=(connection, disconnected),
        daemon=True,
    )
    listener.start()

    try:
        while not disconnected.is_set():
            try:
                message = input("> ").strip()
            except (EOFError, KeyboardInterrupt):
                print("\n[INFO] Leaving chat.")
                break

            if not message:
                continue

            try:
                send_line(connection, message)
            except OSError:
                print("[INFO] Could not send message; the server may have closed.")
                break

            if message == "/quit":
                break
    finally:
        connection.close()
        listener.join(timeout=1)


if __name__ == "__main__":
    main()