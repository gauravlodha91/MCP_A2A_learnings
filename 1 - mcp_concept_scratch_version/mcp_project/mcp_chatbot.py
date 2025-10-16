from dotenv import load_dotenv

from mcp import ClientSession, StdioServerParameters, types
from mcp.client.stdio import stdio_client
from typing import List
import asyncio
import nest_asyncio
import json

nest_asyncio.apply()

load_dotenv()
from groq import Groq

import os

os.environ["GROQ_API_KEY"] = os.getenv("groq")


class MCP_ChatBot:
    def __init__(self):
        # Initialize session and client objects
        self.session: ClientSession = None
        self.client = Groq()
        self.available_tools: List[dict] = []

    async def process_query(self, query):
        messages = [
            {
                "role": "system",
                "content": "You are a helpful research assistant. When you need to use tools, call them with proper function calling syntax.",
            },
            {"role": "user", "content": query},
        ]

        try:
            # Initial response
            response = self.client.chat.completions.create(
                model="llama-3.3-70b-versatile",  # Better model for function calling
                messages=messages,
                tools=self.available_tools,
                max_tokens=2024,
                tool_choice="auto",
            )

            message = response.choices[0].message
            
            print("============================================================")
            print()
            print("message :: " , message)
            print("============================================================")

            # Handle the message content if present
            if message.content:
                print(f"Assistant: {message.content}")

            # Handle tool calls if present
            if hasattr(message, "tool_calls") and message.tool_calls:
                for tool_call in message.tool_calls:
                    try:
                        # Extract tool details
                        tool_name = tool_call.function.name
                        tool_args = json.loads(tool_call.function.arguments)

                        # Execute the tool
                        print(f"\nExecuting {tool_name} with arguments: {tool_args}")
                        result = await self.session.call_tool(tool_name, tool_args)

                        # Add the tool result to messages
                        messages.extend(
                            [
                                {
                                    "role": "assistant",
                                    "content": None,
                                    "tool_calls": [
                                        {
                                            "id": tool_call.id,
                                            "type": "function",
                                            "function": {
                                                "name": tool_name,
                                                "arguments": json.dumps(tool_args),
                                            },
                                        }
                                    ],
                                },
                                {
                                    "role": "tool",
                                    "content": str(result),
                                    "tool_call_id": tool_call.id,
                                },
                            ]
                        )

                        # Get final response after tool execution
                        final_response = self.client.chat.completions.create(
                            model="llama-3.3-70b-versatile",
                            messages=messages,
                            max_tokens=2024,
                        )

                        if final_response.choices[0].message.content:
                            print(
                                f"\nAssistant: {final_response.choices[0].message.content}"
                            )

                    except Exception as e:
                        print(f"Error executing tool {tool_name}: {str(e)}")

        except Exception as e:
            print(f"Error in processing query: {str(e)}")

    async def chat_loop(self):
        """Run an interactive chat loop"""
        print("\nMCP Chatbot Started!")
        print("Type your queries or 'quit' to exit.")

        while True:
            try:
                query = input("\nQuery: ").strip()

                if query.lower() == "quit":
                    break

                await self.process_query(query)
                print("\n")

            except Exception as e:
                print(f"\nError: {str(e)}")

    async def connect_to_server_and_run(self):
        # Create server parameters for stdio connection
        server_params = StdioServerParameters(
            command="python", args=["research_server.py"], env=None
        )
        async with stdio_client(server_params) as (read, write):
            async with ClientSession(read, write) as session:
                self.session = session
                # Initialize the connection
                await session.initialize()

                # List available tools
                response = await session.list_tools()

                print("\nAvailable tools from server:", response.tools)

                tools = response.tools
                print(
                    "\nConnected to server with tools:", [tool.name for tool in tools]
                )

                # FIXED: Format tools correctly for Groq API
                self.available_tools = [
                    {
                        "type": "function",  # Add the required 'type' field
                        "function": {
                            "name": tool.name,
                            "description": tool.description,
                            "parameters": tool.inputSchema,  # Use 'parameters' instead of 'input_schema'
                        },
                    }
                    for tool in response.tools
                ]

                await self.chat_loop()


async def main():
    chatbot = MCP_ChatBot()
    await chatbot.connect_to_server_and_run()


if __name__ == "__main__":
    asyncio.run(main())


"""

wrong code :: 
self.available_tools = [{
    "name": tool.name,
    "description": tool.description,
    "input_schema": tool.inputSchema
} for tool in response.tools]


to this 
self.available_tools = [{
    "type": "function",
    "function": {
        "name": tool.name,
        "description": tool.description,
        "parameters": tool.inputSchema
    }
} for tool in response.tools]


"""
