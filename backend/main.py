from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from api.endpoints import repositories, analysis

app = FastAPI(
    title="Code Analysis API",
    description="API for analyzing code repositories and providing improvement recommendations",
    version="0.1.0"
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # For production, replace with specific origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(repositories.router, prefix="/api/repositories", tags=["repositories"])
app.include_router(analysis.router, prefix="/api/analysis", tags=["analysis"])

@app.get("/", tags=["health"])
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "service": "code-analysis-api"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)