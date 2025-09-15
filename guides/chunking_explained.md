# Chunk size & overlap — explained

- **Chunk size** = maximum token length per embedding vector.
- **Overlap** = how many tokens from the end of one chunk are repeated at the start of the next chunk to preserve context across boundaries.

Examples:
- size=200, overlap=50 → Chunk1: 1–200, Chunk2: 151–350, Chunk3: 301–500…

Rules of thumb:
- <300 tokens per section → 400/40
- 300–1000 → 600–800 with 15–20% overlap
- >1000 → 1000–1500 with 20–30% overlap
