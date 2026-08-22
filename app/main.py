import socket
import threading


def handle_client(client_connection, client_address):
    try:
        data = client_connection.recv(1024)

        if not data:
            return

        request = data.decode("utf-8")
        request_lines = request.split("\r\n")
        request_line = request_lines[0]
        request_line_parts = request_line.split(" ")

        method = request_line_parts[0]
        path = request_line_parts[1]
        version = request_line_parts[2]

        print(f"Client: {client_address}")
        print(f"Method: {method}")
        print(f"Path: {path}")
        print(f"Version: {version}")

        if method == "GET":
            if path == "/":
                client_connection.sendall(
                    b"HTTP/1.1 200 OK\r\n\r\n"
                )

            elif path.startswith("/echo/"):
                echo_string = path[len("/echo/"):]
                body = echo_string.encode("utf-8")

                headers = (
                    "HTTP/1.1 200 OK\r\n"
                    "Content-Type: text/plain\r\n"
                    f"Content-Length: {len(body)}\r\n"
                    "\r\n"
                ).encode("utf-8")

                client_connection.sendall(headers + body)

            elif path == "/user-agent":
                user_agent = ""

                # از خط ۱ شروع می‌کنیم، چون خط ۰ request line است
                for line in request_lines[1:]:
                    if line == "":
                        break

                    if line.lower().startswith("user-agent:"):
                        user_agent = line.split(":", 1)[1].strip()
                        break

                body = user_agent.encode("utf-8")

                headers = (
                    "HTTP/1.1 200 OK\r\n"
                    "Content-Type: text/plain\r\n"
                    f"Content-Length: {len(body)}\r\n"
                    "\r\n"
                ).encode("utf-8")

                client_connection.sendall(headers + body)

            else:
                client_connection.sendall(
                    b"HTTP/1.1 404 Not Found\r\n\r\n"
                )

        else:
            client_connection.sendall(
                b"HTTP/1.1 501 Not Implemented\r\n\r\n"
            )

    finally:
        # فقط اتصال همان client بسته می‌شود
        client_connection.close()


def main():
    print("Server is running on localhost:4221")

    server_socket = socket.create_server(("localhost", 4221))

    try:
        while True:
            # سرور دائماً اتصال‌های جدید را قبول می‌کند
            client_connection, client_address = server_socket.accept()

            # رسیدگی به هر client در thread مستقل
            thread = threading.Thread(
                target=handle_client,
                args=(client_connection, client_address),
                daemon=True,
            )
            thread.start()

    finally:
        server_socket.close()


if __name__ == "__main__":
    main()
