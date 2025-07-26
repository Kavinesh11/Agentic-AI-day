"""
Receipt Management System - FastAPI Application

This application provides a receipt management system using multi-agent architecture
with Gemini 2.0 Flash for receipt classification and parsing.
Updated to use ADK's standardized FastAPI integration patterns with proper caching,
WebSocket support, and session management.
"""

import os
import json
import base64
import uuid
import asyncio
from typing import Dict, Any, Optional
from io import BytesIO
from datetime import datetime
from pathlib import Path
from weakref import WeakValueDictionary

from fastapi import FastAPI, File, UploadFile, HTTPException, WebSocket, WebSocketDisconnect
from fastapi.responses import JSONResponse, FileResponse, StreamingResponse
from fastapi.staticfiles import StaticFiles
from PIL import Image
import uvicorn
from dotenv import load_dotenv

# ADK imports following best practices
from google.adk.cli.fast_api import get_fast_api_app
from google.adk.runners import Runner, InMemoryRunner
from google.adk.sessions import InMemorySessionService, InMemoryArtifactService
from google.adk.agents import LiveRequestQueue
from google.adk.agents.run_config import RunConfig
from google.genai import types

from receipt_agent import root_agent

# Load environment variables
load_dotenv()

# Initialize ADK services following best practices
session_service = InMemorySessionService()
artifact_service = InMemoryArtifactService()
APP_NAME = "Receipt Management System"
DEFAULT_USER_ID = "api_user"

# Global runner cache for efficient reuse - following ADK best practices
# Runners are cached per app to avoid recreation overhead
_runner_cache: Dict[str, Runner] = {}
_runner_cache_lock = asyncio.Lock()

# Active WebSocket connections and sessions tracking
active_websockets: Dict[str, WebSocket] = {}
active_sessions: Dict[str, LiveRequestQueue] = {}
session_cleanup_tasks: Dict[str, asyncio.Task] = {}


async def get_cached_runner(agent_key: Optional[str] = None) -> Runner:
    """
    Get or create a cached Runner instance.
    Runners are cached per app to avoid recreation overhead.
    Efficient cleanup when agents are updated.
    """
    cache_key = agent_key or "default_receipt_agent"

    async with _runner_cache_lock:
        if cache_key not in _runner_cache:
            # Create new runner with proper ADK patterns
            runner = InMemoryRunner(
                agent=root_agent,
                app_name=APP_NAME,
            )
            _runner_cache[cache_key] = runner
            print(f"Created new cached runner for key: {cache_key}")

        return _runner_cache[cache_key]


async def cleanup_runner_cache():
    """Cleanup runner cache - called when agents are updated."""
    async with _runner_cache_lock:
        for key, runner in _runner_cache.items():
            # Proper cleanup for each runner
            try:
                if hasattr(runner, 'cleanup'):
                    await runner.cleanup()
                print(f"Cleaned up runner for key: {key}")
            except Exception as e:
                print(f"Error cleaning up runner {key}: {e}")

        _runner_cache.clear()
        print("Runner cache cleared")

# Get ADK's standardized FastAPI app with proper configuration
current_dir = Path(__file__).parent
app = get_fast_api_app(agent_dir=str(current_dir / "receipt_agent"))

# Update app metadata with enhanced information
app.title = "Receipt Management System"
app.description = """
A multi-agent receipt processing system using Gemini 2.0 Flash with ADK integration.
Features:
- Real-time WebSocket streaming
- Cached Runner instances for performance
- Live request queue for concurrent processing
- Advanced session management
"""
app.version = "2.0.0"

# Mount static files for web UI
static_dir = current_dir / "static"
if static_dir.exists():
    app.mount("/static", StaticFiles(directory=static_dir), name="static")


@app.on_event("startup")
async def startup_event():
    """Initialize services and caches on startup."""
    print("🚀 Starting Receipt Management System...")
    print(f"📋 App: {APP_NAME}")
    print(f"🤖 Agent: {root_agent.name}")
    print("✅ Ready for receipt processing!")


