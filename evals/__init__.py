"""Deterministic eval framework for the MySQL MCP server.

Drives the server as a real MCP client (over stdio) against a real, seeded MySQL
database and scores each tool/resource against known expected results. Gated:
when MySQL is unreachable the suite skips cleanly instead of failing.
"""
