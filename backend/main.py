from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from api.endpoints import repositories, analysis
from config.settings import settings

app = FastAPI(
    title="Code Analysis System",
    description="An LLM-powered system that analyzes repositories and provides refactoring suggestions",
    version="1.0.0"
)

# CORS middleware setup
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(repositories.router, prefix="/api", tags=["repositories"])
app.include_router(analysis.router, prefix="/api", tags=["analysis"])

@app.get("/")
async def root():
    return {"message": "Welcome to the Code Analysis System API"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)