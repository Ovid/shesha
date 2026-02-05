# Dependencies: 
# pip install fastmcp shesha

from mcp.server.fastmcp import FastMCP
from shesha import Shesha  # The "Brain"

# Initialize the MCP server under the name "Librarian"
mcp = FastMCP("Librarian")

try:
    # Initialize the Shesha engine with a persistent local data directory
    # Note: Ensure you have write permissions in the directory where you run this script.
    shesha = Shesha(storage_path="./shesha_data")
except Exception as e:
    print(f"Initialization Error: Could not access or create storage at './shesha_data'. {e}")

@mcp.tool()
def query_library(project_name: str, question: str):
    """
    Query the persistent project library using RLM logic.
    
    Args:
        project_name (str): The name/ID of the specific project library to access.
        question (str): The query to process against the project context.
        
    Returns:
        The result of the query or an error message if the project is not found.
    """
    try:
        # Retrieve the specific project instance from the storage engine
        project = shesha.get_project(project_name)
        
        # Guard clause: Handle cases where the project name does not exist in storage
        if not project:
            return f"Error: Project '{project_name}' not found in the library."
            
        # Execute the query against the project using its internal logic
        return project.query(question)
    
    except Exception as e:
        # Catch unexpected errors during the retrieval or query process
        return f"An error occurred while querying the library: {str(e)}"

if __name__ == "__main__":
    # Start the MCP server. Run this from the project root directory.
    # Command: python <your_script_name>.py
    mcp.run()
