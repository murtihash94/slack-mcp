"""Main FastMCP application for Slack MCP Server."""

import os
from pathlib import Path
from typing import Optional, List, Dict, Any
from mcp.server.fastmcp import FastMCP
from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
from slack_sdk import WebClient
from slack_sdk.errors import SlackApiError

# Get configuration from environment
SLACK_BOT_TOKEN = os.getenv("SLACK_BOT_TOKEN")
SLACK_USER_TOKEN = os.getenv("SLACK_USER_TOKEN")
SLACK_SAFE_SEARCH = os.getenv("SLACK_SAFE_SEARCH", "false").lower() == "true"

if not SLACK_BOT_TOKEN:
    raise ValueError("SLACK_BOT_TOKEN environment variable is required")

if not SLACK_USER_TOKEN:
    raise ValueError("SLACK_USER_TOKEN environment variable is required")

# Initialize Slack clients
slack_client = WebClient(token=SLACK_BOT_TOKEN)
user_client = WebClient(token=SLACK_USER_TOKEN)

if SLACK_SAFE_SEARCH:
    print("Safe search mode enabled: Private channels and DMs will be excluded from search results")

STATIC_DIR = Path(__file__).parent / "static"

# Create an MCP server
mcp = FastMCP("Slack MCP Server on Databricks Apps")


@mcp.tool()
def slack_list_channels(
    limit: int = 100,
    cursor: Optional[str] = None
) -> Dict[str, Any]:
    """List public channels in the workspace with pagination.
    
    Args:
        limit: Maximum number of channels to return (default: 100)
        cursor: Pagination cursor for next page
        
    Returns:
        Dictionary containing channels list and pagination info
    """
    try:
        response = slack_client.conversations_list(
            limit=limit,
            cursor=cursor,
            types="public_channel"
        )
        
        if not response["ok"]:
            raise HTTPException(status_code=400, detail=f"Slack API error: {response.get('error')}")
        
        return {
            "channels": [
                {
                    "id": ch.get("id"),
                    "name": ch.get("name"),
                    "is_archived": ch.get("is_archived"),
                    "num_members": ch.get("num_members")
                }
                for ch in response.get("channels", [])
            ],
            "response_metadata": response.get("response_metadata", {})
        }
    except SlackApiError as e:
        raise HTTPException(status_code=400, detail=f"Slack API error: {str(e)}")


@mcp.tool()
def slack_post_message(
    channel_id: str,
    text: str
) -> str:
    """Post a new message to a Slack channel.
    
    Args:
        channel_id: The ID of the channel to post to
        text: The message text to post
        
    Returns:
        Success message
    """
    try:
        response = slack_client.chat_postMessage(
            channel=channel_id,
            text=text
        )
        
        if not response["ok"]:
            raise HTTPException(status_code=400, detail=f"Slack API error: {response.get('error')}")
        
        return "Message posted successfully"
    except SlackApiError as e:
        raise HTTPException(status_code=400, detail=f"Slack API error: {str(e)}")


@mcp.tool()
def slack_reply_to_thread(
    channel_id: str,
    thread_ts: str,
    text: str
) -> str:
    """Reply to a specific message thread in Slack.
    
    Args:
        channel_id: The ID of the channel
        thread_ts: The timestamp of the parent message
        text: The reply text
        
    Returns:
        Success message
    """
    try:
        response = slack_client.chat_postMessage(
            channel=channel_id,
            thread_ts=thread_ts,
            text=text
        )
        
        if not response["ok"]:
            raise HTTPException(status_code=400, detail=f"Slack API error: {response.get('error')}")
        
        return "Reply sent to thread successfully"
    except SlackApiError as e:
        raise HTTPException(status_code=400, detail=f"Slack API error: {str(e)}")


@mcp.tool()
def slack_add_reaction(
    channel_id: str,
    timestamp: str,
    reaction: str
) -> str:
    """Add a reaction emoji to a message.
    
    Args:
        channel_id: The ID of the channel
        timestamp: The timestamp of the message
        reaction: The emoji name (without colons)
        
    Returns:
        Success message
    """
    try:
        response = slack_client.reactions_add(
            channel=channel_id,
            timestamp=timestamp,
            name=reaction
        )
        
        if not response["ok"]:
            raise HTTPException(status_code=400, detail=f"Slack API error: {response.get('error')}")
        
        return "Reaction added successfully"
    except SlackApiError as e:
        raise HTTPException(status_code=400, detail=f"Slack API error: {str(e)}")


