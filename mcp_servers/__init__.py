"""MCP servers this project exposes, and the ones it bolts on.

Each file here is a standalone process. It speaks JSON-RPC over stdin and
stdout, and it has no idea which AI is calling it, or whether one is at all.
That separation is the whole point of the protocol: the server offers
capabilities, the host decides what to do with them.
"""
