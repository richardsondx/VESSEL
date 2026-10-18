# evidence8-agent

Agent-mode Evidence8: an OpenAI model (gpt-4o-mini) reformulates the raw query
into 2-3 targeted keyword searches, each executed through the hosted MCP
`search_visual_evidence` tool, with results merged and deduplicated.

This mirrors the architecture of Evidence8's in-app Research Chat (LLM
connected to Evidence via MCP). It is a distinct retrieval path from the
plain `evidence8` provider (single deterministic lexical search) and is
reported separately.

- Transport: hosted MCP at `https://evidence8.com/mcp` (JSON-RPC `tools/call`).
- Auth: `Authorization: Bearer <EVIDENCE8_API_KEY>` for MCP; the OpenAI
  credential comes from the `custom.openai` connector (never from `.env`).
- Cost: 1 Evidence8 credit per successful MCP search (no-match is free);
  OpenAI reformulation is a few cents per 1k queries on gpt-4o-mini.
- Env: `EVIDENCE8_API_KEY` (same as the direct provider).
