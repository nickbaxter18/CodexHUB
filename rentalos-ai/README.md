# RentalOS-AI

RentalOS-AI is an intelligent operating system for the rental economy. Stage 1 establishes
core backend services, a modular frontend foundation, and documentation that defines the architectural vision.

## Getting Started

1. Create and activate a Python 3.11 virtual environment.
2. Install backend dependencies using `pip install -r requirements.txt`.
3. Install frontend dependencies using `npm run install:frontend` from the project root.
4. Run the FastAPI app with `uvicorn src.backend.main:app --reload`.
5. Start the frontend development server with `npm run dev`.

## Project Goals

- Automate operational workflows for property managers.
- Deliver self-service tools that empower tenants and communities.
- Embed sustainability metrics into every decision and workflow.

## Repository Layout

The repository follows a modular monolith approach. Backend and frontend packages live inside the `src`
directory, and shared documentation is available under `docs`.

## Stage Tracking

Use `python scripts/detect_stage.py` to determine the highest completed stage. Update `deploy_logs/changelog.md`
after finishing each stage so the detector can track progress accurately.