@mcp.tool()
def slack_get_channel_history(
    channel_id: str,
    limit: int = 100,
    cursor: Optional[str] = None
) -> Dict[str, Any]:
    """Get messages from a channel in chronological order.
    
    Use this when:
    1) You need the latest conversation flow without specific filters
    2) You want ALL messages including bot/automation messages
    3) You need to browse messages sequentially with pagination
    
    Do NOT use if you have specific search criteria - use slack_search_messages instead.
    
    Args:
        channel_id: The ID of the channel
        limit: Maximum number of messages to return (default: 100)
        cursor: Pagination cursor for next page
        
    Returns:
        Dictionary containing messages and pagination info
    """
    try:
        response = slack_client.conversations_history(
            channel=channel_id,
            limit=limit,
            cursor=cursor
        )
        
        if not response["ok"]:
            raise HTTPException(status_code=400, detail=f"Slack API error: {response.get('error')}")
        
        return {
            "messages": [
                {
                    "type": msg.get("type"),
                    "user": msg.get("user"),
                    "text": msg.get("text"),
                    "ts": msg.get("ts"),
                    "thread_ts": msg.get("thread_ts"),
                    "reply_count": msg.get("reply_count"),
                    "reactions": msg.get("reactions")
                }
                for msg in response.get("messages", [])
            ],
            "has_more": response.get("has_more", False),
            "response_metadata": response.get("response_metadata", {})
        }
    except SlackApiError as e:
        raise HTTPException(status_code=400, detail=f"Slack API error: {str(e)}")


@mcp.tool()
def slack_get_thread_replies(
    channel_id: str,
    thread_ts: str,
    limit: int = 100,
    cursor: Optional[str] = None
) -> Dict[str, Any]:
    """Get all replies in a message thread.
    
    Args:
        channel_id: The ID of the channel
        thread_ts: The timestamp of the parent message
        limit: Maximum number of replies to return (default: 100)
        cursor: Pagination cursor for next page
        
    Returns:
        Dictionary containing thread replies and pagination info
    """
    try:
        response = slack_client.conversations_replies(
            channel=channel_id,
            ts=thread_ts,
            limit=limit,
            cursor=cursor
        )
        
        if not response["ok"]:
            raise HTTPException(status_code=400, detail=f"Slack API error: {response.get('error')}")
        
        return {
            "messages": [
                {
                    "type": msg.get("type"),
                    "user": msg.get("user"),
                    "text": msg.get("text"),
                    "ts": msg.get("ts"),
                    "thread_ts": msg.get("thread_ts")
                }
                for msg in response.get("messages", [])
            ],
            "has_more": response.get("has_more", False),
            "response_metadata": response.get("response_metadata", {})
        }
    except SlackApiError as e:
        raise HTTPException(status_code=400, detail=f"Slack API error: {str(e)}")


@mcp.tool()
def slack_get_users(
    limit: int = 100,
    cursor: Optional[str] = None
) -> Dict[str, Any]:
    """Retrieve basic profile information of all users in the workspace.
    
    Args:
        limit: Maximum number of users to return (default: 100)
        cursor: Pagination cursor for next page
        
    Returns:
        Dictionary containing users list and pagination info
    """
    try:
        response = slack_client.users_list(
            limit=limit,
            cursor=cursor
        )
        
        if not response["ok"]:
            raise HTTPException(status_code=400, detail=f"Slack API error: {response.get('error')}")
        
        return {
            "members": [
                {
                    "id": user.get("id"),
                    "name": user.get("name"),
                    "real_name": user.get("real_name"),
                    "profile": {
                        "display_name": user.get("profile", {}).get("display_name"),
                        "email": user.get("profile", {}).get("email"),
                        "image_48": user.get("profile", {}).get("image_48")
                    },
                    "is_bot": user.get("is_bot"),
                    "deleted": user.get("deleted")
                }
                for user in response.get("members", [])
            ],
            "response_metadata": response.get("response_metadata", {})
        }
    except SlackApiError as e:
        raise HTTPException(status_code=400, detail=f"Slack API error: {str(e)}")


