# Vector Store Guide

## Chunking (recommended)
- **Chunk size:** 400 tokens
- **Overlap:** 40 tokens

### When to increase chunk size?
- Long, tightly connected chapters (whitepapers) → 800–1200
- Heavy cross‑references in one section → 800+
- Code/log blocks that must not be split → 800+
- For hundreds of mini‑docs (this repo) → 400/40 is optimal
