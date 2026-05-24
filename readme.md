# I want to implement Task management APIs via FastAPI and Python with OOP and Verticle Slice Architecture

# BackEnds

## Execute APIs

## Execute command

# 1) Activate virtual environment (if not already active)
.\.venv\Scripts\Activate.ps1

# 2) Install dependencies (first time only)
pip install -r requirements.txt

# 3) Run the API
uvicorn main:app --reload --host 127.0.0.1 --port 8888


## After execution

Swagger UI: http://127.0.0.1:8000/docs
ReDoc: http://127.0.0.1:8000/redoc

# Front End

## Execute command

cd .\frontend
npm install
npm run dev -- --host 0.0.0.0 --port 8880