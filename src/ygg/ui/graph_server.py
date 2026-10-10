"""The graph window: a local page served by the terminal app, always open next to it.

  GET  /            the viewer (Cytoscape.js)
  GET  /graph.json  the explanation graph of the open investigation, exactly as recorded by 'ygg case'
  GET  /events      Server-Sent Events: {"type": "reload"} and {"type": "focus", "id": ...} from the terminal
  POST /select      {"id": ...} from the viewer: the terminal selects that object

Shared persistent ids (narrative ids, BOT, terminal names) are the only coupling between the two surfaces.
Standard library only (asyncio); binds 127.0.0.1.
"""
from __future__ import annotations

import asyncio
import json
from pathlib import Path

STATIC = Path(__file__).parent / "static" / "graph.html"


class GraphServer:
    def __init__(self, on_select, host: str = "127.0.0.1", port: int = 8765):
        self.on_select, self.host, self.port = on_select, host, port
        self.payload: dict = {"title": "no investigation open", "nodes": [], "edges": [], "trees": {}}
        self.subs: list[asyncio.Queue] = []
        self.server = None

    @property
    def url(self) -> str:
        return f"http://{self.host}:{self.port}/"

    async def start(self) -> None:
        self.server = await asyncio.start_server(self._handle, self.host, self.port)

    def publish(self, msg: dict) -> None:
        for q in list(self.subs):
            q.put_nowait(msg)

    def show(self, payload: dict) -> None:
        self.payload = payload
        self.publish({"type": "reload"})

    def focus(self, node_id: str) -> None:
        self.publish({"type": "focus", "id": node_id})

    async def _handle(self, reader: asyncio.StreamReader, writer: asyncio.StreamWriter) -> None:
        try:
            head = await reader.readuntil(b"\r\n\r\n")
        except Exception:
            writer.close()
            return
        lines = head.decode("latin-1").split("\r\n")
        method, path, *_ = (lines[0].split(" ") + ["", ""])[:3]
        path = path.split("?", 1)[0]                     # the viewer takes ?view=expl|hood|full
        headers = {k.lower(): v.strip() for k, _, v in (ln.partition(":") for ln in lines[1:] if ln)}
        try:
            if method == "GET" and path in ("/", "/index.html"):
                page = STATIC.read_text().replace("/*__GRAPH__*/null", json.dumps(self.payload).replace("</", "<\\/"))
                await self._send(writer, 200, page.encode(), "text/html; charset=utf-8")
            elif method == "GET" and path.startswith("/graph.json"):
                await self._send(writer, 200, json.dumps(self.payload).encode(), "application/json")
            elif method == "GET" and path.startswith("/events"):
                await self._events(writer)
                return
            elif method == "POST" and path.startswith("/select"):
                n = int(headers.get("content-length", "0") or 0)
                body = json.loads((await reader.readexactly(n)).decode() or "{}") if n else {}
                if body.get("id"):
                    self.on_select(str(body["id"]))
                await self._send(writer, 204, b"", "text/plain")
            else:
                await self._send(writer, 404, b"not found", "text/plain")
        except Exception as e:
            try:
                await self._send(writer, 500, str(e).encode(), "text/plain")
            except Exception:
                pass

    async def _send(self, writer, code: int, body: bytes, ctype: str) -> None:
        reason = {200: "OK", 204: "No Content", 404: "Not Found", 500: "Server Error"}.get(code, "OK")
        writer.write(f"HTTP/1.1 {code} {reason}\r\nContent-Type: {ctype}\r\nContent-Length: {len(body)}\r\n"
                     f"Cache-Control: no-store\r\nConnection: close\r\n\r\n".encode() + body)
        await writer.drain()
        writer.close()

    async def _events(self, writer) -> None:
        q: asyncio.Queue = asyncio.Queue()
        self.subs.append(q)
        writer.write(b"HTTP/1.1 200 OK\r\nContent-Type: text/event-stream\r\nCache-Control: no-store\r\nConnection: keep-alive\r\n\r\n")
        await writer.drain()
        try:
            while True:
                try:
                    msg = await asyncio.wait_for(q.get(), timeout=15)
                    writer.write(f"data: {json.dumps(msg)}\n\n".encode())
                except asyncio.TimeoutError:
                    writer.write(b": keep-alive\n\n")
                await writer.drain()
        except Exception:
            pass
        finally:
            self.subs.remove(q)
            writer.close()


def payload_for(inv, case_json: dict | None) -> dict:
    """The recorded graph of an investigation plus which edges belong to which explanation."""
    g = ((case_json or {}).get("search", {}).get("groups") or [{}])[0].get("graph") or {}
    nodes, edges = list(g.get("nodes", [])), list(g.get("edges", []))
    trees, expl = {}, []
    for e in sorted(inv.explanations, key=lambda e: (e.rank == 0, e.rank)):
        tag = "best" if e.rank == 1 else ("abstain" if e.rank == 0 else f"rival{e.rank}")
        trees[tag] = [[x.src, x.dst] for x in e.edges]
        expl.append({"tag": tag, "rank": e.rank, "entry": e.entry, "label": e.entry_label, "cost": e.cost_mnats,
                     "odds": e.odds_vs_best, "p": {f"{x.src}>{x.dst}": x.p for x in e.edges}})
    if not nodes:                                         # no recorded graph (DEMO or an older case file): the trees alone
        seen = {}
        for e in inv.explanations:
            for x in e.edges:
                for nid, lab in ((x.src, x.src_label), (x.dst, x.dst_label)):
                    kind = "bot" if nid == "BOT" else ("terminal" if nid.startswith("T") and nid[1:].isdigit() else "narrative")
                    seen.setdefault(nid, {"id": nid, "kind": kind, "label": lab if kind == "narrative" else nid, "state": ""})
                if x.src != "BOT" or not x.dst.startswith("T") or x.p:
                    edges.append({"u": x.src, "v": x.dst, "p": x.p, "cost": x.cost_mnats})
        for k, c in enumerate(inv.clusters):
            if f"T{k}" in seen:
                seen[f"T{k}"]["label"] = ", ".join(c)
        nodes = list(seen.values())
    return {"title": f"CASE {inv.case_id} · {inv.source} · τ* {inv.tau_star:%Y-%m-%d %H:%M} UTC" if inv.tau_star else f"CASE {inv.case_id}",
            "nodes": nodes, "edges": edges, "trees": trees, "expl": expl, "recorded_graph": bool(g.get("nodes")),
            "terminal_names": {f"T{k}": ", ".join(c) for k, c in enumerate(inv.clusters)}}
