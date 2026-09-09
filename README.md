# HTTP Server from Scratch

A small HTTP/1.1 server in Python, built with raw sockets — no `http.server`, Flask, or FastAPI.

This repo is a **practice project**: the goal was to go deeper into how HTTP actually works (request parsing, headers, keep-alive, compression) instead of only using a framework. It follows the [Codecrafters “Build Your Own HTTP Server”](https://app.codecrafters.io/courses/http-server/overview) challenge.

## What it does

| Route | Method | Behavior |
| --- | --- | --- |
| `/` | `GET` | `200 OK` |
| `/echo/{text}` | `GET` | Echoes the path as `text/plain` |
| `/user-agent` | `GET` | Returns the `User-Agent` header |
| `/files/{name}` | `GET` | Serves a file from `--directory` |
| `/files/{name}` | `POST` | Creates a file (`201 Created`) |

Also:

- Concurrent clients with one thread per connection
- Persistent connections (HTTP/1.1 keep-alive)
- `Connection: close`
- `gzip` when the client sends `Accept-Encoding: gzip`
- `Content-Length` on every response
- Reads the full request (headers, then body by `Content-Length`)
- Rejects path traversal (`../`) on `/files/`

## Why this exercise

Frameworks hide the protocol. Writing the server by hand makes these pieces concrete:

1. TCP accept loop vs. one HTTP request
2. Where headers end (`\r\n\r\n`) and how the body length is known
3. Why keep-alive breaks if you omit `Content-Length`
4. How `Content-Encoding: gzip` changes the body, not the status line

Codecrafters is used as the test harness and staged roadmap — not as a copy-paste tutorial.

## Run locally

Python 3.14+ (see `.python-version`).

```bash
python3 -m app.main --directory /tmp/http-server-files
```

The server listens on `localhost:4221`.

```bash
# empty 200
curl -i http://localhost:4221/

# echo
curl -i http://localhost:4221/echo/hello

# gzip
curl -i --compressed http://localhost:4221/echo/hello

# user-agent
curl -i -A "my-client/1.0" http://localhost:4221/user-agent

# files
mkdir -p /tmp/http-server-files
echo 'hi' > /tmp/http-server-files/foo.txt
curl -i http://localhost:4221/files/foo.txt
curl -i -X POST -d 'posted' http://localhost:4221/files/bar.txt
```

If you have [uv](https://docs.astral.sh/uv/) (Codecrafters local runner):

```bash
./your_program.sh --directory /tmp/http-server-files
```

## Layout

```
app/main.py          # server
your_program.sh      # local Codecrafters entrypoint
pyproject.toml
```

## Challenge

[Build Your Own HTTP Server](https://app.codecrafters.io/courses/http-server/overview) on [Codecrafters](https://codecrafters.io) — implement HTTP/1.1 from TCP up, in the language you pick.

## License

For learning. Use and change it as you like.
