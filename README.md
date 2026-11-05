# CycloneShield-Q

**CycloneShield-Q** is a prototype disaster-intelligence assistant built for the IBM Hackathon. It uses watsonx AI and RAG (Retrieval-Augmented Generation) to help communities prepare for, respond to, and recover from cyclone events.

## Features
- Conversational Q&A powered by IBM watsonx
- Document ingestion and semantic search via ChromaDB
- Streamlit-based UI for rapid prototyping

## Setup
```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env   # fill in your API keys
streamlit run app.py
```

## License
MIT
