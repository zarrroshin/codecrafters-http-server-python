import socket  # noqa: F401


def main():
    # You can use print statements as follows for debugging, they'll be visible when running tests.
    print("Logs from your program will appear here!")

    server_socket = socket.create_server(("localhost", 4221), reuse_port=True)
    client_connection, client_address = server_socket.accept() # wait for client
    data = client_connection.recv(1024) 
    request = data.decode("utf-8") # wait for client to send request
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
            client_connection.send(b"HTTP/1.1 200 OK\r\n\r\n")
        else:
            client_connection.send(b"HTTP/1.1 404 NOT FOUND\r\n\r\n")
    else:
        client_connection.send(b"HTTP/1.1 501 NOT IMPLEMENTED\r\n\r\n")
    client_connection.close()
    server_socket.close()

    


if __name__ == "__main__":
    main()
