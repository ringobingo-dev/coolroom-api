import uvicorn
import json
from fastapi import FastAPI, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from src.handlers.auth_handler import handler

app = FastAPI(title="Coolroom API")

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mock context for local development
class MockContext:
    function_name = "local-dev"
    memory_limit_in_mb = 128
    invoked_function_arn = "local:arn"
    aws_request_id = "local-id"

@app.get("/debug")
async def debug(request: Request):
    event = {
        "headers": dict(request.headers),
        "httpMethod": request.method,
        "path": request.url.path,
        "requestContext": {
            "httpMethod": request.method,
            "path": request.url.path
        }
    }
    return handler(event, MockContext())

@app.post("/login")
async def login(request: Request):
    body = await request.body()
    body_str = body.decode()
    
    # Validate JSON before passing to handler
    try:
        if body_str:
            json.loads(body_str)
    except json.JSONDecodeError:
        return Response(
            content=json.dumps({
                "status": "error",
                "message": "Invalid JSON format in request body"
            }),
            status_code=400,
            media_type="application/json"
        )
    
    event = {
        "body": body_str,
        "headers": dict(request.headers),
        "httpMethod": request.method,
        "path": request.url.path,
        "requestContext": {
            "httpMethod": request.method,
            "path": request.url.path
        }
    }
    
    result = handler(event, MockContext())
    
    # Check if result is a tuple (response, status_code)
    if isinstance(result, tuple):
        response_body, status_code = result
        return Response(
            content=json.dumps(response_body),
            status_code=status_code,
            media_type="application/json"
        )
    
    # If not a tuple, assume it's just the response body
    return result

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=3000)