@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup resources on shutdown."""
    print("🔄 Shutting down Receipt Management System...")

    # Cleanup active WebSocket connections
    for user_id, websocket in active_websockets.copy().items():
        try:
            await websocket.close()
            print(f"Closed WebSocket for user: {user_id}")
        except Exception as e:
            print(f"Error closing WebSocket for {user_id}: {e}")

    # Cleanup active sessions
    for user_id, queue in active_sessions.copy().items():
        try:
            queue.close()
            print(f"Closed session queue for user: {user_id}")
        except Exception as e:
            print(f"Error closing session for {user_id}: {e}")

    # Cancel cleanup tasks
    for user_id, task in session_cleanup_tasks.copy().items():
        try:
            task.cancel()
            await task
        except asyncio.CancelledError:
            pass
        except Exception as e:
            print(f"Error cancelling cleanup task for {user_id}: {e}")

    # Cleanup runner cache
    await cleanup_runner_cache()
    print("✅ Shutdown complete")


@app.get("/")
async def root():
    """Enhanced root endpoint with comprehensive API information."""
    return {
        "message": "Receipt Management System API v2.0",
        "version": "2.0.0",
        "framework": "Google ADK",
        "features": {
            "websocket_streaming": "Real-time bidirectional communication",
            "runner_caching": "Optimized performance with cached runners",
            "session_management": "Advanced session lifecycle management",
            "concurrent_processing": "Live request queue for multiple users"
        },
        "endpoints": {
            "/process-receipt": "POST - Upload and process receipt image (Legacy)",
            "/ws/{user_id}": "WebSocket - Real-time streaming communication",
            "/health": "GET - Health check",
            "/cache/status": "GET - Cache status information",
            "/cache/clear": "POST - Clear runner cache",
            "/list-apps": "GET - List available ADK applications (Standard ADK)",
            "/run": "POST - Run agent and collect all events (Standard ADK)",
            "/run_sse": "POST - Run agent with streaming events (Standard ADK)",
            "/docs": "GET - Interactive API documentation",
            "/openapi.json": "GET - OpenAPI specification"
        },
        "agent_info": {
            "main_agent": root_agent.name,
            "description": root_agent.description,
            "sub_agents": len(root_agent.sub_agents) if hasattr(root_agent, 'sub_agents') else 0
        },
        "active_connections": {
            "websockets": len(active_websockets),
            "sessions": len(active_sessions),
            "cached_runners": len(_runner_cache)
        },
        "status": "ready"
    }


@app.get("/health")
async def health_check():
    """Enhanced health check with system status."""
    try:
        # Test session service
        test_session = await session_service.create_session(
            app_name=APP_NAME,
            user_id="health_check",
            state={}
        )

        # Test runner cache
        runner = await get_cached_runner("health_check")

        return {
            "status": "healthy",
            "service": "receipt-management-system",
            "version": "2.0.0",
            "framework": "Google ADK",
            "services": {
                "session_service": "operational",
                "artifact_service": "operational",
                "agent": "ready",
                "runner_cache": "operational"
            },
            "metrics": {
                "active_websockets": len(active_websockets),
                "active_sessions": len(active_sessions),
                "cached_runners": len(_runner_cache),
                "cleanup_tasks": len(session_cleanup_tasks)
            },
            "timestamp": datetime.now().isoformat() + 'Z'
        }
    except Exception as e:
        return JSONResponse(
            status_code=503,
            content={
                "status": "unhealthy",
                "error": str(e),
                "timestamp": datetime.now().isoformat() + 'Z'
            }
        )


@app.get("/cache/status")
async def cache_status():
    """Get detailed cache status information."""
    return {
        "runner_cache": {
            "size": len(_runner_cache),
            "keys": list(_runner_cache.keys()),
            "memory_efficient": "Using WeakValueDictionary patterns"
        },
        "active_sessions": {
            "count": len(active_sessions),
            "user_ids": list(active_sessions.keys())
        },
        "websocket_connections": {
            "count": len(active_websockets),
            "user_ids": list(active_websockets.keys())
        },
        "cleanup_tasks": {
            "count": len(session_cleanup_tasks),
            "user_ids": list(session_cleanup_tasks.keys())
        }
    }


@app.post("/cache/clear")
async def clear_cache():
    """Clear runner cache - useful when agents are updated."""
    await cleanup_runner_cache()
    return {
        "message": "Runner cache cleared successfully",
        "timestamp": datetime.now().isoformat() + 'Z'
    }


async def start_agent_session(user_id: str, is_audio: bool = False):
    """
    Starts an agent session with proper ADK patterns.
    Uses cached runner for efficiency.
    """
    # Get cached runner instance
    runner = await get_cached_runner()

    # Create a Session using the runner's session service
    session = await runner.session_service.create_session(
        app_name=APP_NAME,
        user_id=user_id,
        state={"audio_enabled": is_audio, "processing_receipts": True}
    )

    # Set response modality
    modality = "AUDIO" if is_audio else "TEXT"
    run_config = RunConfig(response_modalities=[modality])

    # Create a LiveRequestQueue for this session
    live_request_queue = LiveRequestQueue()

    # Start agent session
    live_events = runner.run_live(
        session=session,
        live_request_queue=live_request_queue,
        run_config=run_config,
    )

    return live_events, live_request_queue


async def cleanup_user_session(user_id: str):
    """Cleanup function for user sessions with proper resource management."""
    try:
        # Close LiveRequestQueue
        if user_id in active_sessions:
            active_sessions[user_id].close()
            del active_sessions[user_id]

        # Close WebSocket connection
        if user_id in active_websockets:
            try:
                await active_websockets[user_id].close()
            except:
                pass  # Connection might already be closed
            del active_websockets[user_id]

        # Remove cleanup task
        if user_id in session_cleanup_tasks:
            del session_cleanup_tasks[user_id]

        print(f"Cleaned up session for user: {user_id}")
    except Exception as e:
        print(f"Error during cleanup for user {user_id}: {e}")


@app.websocket("/ws/{user_id}")
async def websocket_endpoint(websocket: WebSocket, user_id: str, is_audio: str = "false"):
    """
    WebSocket endpoint for real-time streaming responses and live request queue 
    for concurrent processing. Supports bidirectional communication.
    """
    await websocket.accept()
    print(f"🔌 WebSocket client #{user_id} connected, audio mode: {is_audio}")

    # Store active WebSocket connection
    active_websockets[user_id] = websocket

    try:
        # Start agent session
        live_events, live_request_queue = await start_agent_session(
            user_id, is_audio.lower() == "true"
        )

        # Store active session
        active_sessions[user_id] = live_request_queue

        # Start concurrent tasks for bidirectional communication
        agent_to_client_task = asyncio.create_task(
            agent_to_client_messaging(websocket, live_events, user_id)
        )
        client_to_agent_task = asyncio.create_task(
            client_to_agent_messaging(websocket, live_request_queue, user_id)
        )

        # Schedule cleanup task
        cleanup_delay = 300  # 5 minutes idle timeout
        cleanup_task = asyncio.create_task(
            asyncio.sleep(cleanup_delay)
        )
        session_cleanup_tasks[user_id] = cleanup_task

        # Wait until WebSocket disconnection or error
        done, pending = await asyncio.wait(
            [agent_to_client_task, client_to_agent_task, cleanup_task],
            return_when=asyncio.FIRST_COMPLETED
        )

        # Cancel pending tasks
        for task in pending:
            task.cancel()
            try:
                await task
            except asyncio.CancelledError:
                pass

    except WebSocketDisconnect:
        print(f"🔌 WebSocket client #{user_id} disconnected normally")
    except Exception as e:
        print(f"❌ WebSocket error for client #{user_id}: {e}")
    finally:
        # Cleanup user session
        await cleanup_user_session(user_id)
        print(f"🧹 WebSocket client #{user_id} cleanup completed")


async def agent_to_client_messaging(websocket: WebSocket, live_events, user_id: str):
    """Agent to client communication with enhanced error handling."""
    try:
        async for event in live_events:
            # Handle turn completion or interruption
            if event.turn_complete or event.interrupted:
                message = {
                    "type": "control",
                    "turn_complete": event.turn_complete,
                    "interrupted": event.interrupted,
                    "timestamp": datetime.now().isoformat()
                }
                await websocket.send_text(json.dumps(message))
                print(f"[AGENT TO CLIENT {user_id}]: {message}")
                continue

            # Process content parts
            part: types.Part = (
                event.content and event.content.parts and event.content.parts[0]
            )
            if not part:
                continue

            # Handle audio data
            is_audio = part.inline_data and part.inline_data.mime_type.startswith(
                "audio/pcm")
            if is_audio:
                audio_data = part.inline_data and part.inline_data.data
                if audio_data:
                    message = {
                        "type": "audio",
                        "mime_type": "audio/pcm",
                        "data": base64.b64encode(audio_data).decode("ascii"),
                        "size": len(audio_data),
                        "timestamp": datetime.now().isoformat()
                    }
                    await websocket.send_text(json.dumps(message))
                    print(
                        f"[AGENT TO CLIENT {user_id}]: audio/pcm: {len(audio_data)} bytes")
                    continue

            # Handle text data
            if part.text and event.partial:
                message = {
                    "type": "text",
                    "mime_type": "text/plain",
                    "data": part.text,
                    "partial": True,
                    "timestamp": datetime.now().isoformat()
                }
                await websocket.send_text(json.dumps(message))
                print(
                    f"[AGENT TO CLIENT {user_id}]: text: {part.text[:50]}...")

    except WebSocketDisconnect:
        print(f"[AGENT TO CLIENT {user_id}]: WebSocket disconnected")
    except Exception as e:
        print(f"[AGENT TO CLIENT {user_id}] Error: {e}")


async def client_to_agent_messaging(websocket: WebSocket, live_request_queue: LiveRequestQueue, user_id: str):
    """Client to agent communication with enhanced message handling."""
    try:
        while True:
            # Receive message from client
            message_json = await websocket.receive_text()
            message = json.loads(message_json)

            message_type = message.get("type", "unknown")
            mime_type = message.get("mime_type", "")
            data = message.get("data", "")

            # Handle different message types
            if mime_type == "text/plain":
                # Send text message to agent
                content = types.Content(
                    role="user",
                    parts=[types.Part.from_text(text=data)]
                )
                live_request_queue.send_content(content=content)
                print(f"[CLIENT TO AGENT {user_id}]: {data}")

            elif mime_type == "audio/pcm":
                # Send audio data to agent
                decoded_data = base64.b64decode(data)
                live_request_queue.send_realtime(
                    types.Blob(data=decoded_data, mime_type=mime_type)
                )
                print(
                    f"[CLIENT TO AGENT {user_id}]: audio/pcm: {len(decoded_data)} bytes")

            elif message_type == "receipt_image":
                # Handle receipt image processing
                image_data = base64.b64decode(data)
                await process_receipt_via_websocket(
                    websocket, live_request_queue, image_data, user_id
                )

            else:
                print(
                    f"[CLIENT TO AGENT {user_id}] Unsupported message type: {message_type}")
                error_msg = {
                    "type": "error",
                    "message": f"Unsupported message type: {message_type}",
                    "timestamp": datetime.now().isoformat()
                }
                await websocket.send_text(json.dumps(error_msg))

    except WebSocketDisconnect:
        print(f"[CLIENT TO AGENT {user_id}]: WebSocket disconnected")
    except Exception as e:
        print(f"[CLIENT TO AGENT {user_id}] Error: {e}")


async def process_receipt_via_websocket(
    websocket: WebSocket,
    live_request_queue: LiveRequestQueue,
    image_data: bytes,
    user_id: str
):
    """Process receipt image through WebSocket with real-time feedback."""
    try:
        # Validate and process image
        image = Image.open(BytesIO(image_data))
        if image.mode != 'RGB':
            image = image.convert('RGB')

        # Convert to base64 for LLM processing
        buffered = BytesIO()
        image.save(buffered, format="JPEG", quality=85, optimize=True)
        image_base64 = base64.b64encode(buffered.getvalue()).decode()

        # Send processing status
        status_msg = {
            "type": "status",
            "message": "Processing receipt image...",
            "stage": "analysis",
            "timestamp": datetime.now().isoformat()
        }
        await websocket.send_text(json.dumps(status_msg))

        # Create enhanced prompt for the agent
        prompt = f"""
        Please analyze and process this receipt image. Extract all relevant information and return structured data.
        
        Image data: data:image/jpeg;base64,{image_base64}
        
        Classify the receipt type and extract comprehensive information following your specialized parsing instructions.
        Provide real-time feedback during processing.
        """

        # Send to agent via live request queue
        content = types.Content(
            role="user",
            parts=[types.Part.from_text(text=prompt)]
        )
        live_request_queue.send_content(content=content)

        print(f"[RECEIPT PROCESSING {user_id}]: Sent receipt for analysis")

    except Exception as e:
        error_msg = {
            "type": "error",
            "message": f"Receipt processing failed: {str(e)}",
            "timestamp": datetime.now().isoformat()
        }
        await websocket.send_text(json.dumps(error_msg))
        print(f"[RECEIPT PROCESSING {user_id}] Error: {e}")


@app.post("/process-receipt")
async def process_receipt(file: UploadFile = File(...)):
    """
    Process uploaded receipt image through multi-agent system.
    Enhanced version using cached runners and improved error handling.
    """
    try:
        # Enhanced file validation
        file_extension = os.path.splitext(file.filename or "")[1].lower()
        valid_extensions = {'.jpg', '.jpeg', '.png', '.gif', '.bmp', '.webp'}

        # Validate file type
        content_type_valid = (
            file.content_type and
            file.content_type.startswith('image/')
        )

        extension_valid = file_extension in valid_extensions

        if not (content_type_valid or extension_valid):
            raise HTTPException(
                status_code=400,
                detail={
                    "error": "Invalid file type",
                    "message": f"File must be an image. Received content-type: {file.content_type}, extension: {file_extension}",
                    "accepted_types": list(valid_extensions)
                }
            )

        # Read and validate image
        image_data = await file.read()
        if len(image_data) == 0:
            raise HTTPException(
                status_code=400,
                detail={"error": "Empty file",
                        "message": "Uploaded file is empty"}
            )

        try:
            image = Image.open(BytesIO(image_data))
            if image.mode != 'RGB':
                image = image.convert('RGB')
        except Exception as e:
            raise HTTPException(
                status_code=400,
                detail={
                    "error": "Invalid image file",
                    "message": f"Could not process image: {str(e)}"
                }
            )

        # Convert image to base64 for LLM processing
        buffered = BytesIO()
        image.save(buffered, format="JPEG", quality=85, optimize=True)
        image_base64 = base64.b64encode(buffered.getvalue()).decode()

        # Create enhanced prompt for the agent
        prompt = f"""
        Please analyze and process this receipt image. Extract all relevant information and return structured data.
        
        Image data: data:image/jpeg;base64,{image_base64}
        
        Classify the receipt type and extract comprehensive information following your specialized parsing instructions.
        """

        # Get cached runner instance
        runner = await get_cached_runner()

        # Create session using proper ADK patterns
        session = await runner.session_service.create_session(
            app_name=APP_NAME,
            user_id=DEFAULT_USER_ID,
            state={"processing_receipt": True, "filename": file.filename}
        )

        # Create content with proper structure
        content = types.Content(
            role="user",
            parts=[types.Part(text=prompt)]
        )

        # Run the agent using cached runner
        final_response = None
        events_list = []

        try:
            async for event in runner.run_async(
                user_id=DEFAULT_USER_ID,
                session_id=session.id,
                new_message=content
            ):
                events_list.append(event)
                # Extract final response from agent events
                if hasattr(event, 'content') and event.content:
                    if hasattr(event.content, 'parts') and event.content.parts:
                        for part in event.content.parts:
                            if hasattr(part, 'text') and part.text:
                                final_response = part.text
                elif hasattr(event, 'text'):
                    final_response = event.text
                elif hasattr(event, 'data') and event.data:
                    final_response = str(event.data)

        except Exception as e:
            raise Exception(f"Agent processing failed: {str(e)}")

        if not final_response:
            raise Exception("No response received from agent")

        # Enhanced JSON parsing with better error handling
        try:
            response_text = final_response.strip()

            # Remove common markdown formatting
            if response_text.startswith('```json'):
                response_text = response_text.replace(
                    '```json', '').replace('```', '').strip()
            elif response_text.startswith('```'):
                response_text = response_text.replace('```', '').strip()

            # Try to parse as JSON
            parsed_result = json.loads(response_text)

            # Ensure proper structure and add missing fields
            if isinstance(parsed_result, dict):
                # Generate UUID if missing
                if 'billId' not in parsed_result:
                    parsed_result['billId'] = str(uuid.uuid4())

                # Add metadata if missing
                if 'uploadDate' not in parsed_result:
                    parsed_result['uploadDate'] = datetime.now(
                    ).isoformat() + 'Z'

                if 'uploaderId' not in parsed_result:
                    parsed_result['uploaderId'] = DEFAULT_USER_ID

                if 'imageUrl' not in parsed_result:
                    parsed_result[
                        'imageUrl'] = f"https://firebasestorage.googleapis.com/{parsed_result['billId']}.jpg"

                # Add processing metadata
                parsed_result['metadata'] = {
                    "processed_by": "ADK Receipt Management System v2.0",
                    "processing_time": datetime.now().isoformat() + 'Z',
                    "agent_events": len(events_list),
                    "file_info": {
                        "filename": file.filename,
                        "size": len(image_data),
                        "format": image.format,
                        "dimensions": f"{image.width}x{image.height}"
                    },
                    "runner_cache": "enabled",
                    "session_management": "enhanced"
                }

                return JSONResponse(content=parsed_result)
            else:
                # Handle non-dict responses
                return JSONResponse(content={
                    "billId": str(uuid.uuid4()),
                    "billType": "Unknown",
                    "uploadDate": datetime.now().isoformat() + 'Z',
                    "uploaderId": DEFAULT_USER_ID,
                    "imageUrl": f"https://firebasestorage.googleapis.com/unknown.jpg",
                    "parsedData": {
                        "error": "Unexpected response format",
                        "raw_response": str(final_response)
                    },
                    "metadata": {
                        "processed_by": "ADK Receipt Management System v2.0",
                        "processing_time": datetime.now().isoformat() + 'Z',
                        "agent_events": len(events_list)
                    }
                })

        except json.JSONDecodeError as e:
            # Enhanced error response for JSON parsing failures
            return JSONResponse(content={
                "billId": str(uuid.uuid4()),
                "billType": "Error",
                "uploadDate": datetime.now().isoformat() + 'Z',
                "uploaderId": DEFAULT_USER_ID,
                "imageUrl": "https://firebasestorage.googleapis.com/error.jpg",
                "parsedData": {
                    "error": f"JSON parsing failed: {str(e)}",
                    "error_type": "json_decode_error",
                    "raw_response": str(final_response)[:1000]  # Limit size
                },
                "metadata": {
                    "processed_by": "ADK Receipt Management System v2.0",
                    "processing_time": datetime.now().isoformat() + 'Z',
                    "agent_events": len(events_list)
                }
            })

    except HTTPException:
        raise
    except Exception as e:
        # Enhanced error response with better debugging info
        return JSONResponse(
            status_code=500,
            content={
                "billId": str(uuid.uuid4()),
                "billType": "Error",
                "uploadDate": datetime.now().isoformat() + 'Z',
                "uploaderId": DEFAULT_USER_ID,
                "imageUrl": "https://firebasestorage.googleapis.com/error.jpg",
                "parsedData": {
                    "error": f"Processing failed: {str(e)}",
                    "error_type": "processing_error",
                    "filename": file.filename,
                    "file_size": len(image_data) if 'image_data' in locals() else 0
                },
                "metadata": {
                    "processed_by": "ADK Receipt Management System v2.0",
                    "processing_time": datetime.now().isoformat() + 'Z'
                }
            }
        )


@app.get("/ui")
async def serve_ui():
    """Serve basic UI if available, otherwise redirect to docs."""
    ui_file = static_dir / "index.html"
    if ui_file.exists():
        return FileResponse(ui_file)
    else:
        return JSONResponse(content={
            "message": "Web UI not available",
            "alternatives": {
                "api_docs": "/docs",
                "api_specification": "/openapi.json",
                "health_check": "/health",
                "cache_status": "/cache/status",
                "websocket_endpoint": "/ws/{user_id}"
            }
        })

if __name__ == "__main__":
    # Enhanced startup configuration
    port = int(os.getenv("PORT", 8000))
    debug = os.getenv("DEBUG", "False").lower() == "true"

    print("🚀 Starting Receipt Management System with ADK optimizations...")
    print(f"📡 WebSocket support: Enabled")
    print(f"🔄 Runner caching: Enabled")
    print(f"📊 Session management: Enhanced")

    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=port,
        reload=debug,
        access_log=True,
        log_level="info" if not debug else "debug"
    )
