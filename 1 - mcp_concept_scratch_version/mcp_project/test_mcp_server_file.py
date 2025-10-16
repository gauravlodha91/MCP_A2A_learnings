# import subprocess
# import json
# import sys
# import time

# def send_request(process, request):
#     """Send a JSON-RPC request and read the response"""
#     process.stdin.write(json.dumps(request) + "\n")
#     process.stdin.flush()
    
#     # Read the response
#     response_line = process.stdout.readline()
#     if response_line:
#         return json.loads(response_line.strip())
#     return None

# def test_mcp_server():
#     """Test the MCP server with proper initialization"""
    
#     # Start the server process
#     process = subprocess.Popen(
#         [sys.executable, 'research_server.py'],
#         stdin=subprocess.PIPE,
#         stdout=subprocess.PIPE,
#         stderr=subprocess.PIPE,
#         text=True,
#         bufsize=1
#     )
    
#     try:
#         # Step 1: Initialize the server
#         print("Step 1: Initializing server...")
#         init_request = {
#             "jsonrpc": "2.0",
#             "id": 1,
#             "method": "initialize",
#             "params": {
#                 "protocolVersion": "2024-11-05",
#                 "capabilities": {},
#                 "clientInfo": {
#                     "name": "test-client",
#                     "version": "1.0.0"
#                 }
#             }
#         }
        
#         response = send_request(process, init_request)
#         print(f"Initialize response: {json.dumps(response, indent=2)}\n")
        
#         # Step 2: Send initialized notification
#         print("Step 2: Sending initialized notification...")
#         initialized_notification = {
#             "jsonrpc": "2.0",
#             "method": "notifications/initialized"
#         }
#         process.stdin.write(json.dumps(initialized_notification) + "\n")
#         process.stdin.flush()
#         time.sleep(0.5)  # Give server time to process
        
#         # Step 3: List available tools
#         print("Step 3: Listing available tools...")
#         list_tools_request = {
#             "jsonrpc": "2.0",
#             "id": 2,
#             "method": "tools/list"
#         }
        
#         response = send_request(process, list_tools_request)
#         print(f"Tools list response: {json.dumps(response, indent=2)}\n")
        
#         # Step 4: Search for papers
#         print("Step 4: Searching for papers on 'machine learning'...")
#         search_request = {
#             "jsonrpc": "2.0",
#             "id": 3,
#             "method": "tools/call",
#             "params": {
#                 "name": "search_papers",
#                 "arguments": {
#                     "topic": "machine learning",
#                     "max_results": 3
#                 }
#             }
#         }
        
#         response = send_request(process, search_request)
#         print(f"Search response: {json.dumps(response, indent=2)}\n")
        
#         # Extract paper IDs from response if successful
#         if response and 'result' in response:
#             content = response['result'].get('content', [])
#             if content and len(content) > 0:
#                 result_text = content[0].get('text', '[]')
#                 paper_ids = json.loads(result_text)
                
#                 if paper_ids:
#                     # Step 5: Extract info for the first paper
#                     print(f"Step 5: Extracting info for paper '{paper_ids[0]}'...")
#                     extract_request = {
#                         "jsonrpc": "2.0",
#                         "id": 4,
#                         "method": "tools/call",
#                         "params": {
#                             "name": "extract_info",
#                             "arguments": {
#                                 "paper_id": paper_ids[0]
#                             }
#                         }
#                     }
                    
#                     response = send_request(process, extract_request)
#                     print(f"Extract info response: {json.dumps(response, indent=2)}\n")
        
#         # Read any stderr output
#         print("=== Server Messages ===")
#         time.sleep(1)
        
#     except Exception as e:
#         print(f"Error during testing: {e}")
    
#     finally:
#         # Clean up
#         process.terminate()
#         try:
#             process.wait(timeout=2)
#         except subprocess.TimeoutExpired:
#             process.kill()
        
#         # Print any remaining stderr
#         remaining_stderr = process.stderr.read()
#         if remaining_stderr:
#             print("Server stderr output:")
#             print(remaining_stderr)

# if __name__ == "__main__":
#     test_mcp_server()






import subprocess
import json
import sys
import time

