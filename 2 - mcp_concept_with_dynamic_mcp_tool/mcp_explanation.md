# MCP Chatbot - Detailed Explanation

## Table of Contents
1. [Overview](#overview)
2. [Why AsyncExitStack?](#why-asyncexitstack)
3. [Architecture](#architecture)
4. [Server Configuration](#server-configuration)
5. [How It Works](#how-it-works)
6. [Code Flow Diagram](#code-flow-diagram)

---

## Overview

This MCP (Model Context Protocol) Chatbot connects to multiple external servers, collects their tools, and uses an LLM (Groq) to intelligently decide when and how to use these tools based on user queries.

**Key Components:**
- **MCP Servers**: External services that provide tools (filesystem operations, research, web fetching, etc.)
- **MCP Client**: Our chatbot that connects to these servers
- **LLM (Groq)**: Decides which tools to use based on user queries
- **AsyncExitStack**: Manages multiple async connections cleanly

---

## Why AsyncExitStack?

### The Problem Without AsyncExitStack

Imagine you need to connect to 4 different MCP servers. Without `AsyncExitStack`, your code would look like this:

```python
async def connect():
    async with stdio_client(server1) as transport1:
        async with ClientSession(transport1[0], transport1[1]) as session1:
            async with stdio_client(server2) as transport2:
                async with ClientSession(transport2[0], transport2[1]) as session2:
                    async with stdio_client(server3) as transport3:
                        async with ClientSession(transport3[0], transport3[1]) as session3:
                            # Now you can finally use all sessions!
                            # But this is HORRIBLE nesting!
```

**Problems:**
- ❌ Deeply nested code (pyramid of doom)
- ❌ Hard to add/remove servers dynamically
- ❌ Difficult to manage cleanup if one connection fails
- ❌ Can't loop through servers - must hardcode each one

### The Solution: AsyncExitStack

```python
async def connect():
    exit_stack = AsyncExitStack()
    
    for server_config in servers:
        # Add each connection to the stack
        transport = await exit_stack.enter_async_context(stdio_client(server))
        session = await exit_stack.enter_async_context(ClientSession(...))
        # All connections stay open!
    
    # Later, close everything at once:
    await exit_stack.aclose()  # Closes ALL connections in reverse order
```

**Benefits:**
- ✅ Flat, readable code
- ✅ Dynamic - can add servers in a loop
- ✅ Automatic cleanup in reverse order
- ✅ Handles errors gracefully
- ✅ All connections stay open until we explicitly close them

### How AsyncExitStack Works

Think of `AsyncExitStack` as a **stack of cleanup tasks**:

```
┌─────────────────────────────┐
│  Session 3 (last opened)    │  ← Will close FIRST
├─────────────────────────────┤
│  Transport 3                │
├─────────────────────────────┤
│  Session 2                  │
├─────────────────────────────┤
│  Transport 2                │
├─────────────────────────────┤
│  Session 1                  │
├─────────────────────────────┤
│  Transport 1 (first opened) │  ← Will close LAST
└─────────────────────────────┘

When you call: await exit_stack.aclose()
Everything closes from top to bottom (LIFO - Last In First Out)
```

**Why Reverse Order Matters:**
- Sessions depend on transports
- Must close session BEFORE closing its transport
- AsyncExitStack handles this automatically

---

## Architecture

```
┌──────────────────────────────────────────────────────────────┐
│                         USER                                  │
└────────────────────────┬─────────────────────────────────────┘
                         │ Query: "Search for AI papers"
                         ▼
┌──────────────────────────────────────────────────────────────┐
│                    MCP_Chatbot                                │
│  ┌────────────────────────────────────────────────────────┐  │
│  │  1. Process Query with Groq LLM                        │  │
│  │     - LLM sees all available tools                     │  │
│  │     - Decides which tool(s) to use                     │  │
│  └────────────────────────────────────────────────────────┘  │
│                         │                                     │
│                         │ LLM decides: use "search_papers"    │
│                         ▼                                     │
│  ┌────────────────────────────────────────────────────────┐  │
│  │  2. Look up tool in tool_to_session mapping           │  │
│  │     tool_to_session["search_papers"] → research_session│  │
│  └────────────────────────────────────────────────────────┘  │
│                         │                                     │
│                         ▼                                     │
│  ┌────────────────────────────────────────────────────────┐  │
│  │  3. Execute tool on correct MCP server                 │  │
│  │     await research_session.call_tool(...)              │  │
│  └────────────────────────────────────────────────────────┘  │
└────────────────────────┬─────────────────────────────────────┘
                         │
                         ▼
┌──────────────────────────────────────────────────────────────┐
│                    MCP SERVERS                                │
│                                                               │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐       │
│  │ Filesystem   │  │  Research    │  │    Fetch     │       │
│  │   Server     │  │   Server     │  │   Server     │       │
│  ├──────────────┤  ├──────────────┤  ├──────────────┤       │
│  │ • read_file  │  │ • search     │  │ • fetch_url  │       │
│  │ • write_file │  │ • extract    │  │              │       │
│  │ • list_dir   │  │ • weather    │  │              │       │
│  └──────────────┘  └──────────────┘  └──────────────┘       │
└──────────────────────────────────────────────────────────────┘
```

---

## Server Configuration

### server_config.json

This file defines which MCP servers to connect to and how to start them.

```json
{
    "mcpServers": {
        "filesystem": {
            "command": "npx",
            "args": [
                "-y",
                "@modelcontextprotocol/server-filesystem",
                "C:/Users/GAURAV/Desktop"
            ]
        },
        "research": {
            "command": "python",
            "args": ["research_server.py"]
        },
        "fetch": {
            "command": "uvx",
            "args": ["mcp-server-fetch"]
        },
        "sequential-thinking": {
            "command": "npx",
            "args": [
                "-y",
                "@modelcontextprotocol/server-sequential-thinking"
            ]
        }
    }
}
```

### Understanding Each Server

#### 1. **Filesystem Server**
```json
"filesystem": {
    "command": "npx",
    "args": ["-y", "@modelcontextprotocol/server-filesystem", "C:/Users/GAURAV/Desktop"]
}
```

- **Command**: `npx` - Node.js package runner
- **Package**: `@modelcontextprotocol/server-filesystem` - Official MCP filesystem server
- **Flag**: `-y` - Automatically install if not present
- **Directory**: `C:/Users/GAURAV/Desktop` - The directory this server can access
- **Tools Provided**: read_file, write_file, list_directory, etc.

**Why**: Allows LLM to read/write files on your computer

---

#### 2. **Research Server**
```json
"research": {
    "command": "python",
    "args": ["research_server.py"]
}
```

- **Command**: `python` - Python interpreter
- **Script**: `research_server.py` - Your custom MCP server
- **Tools Provided**: search_papers, extract_info, get_weather, etc.

**Why**: Custom tools you built for research tasks

---

#### 3. **Fetch Server**
```json
"fetch": {
    "command": "uvx",
    "args": ["mcp-server-fetch"]
}
```

- **Command**: `uvx` - UV package runner (like pipx)
- **Package**: `mcp-server-fetch` - HTTP fetching server
- **Tools Provided**: fetch (to get web page content)

**Why**: Allows LLM to fetch content from URLs

---

#### 4. **Sequential Thinking Server**
```json
"sequential-thinking": {
    "command": "npx",
    "args": ["-y", "@modelcontextprotocol/server-sequential-thinking"]
}
```

- **Command**: `npx` - Node.js package runner
- **Package**: `@modelcontextprotocol/server-sequential-thinking`
- **Tools Provided**: Think through problems step-by-step

**Why**: Helps LLM break down complex problems

---

## How It Works

### Step-by-Step Flow

#### 1. **Initialization**
```python
chatbot = MCP_Chatbot()
await chatbot.connect_to_servers()
```

**What Happens:**
- Reads `server_config.json`
- For each server:
  - Starts the server process (npx, python, uvx commands)
  - Creates communication channels (stdin/stdout)
  - Establishes MCP client session
  - Asks server: "What tools do you have?"
  - Stores tools in `available_tools` list
  - Maps each tool to its server session

**Result:**
```python
available_tools = [
    {"name": "read_file", "description": "...", ...},
    {"name": "search_papers", "description": "...", ...},
    {"name": "fetch", "description": "...", ...},
    # ... all tools from all servers
]

tool_to_session = {
    "read_file": filesystem_session,
    "search_papers": research_session,
    "fetch": fetch_session,
    # ...
}
```

---

#### 2. **User Query**
```python
query = "Search for papers on transformers and save results to file"
```

**What Happens:**
- Query sent to Groq LLM with ALL available tools
- LLM analyzes: "I need to search papers, then write to file"
- LLM returns tool calls:
  ```json
  [
      {"name": "search_papers", "args": {"query": "transformers"}},
      {"name": "write_file", "args": {"path": "results.txt", "content": "..."}}
  ]
  ```

---

#### 3. **Tool Execution**
```python
for tool_call in message.tool_calls:
    tool_name = "search_papers"
    
    # Find which server has this tool
    session = tool_to_session["search_papers"]  # → research_session
    
    # Execute on that server
    result = await session.call_tool("search_papers", {"query": "transformers"})
```

**What Happens:**
- Look up tool in mapping
- Call the correct MCP server
- Get results back
- Send results to LLM for final response

---

#### 4. **Final Response**
```python
# Send tool results back to LLM
messages.append({
    "role": "tool",
    "content": "Found 10 papers on transformers..."
})

# LLM generates final answer
final_response = client.chat.completions.create(...)
print("I found 10 papers on transformers and saved them to results.txt")
```

---

## Code Flow Diagram

```
┌─────────────────────────────────────────────────────────────┐
│                    PROGRAM START                             │
└────────────────────────┬────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────┐
│  main()                                                      │
│  • Create MCP_Chatbot instance                               │
│  • Initialize AsyncExitStack                                 │
└────────────────────────┬────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────┐
│  connect_to_servers()                                        │
│  • Read server_config.json                                   │
│  • For each server:                                          │
│    └─► connect_to_server()                                   │
│         • Start server process                               │
│         • Create session (via exit_stack)                    │
│         • List tools                                         │
│         • Store in available_tools                           │
└────────────────────────┬────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────┐
│  chat_loop()                                                 │
│  • Display prompt                                            │
│  • Wait for user input                                       │
└────────────────────────┬────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────┐
│  process_query(query)                                        │
│  ┌─────────────────────────────────────────────────────┐    │
│  │ 1. Send to Groq LLM with all tools                  │    │
│  └────────────────────┬────────────────────────────────┘    │
│                       │                                      │
│                       ▼                                      │
│  ┌─────────────────────────────────────────────────────┐    │
│  │ 2. LLM decides: need tools? ───────────┐            │    │
│  └───────────────┬─────────────────────────┘            │    │
│                  │                                      │    │
│         YES ◄────┤                                      │    │
│          │       │                                      │    │
│          │       └─► NO: Return text answer            │    │
│          ▼                                                   │
│  ┌─────────────────────────────────────────────────────┐    │
│  │ 3. For each tool_call:                              │    │
│  │    • Look up session in tool_to_session             │    │
│  │    • Execute: await session.call_tool()             │    │
│  │    • Collect results                                │    │
│  └────────────────────┬────────────────────────────────┘    │
│                       │                                      │
│                       ▼                                      │
│  ┌─────────────────────────────────────────────────────┐    │
│  │ 4. Send tool results back to LLM                    │    │
│  │    • Get final natural language response            │    │
│  └─────────────────────────────────────────────────────┘    │
└────────────────────────┬────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────┐
│  cleanup()                                                   │
│  • await exit_stack.aclose()                                 │
│  • Closes all sessions in reverse order                      │
│  • Closes all server processes                               │
└─────────────────────────────────────────────────────────────┘
```

---

## Key Concepts Summary

### 1. AsyncExitStack Benefits
- **Manages multiple async connections** without nesting
- **Ensures clean shutdown** of all resources
- **LIFO order** (Last In, First Out) for safe cleanup
- **Error-safe** - closes everything even if errors occur

### 2. Tool Mapping
- `tool_to_session` dictionary maps tool names to server sessions
- When LLM says "use search_papers", we know which server to call
- Allows dynamic server management

### 3. LLM Decision Making
- LLM sees ALL available tools from ALL servers
- Decides autonomously which tools to use
- Can chain multiple tools together
- Returns natural language responses

### 4. Server Configuration
- JSON file defines all servers
- Easy to add/remove servers
- Each server provides its own tools
- Tools are automatically discovered

---

## Adding New Servers

To add a new MCP server:

1. **Add to server_config.json**:
```json
{
    "mcpServers": {
        "my-new-server": {
            "command": "python",
            "args": ["my_server.py"]
        }
    }
}
```

2. **Run the chatbot** - it will automatically:
   - Connect to the new server
   - Discover its tools
   - Make them available to the LLM

3. **That's it!** No code changes needed.

---

## Troubleshooting

### Server Won't Connect
- Check command path (npx, python, uvx)
- Verify server script exists
- Check permissions on directories

### Tool Not Being Called
- Verify tool is in `available_tools`
- Check tool description is clear
- Ensure LLM model supports function calling

### Connection Issues
- AsyncExitStack automatically handles cleanup
- Check if server process is running
- Look for error messages in console

---

## Summary

This MCP Chatbot architecture provides:
- ✅ **Modular design** - easy to add/remove servers
- ✅ **Clean resource management** - AsyncExitStack handles cleanup
- ✅ **Intelligent tool usage** - LLM decides what to call
- ✅ **Scalable** - supports unlimited servers and tools
- ✅ **Error-safe** - handles failures gracefully

The key innovation is using **AsyncExitStack** to manage multiple server connections without nested code, making the system maintainable and extensible.
