# Architecture Interaction Plan


## 1. User Request Flow:

API request comes in through FastAPI endpoints
Repository URL/data is passed to the ingestion system
Analysis is triggered and coordinated by core modules
Results are assembled into a report
Report is returned to the user


## 2. Data Flow:

Repository data → Code structure → Analysis agents → Report generation



## 3. Component Interactions
Entry Point & API Layer

main.py initializes FastAPI and imports routes from api/endpoints/*
api/endpoints/repositories.py handles repo submission and status checks
api/endpoints/analysis.py handles analysis requests and report retrieval
api/dependencies.py provides dependency injection for services

## 4. Core Orchestration

core/repo_ingestion.py uses services/gitingest_service.py to clone/parse repos
core/code_analysis.py coordinates the various analyzer agents in sequence
core/report_generator.py compiles analysis results into a structured report

## 5. Agents Layer

Each agent in agents/* performs a specific analysis task:

structural_analyzer.py analyzes overall code structure
pattern_recognizer.py identifies design patterns
smell_detector.py finds potential code smells
refactoring_advisor.py suggests improvements based on other analyses



## 6. Services

services/gitingest_service.py handles git operations and code retrieval
services/llm_service.py provides LLM functionality for deeper code understanding

## 7. Models

models/repository.py represents repository metadata and structure
models/analysis.py contains data structures for analysis results
models/report.py defines the final report format
