import socket
import base64
import hashlib
import os
import struct
import json
import urllib.request
import sys

def ws_connect(url):
    # url: ws://127.0.0.1:9222/devtools/page/...
    url_clean = url.replace("ws://", "")
    host_port, path = url_clean.split("/", 1)
    host, port = host_port.split(":")
    port = int(port)
    path = "/" + path

    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.settimeout(5.0)
    s.connect((host, port))

    sec_key = base64.b64encode(os.urandom(16)).decode('utf-8')
    headers = [
        f"GET {path} HTTP/1.1",
        f"Host: {host}:{port}",
        "Upgrade: websocket",
        "Connection: Upgrade",
        f"Sec-WebSocket-Key: {sec_key}",
        "Sec-WebSocket-Version: 13",
        "\r\n"
    ]
    s.sendall("\r\n".join(headers).encode('utf-8'))
    
    resp = s.recv(4096)
    if not resp.startswith(b"HTTP/1.1 101"):
        raise RuntimeError(f"WebSocket upgrade failed: {resp[:100]}")
    return s

def ws_send(s, data_str):
    data = data_str.encode('utf-8')
    length = len(data)
    
    # Client to server frames must be masked
    mask_key = os.urandom(4)
    frame = bytearray()
    frame.append(0x81) # text frame, FIN=1
    
    if length < 126:
        frame.append(0x80 | length)
    elif length < 65536:
        frame.append(0x80 | 126)
        frame.extend(struct.pack("!H", length))
    else:
        frame.append(0x80 | 127)
        frame.extend(struct.pack("!Q", length))
        
    frame.extend(mask_key)
    masked_data = bytearray(data[i] ^ mask_key[i % 4] for i in range(length))
    frame.extend(masked_data)
    
    s.sendall(frame)

def ws_recv(s):
    header = s.recv(2)
    if len(header) < 2:
        return None
    b1, b2 = header[0], header[1]
    opcode = b1 & 0x0f
    is_masked = bool(b2 & 0x80)
    length = b2 & 0x7f
    if length == 126:
        length = struct.unpack("!H", s.recv(2))[0]
    elif length == 127:
        length = struct.unpack("!Q", s.recv(8))[0]
    
    mask = s.recv(4) if is_masked else None
    data = bytearray()
    while len(data) < length:
        chunk = s.recv(length - len(data))
        if not chunk: break
        data.extend(chunk)
        
    if is_masked:
        data = bytearray(data[i] ^ mask[i % 4] for i in range(len(data)))
    return data.decode('utf-8', errors='replace')

def eval_expression(expr):
    tabs = json.loads(urllib.request.urlopen("http://127.0.0.1:9222/json", timeout=3).read().decode())
    target = [t for t in tabs if t.get('type') == 'page'][0]
    ws_url = target['webSocketDebuggerUrl']
    s = ws_connect(ws_url)
    req = json.dumps({"id": 1, "method": "Runtime.evaluate", "params": {"expression": expr, "userGesture": True, "awaitPromise": True, "returnByValue": True}})
    ws_send(s, req)
    res = ws_recv(s)
    s.close()
    print("CDP_RESULT:", res)
    return res

if __name__ == "__main__":
    if len(sys.argv) > 1:
        eval_expression(sys.argv[1])
