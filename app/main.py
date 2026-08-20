import socket


def main():
    print("Logs from your program will appear here!")

    server_socket = socket.create_server(("localhost", 4221))

    client_connection, client_address = server_socket.accept()

    try:
        data = client_connection.recv(1024)
        request = data.decode("utf-8")

        request_lines = request.split("\r\n")
        request_line = request_lines[0]
        request_line_parts = request_line.split(" ")

        method = request_line_parts[0]
        path = request_line_parts[1]
        version = request_line_parts[2]

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

            else:
                client_connection.sendall(
                    b"HTTP/1.1 404 Not Found\r\n\r\n"
                )

        else:
            client_connection.sendall(
                b"HTTP/1.1 501 Not Implemented\r\n\r\n"
            )

    finally:
        client_connection.close()
        server_socket.close()


if __name__ == "__main__":
    main()