def send_request(process, request):
    """Send a JSON-RPC request and read the response"""
    process.stdin.write(json.dumps(request) + "\n")
    process.stdin.flush()
    
    # Read the response
    response_line = process.stdout.readline()
    if response_line:
        try:
            return json.loads(response_line.strip())
        except json.JSONDecodeError as e:
            print(f"JSON decode error: {e}")
            print(f"Response line: {response_line}")
            return None
    return None

def test_mcp_server():
    """Test the MCP server with proper initialization"""
    
    # Start the server process
    process = subprocess.Popen(
        [sys.executable, 'research_server.py'],
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        bufsize=1
    )
    
    try:
        # Step 1: Initialize the server
        print("Step 1: Initializing server...")
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
        
        response = send_request(process, init_request)
        print(f"Initialize response: {json.dumps(response, indent=2)}\n")
        
        # Step 2: Send initialized notification
        print("Step 2: Sending initialized notification...")
        initialized_notification = {
            "jsonrpc": "2.0",
            "method": "notifications/initialized"
        }
        process.stdin.write(json.dumps(initialized_notification) + "\n")
        process.stdin.flush()
        time.sleep(0.5)
        
        # Step 3: List available tools
        print("Step 3: Listing available tools...")
        list_tools_request = {
            "jsonrpc": "2.0",
            "id": 2,
            "method": "tools/list"
        }
        
        response = send_request(process, list_tools_request)
        print(f"Tools list response: {json.dumps(response, indent=2)}\n")
        
        # Step 4: Search for papers
        print("Step 4: Searching for papers on 'machine learning'...")
        search_request = {
            "jsonrpc": "2.0",
            "id": 3,
            "method": "tools/call",
            "params": {
                "name": "search_papers",
                "arguments": {
                    "topic": "machine learning",
                    "max_results": 3
                }
            }
        }
        
        response = send_request(process, search_request)
        print(f"Search response: {json.dumps(response, indent=2)}\n")
        
        # Extract paper IDs from response
        paper_ids = []
        if response and 'result' in response:
            structured_content = response['result'].get('structuredContent', {})
            paper_ids = structured_content.get('result', [])
            print(f"Found paper IDs: {paper_ids}\n")
        
        if paper_ids:
            # Step 5: Extract info for the first paper
            print(f"Step 5: Extracting info for paper '{paper_ids[0]}'...")
            extract_request = {
                "jsonrpc": "2.0",
                "id": 4,
                "method": "tools/call",
                "params": {
                    "name": "extract_info",
                    "arguments": {
                        "paper_id": paper_ids[0]
                    }
                }
            }
            
            response = send_request(process, extract_request)
            print(f"Extract info response: {json.dumps(response, indent=2)}\n")
            
            # Pretty print the paper info
            if response and 'result' in response:
                structured = response['result'].get('structuredContent', {})
                paper_info_str = structured.get('result', '{}')
                try:
                    paper_info = json.loads(paper_info_str)
                    print("=" * 60)
                    print("PAPER DETAILS:")
                    print("=" * 60)
                    print(f"Title: {paper_info.get('title', 'N/A')}")
                    print(f"Authors: {', '.join(paper_info.get('authors', []))}")
                    print(f"Published: {paper_info.get('published', 'N/A')}")
                    print(f"PDF URL: {paper_info.get('pdf_url', 'N/A')}")
                    print(f"\nSummary:\n{paper_info.get('summary', 'N/A')[:300]}...")
                    print("=" * 60)
                except json.JSONDecodeError:
                    print("Could not parse paper info")
        
        print("\n✅ All tests completed successfully!")
        
        # Check if papers directory was created
        import os
        papers_dir = "papers/machine_learning"
        if os.path.exists(papers_dir):
            print(f"\n📁 Papers directory created: {papers_dir}")
            json_file = f"{papers_dir}/papers_info.json"
            if os.path.exists(json_file):
                print(f"📄 Papers info saved to: {json_file}")
        
    except Exception as e:
        print(f"❌ Error during testing: {e}")
        import traceback
        traceback.print_exc()
    
    finally:
        # Clean up
        process.terminate()
        try:
            process.wait(timeout=2)
        except subprocess.TimeoutExpired:
            process.kill()

if __name__ == "__main__":
    test_mcp_server()