@mcp.tool()
def slack_get_user_profiles(
    user_ids: List[str]
) -> Dict[str, Any]:
    """Get multiple users' profile information in bulk.
    
    Args:
        user_ids: List of user IDs to fetch profiles for
        
    Returns:
        Dictionary containing profiles with user_id as key
    """
    profiles = []
    
    for user_id in user_ids:
        try:
            response = slack_client.users_profile_get(user=user_id)
            
            if response["ok"]:
                profiles.append({
                    "user_id": user_id,
                    "profile": response.get("profile", {})
                })
            else:
                profiles.append({
                    "user_id": user_id,
                    "error": response.get("error", "Unknown error")
                })
        except SlackApiError as e:
            profiles.append({
                "user_id": user_id,
                "error": str(e)
            })
    
    return {"profiles": profiles}


@mcp.tool()
def slack_search_messages(
    query: Optional[str] = None,
    in_channel: Optional[str] = None,
    from_user: Optional[str] = None,
    before: Optional[str] = None,
    after: Optional[str] = None,
    on: Optional[str] = None,
    during: Optional[str] = None,
    highlight: bool = False,
    sort: str = "score",
    sort_dir: str = "desc",
    count: int = 20,
    page: int = 1
) -> Dict[str, Any]:
    """Search for messages with specific criteria/filters.
    
    Use this when:
    1) You need to find messages from a specific user
    2) You need messages from a specific date range
    3) You need to search by keywords
    4) You want to filter by channel
    
    This tool is optimized for targeted searches. For general channel browsing
    without filters, use slack_get_channel_history instead.
    
    Args:
        query: Search query text
        in_channel: Filter by channel ID
        from_user: Filter by user ID
        before: Messages before this date (YYYY-MM-DD)
        after: Messages after this date (YYYY-MM-DD)
        on: Messages on this date (YYYY-MM-DD)
        during: Messages during this period (e.g., "July", "2023")
        highlight: Whether to highlight matches
        sort: Sort by "score" or "timestamp"
        sort_dir: Sort direction "asc" or "desc"
        count: Number of results per page (default: 20)
        page: Page number (default: 1)
        
    Returns:
        Dictionary containing search results
    """
    try:
        search_query = query or ""
        
        # Add channel filter
        if in_channel:
            # Resolve channel name from ID
            channel_info = slack_client.conversations_info(channel=in_channel)
            if channel_info["ok"] and channel_info.get("channel", {}).get("name"):
                search_query += f" in:{channel_info['channel']['name']}"
        
        # Add user filter
        if from_user:
            search_query += f" from:<@{from_user}>"
        
        # Add date filters
        if before:
            search_query += f" before:{before}"
        if after:
            search_query += f" after:{after}"
        if on:
            search_query += f" on:{on}"
        if during:
            search_query += f" during:{during}"
        
        search_query = search_query.strip()
        print(f"Search query: {search_query}")
        
        response = user_client.search_messages(
            query=search_query,
            highlight=highlight,
            sort=sort,
            sort_dir=sort_dir,
            count=count,
            page=page
        )
        
        if not response["ok"]:
            raise HTTPException(status_code=400, detail=f"Slack API error: {response.get('error')}")
        
        # Apply safe search filtering if enabled
        matches = response.get("messages", {}).get("matches", [])
        if SLACK_SAFE_SEARCH:
            original_count = len(matches)
            matches = [
                msg for msg in matches
                if not (
                    msg.get("channel", {}).get("is_private") or
                    msg.get("channel", {}).get("is_im") or
                    msg.get("channel", {}).get("is_mpim")
                )
            ]
            filtered_count = original_count - len(matches)
            if filtered_count > 0:
                print(f"Safe search: Filtered out {filtered_count} messages from private channels/DMs")
        
        return {
            "messages": {
                "total": response.get("messages", {}).get("total", 0),
                "matches": [
                    {
                        "type": msg.get("type"),
                        "user": msg.get("user"),
                        "username": msg.get("username"),
                        "text": msg.get("text"),
                        "ts": msg.get("ts"),
                        "channel": {
                            "id": msg.get("channel", {}).get("id"),
                            "name": msg.get("channel", {}).get("name")
                        },
                        "permalink": msg.get("permalink")
                    }
                    for msg in matches
                ]
            }
        }
    except SlackApiError as e:
        raise HTTPException(status_code=400, detail=f"Slack API error: {str(e)}")


