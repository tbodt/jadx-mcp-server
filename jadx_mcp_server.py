# /// script
# requires-python = ">=3.10"
# dependencies = [ "fastmcp", "httpx", "logging", "argparse"]
# ///

"""
Copyright (c) 2025 jadx mcp server developer(s) (https://github.com/zinja-coder/jadx-ai-mcp)
See the file 'LICENSE' for copying permission
"""

import httpx
import logging
import json
import argparse

from typing import List, Union, Dict, Optional
from fastmcp import FastMCP

# Set up logging configuration
logger = logging.getLogger()
logger.setLevel(logging.ERROR)

# Console handler for logging to the console
console_handler = logging.StreamHandler()
console_handler.setLevel(logging.ERROR)
console_handler.setFormatter(logging.Formatter('%(asctime)s - %(levelname)s - %(message)s'))
logger.addHandler(console_handler)

# setup argparse to parse whether to run this script as http streambased or stdio based
parser = argparse.ArgumentParser(description='JADX AI MCP SERVER')
parser.add_argument('--http', action="store_true", default=False, help='This switch runs the mcp server in http stream based mode.')
parser.add_argument('--port', type=int, default=8651, help='Port to listen - default:8651')

# Initialize the MCP server
mcp = FastMCP("JADX-AI-MCP Plugin Reverse Engineering Server")

# To do : implement logic to handle the scenario where port is not available
JADX_HTTP_BASE = "http://127.0.0.1:8650" # Base URL for the JADX-AI-MCP Plugin


# Generic method to fetch data from jadx
async def get_from_jadx(endpoint: str, params: dict = {}) -> Union[str, dict]:
    """Generic helper to request data from the JADX plugin with proper error reporting and logging."""
    try:
        async with httpx.AsyncClient() as client:
            resp = await client.get(f"{JADX_HTTP_BASE}/{endpoint}", params=params, timeout=60)
            resp.raise_for_status()
            return resp.text
    except httpx.HTTPStatusError as e:
        error_message = f"HTTP error {e.response.status_code}: {e.response.text}"
        logger.error(error_message)
        return {"error": f"{error_message}."}
    except httpx.RequestError as e:
        error_message = f"Request failed: {str(e)}"
        logger.error(error_message)
        return {"error": f"{error_message}."}
    except Exception as e:
        error_message = f"Unexpected error: {str(e)}"
        logger.error(error_message)
        return {"error": f"{error_message}."}

# Specific MCP tools

@mcp.tool(name="fetch_current_class", description="Fetch the currently selected class and its code from the JADX-GUI plugin.")
async def fetch_current_class() -> dict:
    """Fetch currently opened class in jadx.
    
    Args:
        None

    Returns:
        Dictionary containing currently opened class in jadx. 
    """
    response = await get_from_jadx("current-class")

    if isinstance(response, str):
        try:
            return json.loads(response)
        except json.JSONDecodeError:
            return {"error": "Malformed manifest JSON string"}

@mcp.tool(name="get_selected_text", description="Returns the currently selected text in the decompiled code view.")
async def get_selected_text() -> str:
    """Returns the currently selected text in the decompiled code view.
    
    Args:
        None

    Returns:
        String containing currently highlighted/selected text in jadx-gui.
    """
    return await get_from_jadx("selected-text")

@mcp.tool(name="get_method_by_name", description="Fetch the source code of a method from a specific class.")
async def get_method_by_name(class_name: str, method_name: str) -> dict:
    """Fetch the source code of a method from a specific class.
    
    Args:
        class_name: Name of the class whose method's code will be returned
        method_name: Name of the method whose code will be returned

    Returns:
        Code of requested method as String.
    """
    response = await get_from_jadx("method-by-name", {"class": class_name, "method": method_name})
    if isinstance(response, str):
        try:
            return json.loads(response)
        except json.JSONDecodeError:
            return {"error": "Malformed manifest JSON string"}

