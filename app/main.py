import argparse
import gzip
import os
import socket
import threading

HEADER_SEPARATOR = b"\r\n\r\n"
RECV_SIZE = 4096


def recv_until(connection, buffer, separator):
    while separator not in buffer:
        chunk = connection.recv(RECV_SIZE)
        if not chunk:
            return None, buffer
        buffer += chunk

    before, after = buffer.split(separator, 1)
    return before, after


def recv_exact(connection, buffer, size):
    while len(buffer) < size:
        chunk = connection.recv(RECV_SIZE)
        if not chunk:
            return None, buffer
        buffer += chunk

    return buffer[:size], buffer[size:]


def parse_request_line(line):
    parts = line.split(" ")
    if len(parts) != 3:
        return None
    return parts[0], parts[1], parts[2]


def parse_headers(header_bytes):
    try:
        header_text = header_bytes.decode("iso-8859-1")
    except UnicodeDecodeError:
        return None

    lines = header_text.split("\r\n")
    if not lines or not lines[0]:
        return None

    request_line = parse_request_line(lines[0])
    if request_line is None:
        return None

    headers = {}
    for line in lines[1:]:
        if not line or ":" not in line:
            continue
        name, value = line.split(":", 1)
        headers[name.strip().lower()] = value.strip()

    return request_line[0], request_line[1], request_line[2], headers


def accepted_encodings(header_value):
    return [item.strip() for item in header_value.split(",") if item.strip()]


def should_close_connection(version, headers):
    connection = headers.get("connection", "").lower()
    if connection == "close":
        return True
    if connection == "keep-alive":
        return False
    return not version.upper().startswith("HTTP/1.1")


def build_response(status, headers=None, body=b""):
    if headers is None:
        headers = {}

    headers = {**headers, "Content-Length": str(len(body))}
    lines = [f"HTTP/1.1 {status}"]
    for name, value in headers.items():
        lines.append(f"{name}: {value}")
    return ("\r\n".join(lines) + "\r\n\r\n").encode("iso-8859-1") + body


def safe_file_path(directory, filename):
    if not directory or not filename:
        return None

    if os.path.isabs(filename):
        return None

    parts = filename.replace("\\", "/").split("/")
    if any(part in ("", ".", "..") for part in parts):
        return None

    base = os.path.realpath(directory)
    full = os.path.realpath(os.path.join(base, filename))
    if full == base or not full.startswith(base + os.sep):
        return None
    return full


def handle_request(method, path, version, headers, body, directory):
    extra = {}
    close = should_close_connection(version, headers)
    if close:
        extra["Connection"] = "close"

    def respond(status, response_headers=None, response_body=b""):
        merged = dict(extra)
        if response_headers:
            merged.update(response_headers)
        return build_response(status, merged, response_body), close

    if method == "GET":
        if path == "/":
            return respond("200 OK")

        if path.startswith("/echo/"):
            echo_body = path[len("/echo/") :].encode("utf-8")
            response_headers = {"Content-Type": "text/plain"}
            if "gzip" in accepted_encodings(headers.get("accept-encoding", "")):
                echo_body = gzip.compress(echo_body)
                response_headers["Content-Encoding"] = "gzip"
            return respond("200 OK", response_headers, echo_body)

        if path == "/user-agent":
            user_agent = headers.get("user-agent", "").encode("utf-8")
            return respond(
                "200 OK",
                {"Content-Type": "text/plain"},
                user_agent,
            )

        if path.startswith("/files/"):
            file_path = safe_file_path(directory, path[len("/files/") :])
            if file_path is None:
                return respond("404 Not Found")
            try:
                with open(file_path, "rb") as file:
                    content = file.read()
            except FileNotFoundError:
                return respond("404 Not Found")
            except OSError:
                return respond("500 Internal Server Error")
            return respond(
                "200 OK",
                {"Content-Type": "application/octet-stream"},
                content,
            )

        return respond("404 Not Found")

    if method == "POST":
        if path.startswith("/files/"):
            file_path = safe_file_path(directory, path[len("/files/") :])
            if file_path is None:
                return respond("404 Not Found")
            try:
                with open(file_path, "wb") as file:
                    file.write(body)
            except OSError:
                return respond("500 Internal Server Error")
            return respond("201 Created")
        return respond("404 Not Found")

    return respond("501 Not Implemented")


def handle_client(client_connection, client_address, directory):
    buffer = b""
    try:
        while True:
            header_bytes, buffer = recv_until(
                client_connection, buffer, HEADER_SEPARATOR
            )
            if header_bytes is None:
                break

            parsed = parse_headers(header_bytes)
            if parsed is None:
                client_connection.sendall(
                    build_response("400 Bad Request", {"Connection": "close"})
                )
                break

            method, path, version, headers = parsed

            print(f"Client: {client_address}")
            print(f"Method: {method}")
            print(f"Path: {path}")
            print(f"Version: {version}")

            try:
                content_length = int(headers.get("content-length", "0"))
                if content_length < 0:
                    raise ValueError
            except ValueError:
                client_connection.sendall(
                    build_response("400 Bad Request", {"Connection": "close"})
                )
                break

            body, buffer = recv_exact(client_connection, buffer, content_length)
            if body is None:
                break

            response, close = handle_request(
                method, path, version, headers, body, directory
            )
            client_connection.sendall(response)
            if close:
                break
    except OSError:
        pass
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

    print("Server is running on localhost:4221")
    print(f"Files directory: {directory}")

    server_socket = socket.create_server(("localhost", 4221), reuse_port=True)
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