@mcp.tool()
def slack_search_channels(
    query: str,
    limit: int = 20
) -> Dict[str, Any]:
    """Search for channels by partial name match.
    
    Use this when you need to find channels containing specific keywords in their names.
    
    Args:
        query: Search query to match against channel names
        limit: Maximum number of channels to return (default: 20)
        
    Returns:
        Dictionary containing matching channels
    """
    try:
        # Fetch all channels
        all_channels = []
        cursor = None
        
        while True:
            response = slack_client.conversations_list(
                limit=200,
                cursor=cursor,
                types="public_channel"
            )
            
            if not response["ok"]:
                raise HTTPException(status_code=400, detail=f"Slack API error: {response.get('error')}")
            
            all_channels.extend(response.get("channels", []))
            
            cursor = response.get("response_metadata", {}).get("next_cursor")
            if not cursor:
                break
        
        # Filter by query
        query_lower = query.lower()
        matching_channels = [
            ch for ch in all_channels
            if query_lower in ch.get("name", "").lower() and not ch.get("is_archived", False)
        ]
        
        # Limit results
        matching_channels = matching_channels[:limit]
        
        return {
            "channels": [
                {
                    "id": ch.get("id"),
                    "name": ch.get("name"),
                    "num_members": ch.get("num_members"),
                    "purpose": ch.get("purpose", {}).get("value")
                }
                for ch in matching_channels
            ],
            "total": len(matching_channels)
        }
    except SlackApiError as e:
        raise HTTPException(status_code=400, detail=f"Slack API error: {str(e)}")


@mcp.tool()
def slack_search_users(
    query: str,
    limit: int = 20
) -> Dict[str, Any]:
    """Search for users by partial name match across username, display name, and real name.
    
    Use this when you need to find users containing specific keywords in their names.
    
    Args:
        query: Search query to match against user names
        limit: Maximum number of users to return (default: 20)
        
    Returns:
        Dictionary containing matching users
    """
    try:
        # Fetch all users
        all_users = []
        cursor = None
        
        while True:
            response = slack_client.users_list(
                limit=200,
                cursor=cursor
            )
            
            if not response["ok"]:
                raise HTTPException(status_code=400, detail=f"Slack API error: {response.get('error')}")
            
            all_users.extend(response.get("members", []))
            
            cursor = response.get("response_metadata", {}).get("next_cursor")
            if not cursor:
                break
        
        # Filter by query
        query_lower = query.lower()
        matching_users = [
            user for user in all_users
            if not user.get("deleted", False) and (
                query_lower in user.get("name", "").lower() or
                query_lower in user.get("real_name", "").lower() or
                query_lower in user.get("profile", {}).get("display_name", "").lower()
            )
        ]
        
        # Limit results
        matching_users = matching_users[:limit]
        
        return {
            "users": [
                {
                    "id": user.get("id"),
                    "name": user.get("name"),
                    "real_name": user.get("real_name"),
                    "display_name": user.get("profile", {}).get("display_name"),
                    "email": user.get("profile", {}).get("email"),
                    "is_bot": user.get("is_bot")
                }
                for user in matching_users
            ],
            "total": len(matching_users)
        }
    except SlackApiError as e:
        raise HTTPException(status_code=400, detail=f"Slack API error: {str(e)}")


# Create the MCP app
mcp_app = mcp.streamable_http_app()

# Create the main FastAPI app
app = FastAPI(
    title="Slack MCP Server on Databricks Apps",
    description="A Model Context Protocol server for Slack API integration",
    version="0.1.4",
    lifespan=lambda _: mcp.session_manager.run(),
)


@app.get("/", include_in_schema=False)
async def serve_index():
    """Serve the index page."""
    if STATIC_DIR.exists() and (STATIC_DIR / "index.html").exists():
        return FileResponse(STATIC_DIR / "index.html")
    return {"message": "Slack MCP Server is running", "version": "0.1.4"}


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {
        "status": "ok",
        "version": "0.1.4",
        "service": "slack-mcp-server"
    }


# Mount the MCP app
app.mount("/", mcp_app)
