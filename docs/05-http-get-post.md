# 05 · HTTP, GET and POST

Unreal and the server communicate with plain HTTP on the local machine. Before wiring it in Blueprints, send the same requests by hand: when something later does not work, you will know what a correct exchange looks like.

## 5.1 The concepts you need

- **Client and server.** The server (`uvicorn`) listens on an address and port, here `127.0.0.1:8000`. `127.0.0.1` is the loopback address: traffic stays inside the machine and nothing outside can reach it. The client (curl, later Unreal) opens a connection, sends a request, reads the response.
- **Request.** A *method* (`GET`, `POST`), a *path* (`/health`, `/query`), headers, and optionally a *body*.
- **GET** asks for a resource and carries no body. `/health` is a GET: it returns the server's state.
- **POST** sends data for the server to process. `/query` is a POST: the body is the sentence.
- **JSON** is the body format. A JSON object is a set of `"name": value` pairs, for example `{"text": "make the cube red"}`. The header `Content-Type: application/json` tells the server how to read the body.
- **Status code** in the response: `200` success, `405` wrong method for that path, `422` the body is valid JSON but does not have the expected fields, connection refused when nothing listens on that port.

Note that `200` only means the server understood the request. Whether the *sentence* matched an action is in the field `status` of the JSON (`ok`, `ambiguous`, `out_of_scope`). Unreal must check both levels: whether the request completed at all, and what `status` says.

## 5.2 GET

The server must be running ([04](04-python-server.md#43-start-the-server)).

**Linux, macOS**

```bash
curl http://127.0.0.1:8000/health
```

**Windows (PowerShell)**

```powershell
curl.exe http://127.0.0.1:8000/health
```

## 5.3 POST

**Linux, macOS**

```bash
curl -X POST http://127.0.0.1:8000/query -H "Content-Type: application/json" -d '{"text":"make the cube red"}'
```

**Windows (PowerShell)** (Windows PowerShell 5.1 drops the inner double quotes when it passes arguments to `curl.exe`, which breaks the JSON; use PowerShell's own command)

```powershell
Invoke-RestMethod -Method Post -Uri http://127.0.0.1:8000/query -ContentType "application/json" -Body '{"text":"make the cube red"}'
```

Response (`Invoke-RestMethod` prints it as an object, with the same fields):

```json
{"status":"ok","score":0.9999,"margin":0.9903,"alternatives":[{"id":"cube_red","title":"cube red"},{"id":"cube_blue","title":"cube blue"},{"id":"cube_green","title":"cube green"}],"timing":{"retrieve_ms":211.3,"rerank_ms":30.0},"id":"cube_red","params":{"color":"red"},"reply":"The cube is now red."}
```

The server terminal shows `POST /query HTTP/1.1" 200 OK`. The fields Unreal uses are `status`, `id` and `reply`.

Try these and compare:

| Sentence | `status` | `id` |
|---|---|---|
| `make the cube red` | `ok` | `cube_red` |
| `rendi il cubo blu` | `ok` | `cube_blue` |
| `order me a pizza` | `out_of_scope` | (absent) |
| `paint the wall red` | `ok` | `cube_red` (a known false accept, score 0.62) |

The first request after start-up can take a second longer (warm-up).

## 5.4 Three errors worth provoking once

Seeing them here makes them recognisable in Unreal.

**Wrong field name** (the field must be `text`):

```bash
curl -X POST http://127.0.0.1:8000/query -H "Content-Type: application/json" -d '{"txt":"x"}'
```

Answer, status `422`: `{"detail":[{"type":"missing","loc":["body","text"],"msg":"Field required","input":{"txt":"x"}}]}`. In Unreal this happens if the **Field Name** of *Set String Field* is not exactly `text`.

**Wrong method** (GET on `/query`):

```bash
curl http://127.0.0.1:8000/query
```

Answer, status `405`: `{"detail":"Method Not Allowed"}`.

**Server stopped** (press Ctrl+C in the server terminal, then repeat the health check): curl reports *connection refused*. In Unreal this is the case that raises **On Request Fail**.

## 5.5 The interactive documentation

FastAPI generates a test page for every route. With the server running, open <http://127.0.0.1:8000/docs> in a browser, expand **POST /query** → **Try it out**, edit the body and press **Execute**. It shows the request, the response and the status code.

Next: [06 · Blueprints](06-blueprints.md).
