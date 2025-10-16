import arxiv
import json
import os
from typing import List
from mcp.server.fastmcp import FastMCP


PAPER_DIR = "papers"

# Initialize FastMCP server
mcp = FastMCP("research")


@mcp.tool()
def search_papers(topic: str, max_results: int = 5) -> List[str]:
    """
    Search for papers on arXiv based on a topic and store their information.

    Args:
        topic: The topic to search for
        max_results: Maximum number of results to retrieve (default: 5)

    Returns:
        List of paper IDs found in the search
    """

    # Use arxiv to find the papers
    client = arxiv.Client()

    # Search for the most relevant articles matching the queried topic
    search = arxiv.Search(
        query=topic, max_results=max_results, sort_by=arxiv.SortCriterion.Relevance
    )

    papers = client.results(search)

    # Create directory for this topic
    path = os.path.join(PAPER_DIR, topic.lower().replace(" ", "_"))
    os.makedirs(path, exist_ok=True)

    file_path = os.path.join(path, "papers_info.json")

    # Try to load existing papers info
    try:
        with open(file_path, "r") as json_file:
            papers_info = json.load(json_file)
    except (FileNotFoundError, json.JSONDecodeError):
        papers_info = {}

    # Process each paper and add to papers_info
    paper_ids = []
    for paper in papers:
        paper_ids.append(paper.get_short_id())
        paper_info = {
            "title": paper.title,
            "authors": [author.name for author in paper.authors],
            "summary": paper.summary,
            "pdf_url": paper.pdf_url,
            "published": str(paper.published.date()),
        }
        papers_info[paper.get_short_id()] = paper_info

    # Save updated papers_info to json file
    with open(file_path, "w") as json_file:
        json.dump(papers_info, json_file, indent=2)

    print(f"Results are saved in: {file_path}")

    return paper_ids


@mcp.tool()
def extract_info(paper_id: str) -> str:
    """
    Search for information about a specific paper across all topic directories.

    Args:
        paper_id: The ID of the paper to look for

    Returns:
        JSON string with paper information if found, error message if not found
    """

    for item in os.listdir(PAPER_DIR):
        item_path = os.path.join(PAPER_DIR, item)
        if os.path.isdir(item_path):
            file_path = os.path.join(item_path, "papers_info.json")
            if os.path.isfile(file_path):
                try:
                    with open(file_path, "r") as json_file:
                        papers_info = json.load(json_file)
                        if paper_id in papers_info:
                            return json.dumps(papers_info[paper_id], indent=2)
                except (FileNotFoundError, json.JSONDecodeError) as e:
                    print(f"Error reading {file_path}: {str(e)}")
                    continue

    return f"There's no saved information related to paper {paper_id}."


@mcp.tool()
def get_weather(city) -> dict:
    """
    Get the weather for a given city. This gives you an examples for getting weather report.

    Args:
        city: The city to get the weather for
    Returns:
        A dictionary with weather information.

    """
    import random
    temp = random.uniform(40, 70)

       
    return {
        "city": city,
        "weather": "sunny",
        "temperature": temp,
        "message": "This is Agent Generated Data",
    }

@mcp.tool()
def change_from_temperature_to_fahrenheit(temperature):
    """
     Convert the temperature from celsius to fahrenheit.

    Args:
        Temperature : The Temperature in celsius.
    Returns:
        The string with converted the temperature from the celsius.
    
    """
    ch = int(temperature) + 45
    return f"The required temperature is {ch}"


if __name__ == "__main__":
    # Initialize and run the server
    mcp.run(transport="stdio")






"""

What this does:

Starts your research_server.py as a separate process
Opens pipes so you can send/receive data

MCP (Model Context Protocol) servers communicate using JSON-RPC over stdin/stdout. Think of it like this:

You send JSON messages to the server's input (stdin)
Server responds with JSON messages on its output (stdout)

import subprocess
import sys

# Start the server as a subprocess
process = subprocess.Popen(
    [sys.executable, 'research_server.py'],  # Run the server
    stdin=subprocess.PIPE,   # We can write to it
    stdout=subprocess.PIPE,  # We can read from it
    stderr=subprocess.PIPE,  # Capture errors
    text=True,               # Use text mode (not bytes)
    bufsize=1                # Line buffered
)




# Why? MCP requires initialization before you can use any tools.
import json

# Create the initialize request
init_request = {
    "jsonrpc": "2.0",
    "id": 1,
    "method": "initialize",
    "params": {
        "protocolVersion": "2024-11-05",
        "capabilities": {},
        "clientInfo": {
            "name": "test-client",
            "version": "1.0.0"
        }
    }
}

# Send it to the server
process.stdin.write(json.dumps(init_request) + "\n")
process.stdin.flush()

# Read the response
response = process.stdout.readline()
init_response = json.loads(response)
print("Server initialized:", init_response)

What happens:

You send an initialize message
Server responds with its capabilities
Now the server is ready


-----------------------------------


Step 3: Call a Tool

# Create a tool call request
search_request = {
    "jsonrpc": "2.0",
    "id": 2,
    "method": "tools/call",
    "params": {
        "name": "search_papers",      # Tool name
        "arguments": {                # Tool arguments
            "topic": "machine learning",
            "max_results": 3
        }
    }
}

# Send the request
process.stdin.write(json.dumps(search_request) + "\n")
process.stdin.flush()

# Read the response
response = process.stdout.readline()
result = json.loads(response)
print("Search result:", result)


What happens:

You tell the server which tool to call and with what arguments
Server executes search_papers("machine learning", 3)
Server returns the result


"""
