with open('docs/architecture.md', 'r') as f:
    content = f.read()

# Update LLMClient description
old1 = 'LLM["LLMClient<br/>OpenAI or Anthropic if valid key;<br/>MockProvider fallback; retries + timeout"]'
new1 = 'LLM["LLMClient<br/>Llm7Provider (free, OpenAI-compatible) / OpenAI / Anthropic if valid key;<br/>MockProvider fallback; retries + timeout"]'
content = content.replace(old1, new1)

# Update LLM provider diagram
old2 = 'LLM -.->|"real API call (server-side key)"| EXT["LLM provider<br/>OpenAI GPT-4o-mini or<br/>Anthropic Claude 3 Haiku"]'
new2 = 'LLM -.->|"real API call (server-side key, free tier first)"| EXT["LLM provider<br/>LLM7.io free tier (GPT-4o-mini)<br/>or OpenAI / Anthropic"]'
content = content.replace(old2, new2)

# Update AI workflow text
old3 = '- **Invoked by LLM (when a valid key is configured server-side):** free-text explanation/summary generation only (`gpt-4o-mini` or `claude-3-haiku`, JSON mode, temperature 0.1).'
new3 = '- **Free LLM provider (production default):** LLM7.io — OpenAI-compatible, GPT-4o-mini on free tier, 30 RPM, email signup only, no credit card required\n- **Invoked by LLM (when a valid key is configured server-side):** free-text explanation/summary generation only (`gpt-4o-mini` or `claude-3-haiku`, JSON mode, temperature 0.1).'
content = content.replace(old3, new3)

# Update MockProvider fallback
old4 = '- **MockProvider fallback:** if no valid `OPENAI_API_KEY`/`ANTHROPIC_API_KEY` is present (missing, placeholder `test-` prefix, or <= 20 chars), responses are explicitly labeled mock text.'
new4 = '- **MockProvider fallback:** if no valid `LLM7_API_KEY`/`OPENAI_API_KEY`/`ANTHROPIC_API_KEY` is present (missing, placeholder `test-` prefix, or <= 20 chars), responses are explicitly labeled mock text.'
content = content.replace(old4, new4)

# Update External Services
old5 = '| OpenAI API *or* Anthropic API | Chat completion (only when a valid key is configured) |'
new5 = '| LLM7.io free tier (GPT-4o-mini, OpenAI-compatible) / OpenAI API *or* Anthropic API | Chat completion (only when a valid key is configured) |'
content = content.replace(old5, new5)

with open('docs/architecture.md', 'w') as f:
    f.write(content)
print('Done')