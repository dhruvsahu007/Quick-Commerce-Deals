# Quick Commerce Deals - Price Comparison Platform

A sophisticated price comparison platform for quick commerce apps (Blinkit, Zepto, Instamart, BigBasket Now, etc.) that tracks real-time pricing, discounts, and availability across multiple platforms using natural language queries.

## Features

- **Multi-Platform Price Tracking**: Real-time price monitoring across 10+ quick commerce platforms
- **Natural Language Queries**: SQL agent that understands complex queries in plain English
- **Intelligent Table Selection**: Semantic indexing for optimal query planning across 50+ tables
- **Performance Optimized**: Connection pooling, caching, and query optimization
- **Real-time Updates**: Simulated real-time price updates with dummy data
- **Web Interface**: User-friendly web interface for price comparison

## Architecture

```
├── database/           # Database schemas and models
├── agents/            # SQL agent and query processing
├── api/               # FastAPI backend
├── web/               # Streamlit web interface
├── data/              # Data generation and simulation
├── cache/             # Caching strategies
├── monitoring/        # Performance monitoring
└── config/            # Configuration files
```

## Quick Start

1. Install dependencies:
```bash
pip install -r requirements.txt
```

2. Initialize database:
```bash
python database/init_db.py
```

3. Start data simulation:
```bash
python data/simulate_data.py
```

4. Run the application:
```bash
streamlit run web/app.py
```

## Sample Queries

- "Which app has cheapest onions right now?"
- "Show products with 30%+ discount on Blinkit"
- "Compare fruit prices between Zepto and Instamart"
- "Find best deals for ₹1000 grocery list"

## Technology Stack

- **Backend**: FastAPI, SQLAlchemy
- **Database**: SQLite (with connection pooling)
- **AI/ML**: LangChain, OpenAI GPT
- **Frontend**: Streamlit
- **Caching**: Redis-like in-memory caching
- **Monitoring**: Custom query performance tracking
