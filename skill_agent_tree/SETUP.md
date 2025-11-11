# Skill Agent Tree Configuration Example

## Environment Setup

### 1. Create a virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

### 2. Install dependencies
pip install -r requirements.txt

### 3. Set up environment variables
export DASHSCOPE_API_KEY="sk-xxx..."
# Or add to .env file:
# DASHSCOPE_API_KEY=sk-xxx...

## Quick Start

### Run the test suite
python test.py

### Run the interactive system
python main.py

## Configuration Options

### Model Provider Configuration

#### DashScope (Default)
```python
from agentscope.model import DashScopeChatModel

model = DashScopeChatModel(
    model_name="gpt-4-turbo-preview",
    api_key="your-api-key",
    stream=True
)
```

#### Alibaba Cloud DashScope
```python
from agentscope.model import DashScopeChatModel

model = DashScopeChatModel(
    model_name="qwen-max",
    api_key="your-api-key"
)
```

#### Anthropic Claude
```python
from agentscope.model import AnthropicChatModel

model = AnthropicChatModel(
    model_name="claude-3-sonnet-20240229",
    api_key="your-api-key"
)
```

### Formatter Configuration
```python
from agentscope.formatter import (
    DashScopeChatFormatter,
    DashScopeChatFormatter,
    AnthropicChatFormatter
)
```

### Memory Configuration
```python
from agentscope.memory import InMemoryMemory

# Default in-memory storage
memory = InMemoryMemory()

# Can be extended with:
# - Long-term memory (Mem0, ReME)
# - Database backends
# - Vector stores for RAG
```

## Directory Structure After Setup

```
skill_agent_tree/
├── __init__.py
├── tree_node_agent.py      # Core agent class
├── agent_tree.py           # Tree management
├── main.py                 # Entry point
├── test.py                 # Tests
├── requirements.txt
├── pyproject.toml
├── README.md
├── .gitignore
├── .env                    # Local environment variables (not in git)
└── logs/                   # Created at runtime
    └── skill_agent_tree.log
```

## Troubleshooting

### ImportError: No module named 'agentscope'
Solution: Install agentscope
```bash
pip install agentscope
```

### DashScope API Error
- Check DASHSCOPE_API_KEY is set correctly
- Verify API key has necessary permissions
- Check API usage limits

### Memory Issues with Large Conversation Histories
- Consider implementing long-term memory
- Implement memory summarization
- Use vector stores for semantic search

## Performance Tips

1. **Use streaming**: Set `stream=True` in model configuration for lower latency
2. **Parallel execution**: Enable `parallel_tool_calls` for concurrent operations
3. **Caching**: Implement caching for frequently used skills
4. **Batching**: Group similar tasks for efficiency

## Next Steps

1. Customize system prompts for your domain
2. Add domain-specific tools to the toolkit
3. Implement persistent storage for skills
4. Set up monitoring and logging
5. Deploy to production environment

## Support & Documentation

- AgentScope Docs: https://modelscope.github.io/agentscope/
- GitHub Issues: Report bugs and feature requests
- Community: Join our discussions

## License
MIT
