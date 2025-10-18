from dotenv import load_dotenv
from mcp import ClientSession, StdioServerParameters, types
from mcp.client.stdio import stdio_client
from typing import List, Dict, TypedDict
import asyncio
import nest_asyncio
import json
from contextlib import AsyncExitStack

# Apply nest_asyncio to allow nested event loops (useful in Jupyter notebooks)
nest_asyncio.apply()

# Load environment variables from .env file
load_dotenv()

from groq import Groq
import os

# Set Groq API key from environment variable
os.environ["GROQ_API_KEY"] = os.getenv("groq")


class ToolDefinition(TypedDict):
    """Type definition for tool schema used by Groq API"""
    name: str
    description: str
    input_schema: dict


class MCP_Chatbot:
    """
    MCP Chatbot that connects to multiple MCP servers and uses LLM for processing.
    
    This chatbot:
    1. Connects to multiple MCP servers (filesystem, research, fetch, etc.)
    2. Collects all available tools from these servers
    3. Uses Groq LLM to decide which tools to call
    4. Executes tools and returns results
    """
    
    def __init__(self):
        """Initialize the chatbot with empty collections for sessions and tools"""
        # List to store all active MCP client sessions (one per server)
        self.session: List[ClientSession] = []
        
        # AsyncExitStack manages async context managers (sessions, connections)
        # WHY: It allows us to open multiple async connections and cleanly close them all at once
        # Without it, we'd need nested 'async with' statements for each server
        self.exit_stack = AsyncExitStack()
        
        # Groq LLM client for processing queries and deciding tool usage
        self.client = Groq()
        
        # List of all available tools from all connected MCP servers
        self.available_tools: List[ToolDefinition] = []
        
        # Maps tool names to their respective sessions
        # WHY: When LLM decides to use a tool, we need to know which server to call
        self.tool_to_session: Dict[str, ClientSession] = {}
        
    async def process_query(self, query):
        """
        Process user query using LLM and execute any required tools.
        
        Flow:
        1. Send query to LLM with available tools
        2. If LLM wants to use a tool, execute it
        3. Send tool results back to LLM for final answer
        """
        # Prepare messages for LLM
        messages = [
            {
                "role": "system",
                "content": "You are a helpful research assistant. When you need to use tools, call them with proper function calling syntax.",
            },
            {"role": "user", "content": query},
        ]

        try:
            # Step 1: Get initial response from LLM
            # LLM will decide if it needs to use any tools
            response = self.client.chat.completions.create(
                model="llama-3.3-70b-versatile",
                messages=messages,
                tools=self.available_tools,  # Provide all available tools
                max_tokens=2024,
                tool_choice="auto",  # Let LLM decide when to use tools
            )

            message = response.choices[0].message
            
            # If LLM responds with text (no tool needed), print it
            if message.content:
                print(f"Assistant: {message.content}")

            # Step 2: Check if LLM wants to use any tools
            if hasattr(message, "tool_calls") and message.tool_calls:
                for tool_call in message.tool_calls:
                    try:
                        # Extract which tool to call and with what arguments
                        tool_name = tool_call.function.name
                        tool_args = json.loads(tool_call.function.arguments)

                        print(f"\nExecuting {tool_name} with arguments: {tool_args}")
                        
                        # Step 3: Find the correct MCP server session for this tool
                        session = self.tool_to_session.get(tool_name)
                        if session:
                            # Execute the tool on the appropriate MCP server
                            result = await session.call_tool(tool_name, tool_args)
                        else:
                            print(f"No session found for tool {tool_name}")
                            continue
                        
                        # Step 4: Add tool execution to conversation history
                        # This tells LLM: "You called this tool, here's what it returned"
                        messages.extend([
                            {
                                "role": "assistant",
                                "content": None,
                                "tool_calls": [{
                                    "id": tool_call.id,
                                    "type": "function",
                                    "function": {
                                        "name": tool_name,
                                        "arguments": json.dumps(tool_args),
                                    },
                                }],
                            },
                            {
                                "role": "tool",
                                "content": str(result),
                                "tool_call_id": tool_call.id,
                            },
                        ])

                        # Step 5: Get final response from LLM with tool results
                        final_response = self.client.chat.completions.create(
                            model="llama-3.3-70b-versatile",
                            messages=messages,
                            max_tokens=2024,
                        )

                        if final_response.choices[0].message.content:
                            print(f"\nAssistant: {final_response.choices[0].message.content}")

                    except Exception as e:
                        print(f"Error executing tool {tool_name}: {str(e)}")

        except Exception as e:
            print(f"Error in processing query: {str(e)}")
    
    async def chat_loop(self):
        """Run an interactive chat loop for continuous conversation"""
        print("\nMCP Chatbot Started!")
        print("Type your queries or 'quit' to exit.")
        
        while True:
            try:
                query = input("\nQuery: ").strip()
        
                if query.lower() == 'quit':
                    break
                    
                await self.process_query(query)
                print("\n")
                    
            except Exception as e:
                print(f"\nError: {str(e)}")
    
    async def cleanup(self):
        """
        Cleanly close all resources using AsyncExitStack.
        
        WHY AsyncExitStack.aclose():
        - Closes ALL async context managers in reverse order
        - Ensures no hanging connections or processes
        - Prevents resource leaks
        """
        await self.exit_stack.aclose()
        
    async def connect_to_server(self, server_name, server_config):
        """
        Connect to a single MCP Server and register its tools.
        
        AsyncExitStack Usage:
        1. enter_async_context() - Similar to 'async with' but manual control
        2. Keeps connection alive for entire program lifecycle
        3. Will be closed when exit_stack.aclose() is called
        """
        try:
            # Create server parameters from config (command, args, env vars)
            server_params = StdioServerParameters(**server_config)
            
            # Start the MCP server process and establish stdio communication
            # WHY exit_stack: Keeps this connection alive and manages cleanup
            stdio_transport = await self.exit_stack.enter_async_context(
                stdio_client(server_params)
            )
            
            # Get read/write streams for communication
            read, write = stdio_transport
            
            # Create MCP client session for this server
            # WHY exit_stack: Session needs to stay open for entire program
            session = await self.exit_stack.enter_async_context(
                ClientSession(read, write)
            )
            
            # Initialize the MCP protocol handshake
            await session.initialize()
            
            # Store session for later use
            self.session.append(session)
            
            # Get list of tools this server provides
            response = await session.list_tools()
            tools = response.tools
            
            print(f"\nConnected to {server_name} with tools:", [t.name for t in tools])
            
            # Register each tool for LLM usage
            for tool in tools:
                # Map tool name to its session (so we know where to execute it)
                self.tool_to_session[tool.name] = session
                
                # Format tool for Groq API
                self.available_tools.append({
                    "type": "function",
                    "function": {
                        "name": tool.name,
                        "description": tool.description,
                        "parameters": tool.inputSchema,
                    },
                })
                
        except Exception as e:
            print(f"Failed to connect to {server_name}: {e}")

    async def connect_to_servers(self):
        """
        Connect to all configured MCP servers from server_config.json
        
        This method:
        1. Reads server configurations
        2. Connects to each server
        3. Collects all tools from all servers
        """
        try:
            # Load server configurations
            with open("server_config.json", "r") as file:
                data = json.load(file)
            
            servers = data.get("mcpServers", {})
            
            # Connect to each server sequentially
            for server_name, server_config in servers.items():
                await self.connect_to_server(server_name, server_config)
                
        except Exception as e:
            print(f"Error loading server configuration: {e}")
            raise


async def main():
    """
    Main entry point for the chatbot.
    
    Flow:
    1. Create chatbot instance
    2. Connect to all MCP servers
    3. Start interactive chat loop
    4. Cleanup all connections on exit
    """
    chatbot = MCP_Chatbot()
    try:
        # Connect to all servers and collect their tools
        await chatbot.connect_to_servers()
        
        # Start interactive chat
        await chatbot.chat_loop()
        
    finally:
        # Always cleanup, even if error occurs
        # This closes all MCP server connections cleanly
        await chatbot.cleanup()


if __name__ == "__main__":
    asyncio.run(main())


