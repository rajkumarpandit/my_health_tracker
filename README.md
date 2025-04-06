# Health Tracker Application

A Flask-based web application for tracking daily meals and nutrition information.

## Features
- Record meals with natural language input
- Calculate nutrition information using OpenAI GPT
- Store nutrition data in ChromaDB for quick retrieval
- Track daily nutrition intake
- User authentication

## Technologies Used
- Python/Flask
- OpenAI GPT API
- ChromaDB
- SQLite
- Bootstrap

## Setup
1. Clone the repository
2. Create a virtual environment:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```
3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
4. Set up environment variables:
   - Create a `.env` file
   - Add your OpenAI API key: `OPENAI_API_KEY=your_key_here`

5. Initialize the database:
   ```bash
   flask db upgrade
   ```

6. Run the application:
   ```bash
   flask run
   ```

## Project Structure
```
my_health_tracker/
├── app/
│   ├── __init__.py
│   ├── models.py
│   ├── routes/
│   │   └── meal.py
│   └── templates/
│       └── meal/
│           └── record.html
├── data/
│   └── chromadb/
├── migrations/
├── .env
├── .gitignore
└── README.md
```
