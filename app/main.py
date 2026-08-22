import socket
import threading
import argparse
import os
import gzip




def handle_client(client_connection, client_address, directory):
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
                accept_encoding = ""

                for line in request_lines[1:]:
                    if line == "":
                        break

                    if line.lower().startswith("accept-encoding:"):
                        accept_encoding = line.split(":", 1)[1].strip()
                        break
                accepted_encodings = [
                    encoding.strip()
                    for encoding in accept_encoding.split(",")
                ]

                echo_string = path[len("/echo/"):]
                body = echo_string.encode("utf-8")

                headers = (
                    "HTTP/1.1 200 OK\r\n"
                    "Content-Type: text/plain\r\n"
                )

            # سرور فعلاً فقط gzip را پشتیبانی می‌کند
                if "gzip" in accepted_encodings:
                    headers += "Content-Encoding: gzip\r\n"
                    body = gzip.compress(body)

                headers += (
                    f"Content-Length: {len(body)}\r\n"
                    "\r\n"
                )

                client_connection.sendall(headers.encode("utf-8") + body)


            elif path.startswith("/files/"):
                        filename = path[len("/files/"):]
                        file_path = os.path.join(directory, filename)

                        try:
                            with open(file_path, "rb") as f:
                                content = f.read()

                            headers = (
                                "HTTP/1.1 200 OK\r\n"
                                "Content-Type: application/octet-stream\r\n"
                                f"Content-Length: {len(content)}\r\n"
                                "\r\n"
                            ).encode("utf-8")

                            client_connection.sendall(headers + content)

                        except FileNotFoundError:
                            client_connection.sendall(
                                b"HTTP/1.1 404 Not Found\r\n\r\n"
                            )

            elif path == "/user-agent":
                user_agent = ""

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

        elif method =="POST":
            if path.startswith("/files/"):
                filename = path[len("/files/"):]
                file_path = os.path.join(directory, filename)
                try:
                    body = data.split(b"\r\n\r\n",1)[1]
                    with open(file_path,"wb") as f :
                        f.write(body)
                    client_connection.sendall(
                                        b"HTTP/1.1 201 Created\r\n\r\n"
                                    )
                except:
                    client_connection.sendall(
                                        b"HTTP/1.1 404 Not Found\r\n\r\n"
                                    )


                

                
            
        else:
            client_connection.sendall(
                b"HTTP/1.1 501 Not Implemented\r\n\r\n"
            )

    finally:
        client_connection.close()


def main():
    parser = argparse.ArgumentParser()

    parser.add_argument(
        "--directory",
        default=None,
        help="Directory used for serving files",
    )

    args = parser.parse_args()
    directory = args.directory

    print(f"Server is running on localhost:4221")
    print(f"Files directory: {directory}")

    server_socket = socket.create_server(("localhost", 4221))

    try:
        while True:
            client_connection, client_address = server_socket.accept()

            thread = threading.Thread(
                target=handle_client,
                args=(client_connection, client_address, directory),
                daemon=True,
            )
            thread.start()

    finally:
        server_socket.close()


if __name__ == "__main__":
    main()