@mcp.tool(name="get_all_classes", description="Returns a list of all classes in the project. This does not returns any code.")
async def get_all_classes() -> dict:
    """Returns a list of all classes in the project.
    
    Args:
        None
    
    Returns:
        A list of all classes in the project.
    """

    response = await get_from_jadx(f"all-classes")
    #if isinstance(response, dict):
    #    all_classes = response.get("classes", [])
    #else:
    #    try:
    #        parsed = json.loads(response)
    #        all_classes = parsed.get("classes", [])
    #    except (json.JSONDecodeError, AttributeError):
    #        all_classes = []
    if isinstance(response, str):
        try:
            return json.loads(response)
        except json.JSONDecodeError:
            return {"error": "Malformed manifest JSON string"}
    return response

@mcp.tool(name="get_class_sources", description="Fetch the Java source of a specific class.")
async def get_class_source(class_name: str) -> str:
    """Fetch the Java source of a specific class.
    
    Args:
        class_name: Name of the class whose source code will be returned

    Returns:
        Code of requested class as String.
    """
    return await get_from_jadx("class-source", {"class": class_name})

@mcp.tool(name="search_method_by_name", description="Search for a method name across all classes.")
async def search_method_by_name(method_name: str) -> List[str]:
    """Search for a method name across all classes.
    
    Args:
        method_name: The name of the method to search for
        offset: Offset to start listing from (start at 0)
        count: Number of strings to list (0 means remainder)
    
    Returns:
        A list of all classes containing the method.
    """
    response = await get_from_jadx("search-method", {"method": method_name})
    all_matches = response.splitlines() if response else []
    return all_matches

@mcp.tool(name="get_methods_of_class", description="List all method names in a class.")
async def get_methods_of_class(class_name: str) -> List[str]:
    """List all method names in a class.
    
    Args:
        count: Number of strings to list (0 means remainder)
    
    Returns:
        A list of all methods in the class.
    """    
    response = await get_from_jadx("methods-of-class", {"class": class_name})
    all_methods = response.splitlines() if response else []
    return all_methods

@mcp.tool(name="get_fields_of_class", description="List all field names in a class.")
async def get_fields_of_class(class_name: str) -> List[str]:
    """List all field names in a class.
    
    Args:
        count: Number of strings to list (0 means remainder)
    
    Returns:
        A list of all fields in the class.
    """

    response = await get_from_jadx("fields-of-class", {"class": class_name})
    all_fields = response.splitlines() if response else []
    return all_fields

@mcp.tool(name="get_smali_of_class", description="Fetch the smali representation of a class.")
async def get_smali_of_class(class_name: str) -> str:
    """Fetch the smali representation of a class.
    
    Args:
        class_name: Name of the class whose smali is to be returned

    Returns:
        Smali code of the requested class as String.
    """
    return await get_from_jadx("smali-of-class", {"class": class_name})

@mcp.tool(name="get_android_manifest", description="Retrieve and return the AndroidManifest.xml content.")
async def get_android_manifest() -> dict:
    """Retrieve and return the AndroidManifest.xml content.
    
    Args:
        None

    Returns:
        Dictionary containing content of AndroidManifest.xml file.
    """
    response = await get_from_jadx("manifest")
    if isinstance(response, str):
        try:
            return json.loads(response)
        except json.JSONDecodeError:
            return {"error": "Malformed manifest JSON string"}

@mcp.tool(name="get_strings", description="Retrieve contents of strings.xml files that exists in application.")
async def get_strings() -> dict:
    """Retrieve contents of strings.xml files that exists in application

    Args:
        None

    Returns:
        Dictionary containing contents of strings.xml file.
    """
    response = await get_from_jadx("strings")
    if isinstance(response, str):
        try:
            return json.loads(response)
        except json.JSONDecodeError:
            return {"error": "Malformed manifest JSON string"}

@mcp.tool(name="get_all_resource_file_names", description="Retrieve all resource files names that exists in application.")
async def get_all_resource_file_names() -> dict:
    """Retrieve all resource files names that exists in application

    Args:
        None

    Returns:
        List of all resource files names.
    """
    response = await get_from_jadx("list-all-resource-files-names")
    if isinstance(response, str):
        try:
            return json.loads(response)
        except json.JSONDecodeError:
            return {"error": "Malformed manifest JSON string"}

@mcp.tool(name="get_resource_file", description="Retrieve resource file content.")
async def get_resource_file(resource_name: str) -> dict:
    """Retrieve resource file content

    Args:
        resource_name: Name of the resource file

    Returns:
        Gets the content of resource file specified in 'resource_name' parameter
    """
    response = await get_from_jadx("get-resource-file", {"name": resource_name})
    if isinstance(response, str):
        try:
            return json.loads(response)
        except json.JSONDecodeError:
            return {"error": "Malformed manifest JSON string"}
    
