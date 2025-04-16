# Vapor Store Assistant

A voice-enabled store assistant that helps customers with store hours, product prices, and inventory inquiries.

## Features

- Voice-based interaction using Web Speech API
- Real-time conversation with AI assistant
- Information about store hours
- Product pricing
- Inventory status
- Natural language processing

## Setup

1. Clone the repository:
```bash
git clone <repository-url>
cd vapor
```

2. Create and activate a virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Set up environment variables:
Create a `.env` file with your OpenAI API key:
```
OPENAI_API_KEY=your_api_key_here
```

## Running the Application

1. Start the FastAPI server:
```bash
uvicorn server:app --reload
```

2. Open `index.html` in your web browser or serve it using a local server.

3. Click the start button to begin the conversation.

## Development

- Frontend: HTML, JavaScript
- Backend: Python, FastAPI
- AI: OpenAI GPT-3.5 Turbo
- Speech: Web Speech API

## License

MIT 