@mcp.tool(name="get_main_application_classes_names", description="Fetch all the main application classes' names based on the package name defined in the AndroidManifest.xml.")
async def get_main_application_classes_names() -> List[str]:
    """Fetch all the main application classes' names based on the package name defined in the AndroidManifest.xml.
    
    Args:
        None

    Returns:
        Dictionary containing all the main application's classes' names based on the package name defined in the AndroidManifest.xml file.
    """

    response = await get_from_jadx("main-application-classes-names")
    if isinstance(response, dict):
        class_names = response.get("classes", [])
    else:
        try:
            parsed = json.loads(response)
            class_info_list = parsed.get("classes", [])
            class_names = [cls_info.get("name") for cls_info in class_info_list if "name" in cls_info]
        except (json.JSONDecodeError, AttributeError):
            class_names = []
    
    return class_names

@mcp.tool(name="get_main_application_classes_code", description="Fetch all the main application classes' code based on the package name defined in the AndroidManifest.xml.")
async def get_main_application_classes_code() -> List[dict]:
    """Fetch all the main application classes' code based on the package name defined in the AndroidManifest.xml.
    
    Args:
        offset: Offset to start listing from (start at 0)
        count: Number of strings to list (0 means remainder)

    Returns:
        Dictionary containing all classes' source code which are under main package only based on package name defined in the AndroidManifest.xml file.
    """

    response = await get_from_jadx("main-application-classes-code")
    try:
        parsed = json.loads(response)
        class_sources = parsed.get("allClassesInPackage", [])
    except (json.JSONDecodeError, AttributeError):
        class_sources = []
    
    return class_sources
    
@mcp.tool(name="get_main_activity_class", description="Fetch the main activity class as defined in the AndroidManifest.xml.")
async def get_main_activity_class() -> dict:
    """Fetch the main activity class as defined in the AndroidManifest.xml.
    
    Args:
        None

    Returns:
        Dictionary containing content of main activity class defined in AndroidManifest.xml file.
    """
    response = await get_from_jadx("main-activity")
    if isinstance(response, str):
        try:
            return json.loads(response)
        except json.JSONDecodeError:
            return {"error": "Malformed manifest JSON string"}

@mcp.tool(name="rename_class", description="rename specific class name to one better understanding name,input class name must contain package name")
async def rename_class(class_name: str, new_name: str):
    """Renames a specific class.

    Args:
        class_name (str): The full name of the class to be renamed, including package name.
        new_name (str): The new name for the class.

    Returns:
        dict: The response from the JADX server.
    """
    return await get_from_jadx("rename-class", {"class": class_name, "newName": new_name})

@mcp.tool(name="rename_method", description="rename specific method name to one better understanding name,input method name must contain package name and class name")
async def rename_method(method_name: str, new_name: str):
    """Renames a specific method.

    Args:
        method_name (str): The full name of the method to be renamed, including package and class name.
        new_name (str): The new name for the method.

    Returns:
        dict: The response from the JADX server.
    """
    return await get_from_jadx("rename-method", {"method": method_name, "newName": new_name})

@mcp.tool(name="rename_field", description="rename specific field name to one better understanding name,must input full class name and field name")
async def rename_field(class_name: str,field_name: str, new_name: str):
    """Renames a specific field.

    Args:
        class_name (str): The full class name of field
        field_name (str): The field to be rename.
        new_name (str): The new name for the field.

    Returns:
        dict: The response from the JADX server.
    """
    return await get_from_jadx("rename-field", {"class": class_name, "field":field_name,"newFieldName": new_name})
    
if __name__ == "__main__":
    args = parser.parse_args()
    logger.info("JADX MCP SERVER\n - By ZinjaCoder (https://github.com/zinja-coder) \n - To Report Issues: https://github.com/zinja-coder/jadx-mcp-server/issues\n")
    if not args.http:
        mcp.run(transport="stdio")
    else:
        mcp.run(transport="http",host="0.0.0.0",
        port=8651,
        log_level="debug")
