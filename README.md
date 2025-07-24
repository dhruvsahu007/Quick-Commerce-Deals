# Quick Commerce Price Comparison App 🛒

A Streamlit-based application that helps you compare prices across popular quick commerce platforms (Zepto, Blinkit, and Swiggy Instamart) using natural language queries powered by LangChain SQL agents and OpenAI.

## 🌟 Live Repository
**GitHub:** [https://github.com/dhruvsahu007/Quick-Commerce-Deals](https://github.com/dhruvsahu007/Quick-Commerce-Deals)

## Features ✨

- **Natural Language Queries**: Ask questions in plain English like "Which app has cheapest onions?"
- **Multi-Platform Comparison**: Compare prices across Zepto, Blinkit, and Swiggy Instamart
- **Interactive Visualizations**: Price comparison charts and discount analysis
- **Smart SQL Generation**: Uses OpenAI GPT to convert questions into SQL queries
- **Real-time Results**: Instant price comparisons and deal discovery

## Project Structure 📁

```
quick_commerce_deals/
├── databases/
│   ├── zepto.db          # Zepto products database
│   ├── blinkit.db        # Blinkit products database
│   └── swiggy.db         # Swiggy Instamart products database
├── generate_data.py      # Database creation and population script
├── app.py               # Main Streamlit application
├── query_engine.py      # LangChain SQL agents engine
├── run.py               # Application launcher script
├── requirements.txt     # Python dependencies
├── .env                # Environment variables (OpenAI API key)
├── .gitignore          # Git ignore rules
└── README.md           # This file
```
└── README.md           # This file
```

## Setup Instructions 🚀

### 0. Clone the Repository

```bash
git clone https://github.com/dhruvsahu007/Quick-Commerce-Deals.git
cd Quick-Commerce-Deals
```

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

### 2. Configure OpenAI API Key

1. Get your OpenAI API key from [OpenAI Platform](https://platform.openai.com/api-keys)
2. Copy the example environment file:
   ```bash
   cp .env.example .env
   ```
3. Update the `.env` file with your actual API key:
   ```env
   OPENAI_API_KEY=your_actual_openai_api_key_here
   ```

### 3. Create and Populate Databases

```bash
python generate_data.py
```

This will create three SQLite databases with sample product data:
- `databases/zepto.db`
- `databases/blinkit.db` 
- `databases/swiggy.db`

### 4. Run the Application

**Option 1: Using the launcher script**
```bash
python run.py
```

**Option 2: Direct streamlit command**
```bash
streamlit run app.py
```

The app will open in your browser at `http://localhost:8501`

## Database Schema 📊

Each database contains a `products` table with the following structure:

| Column | Type | Description |
|--------|------|-------------|
| id | INTEGER | Primary key |
| name | TEXT | Product name |
| category | TEXT | Product category (Fruits, Vegetables, Snacks, etc.) |
| price | REAL | Price in rupees |
| discount_percentage | REAL | Discount percentage (0-100) |
| availability | BOOLEAN | Product availability (1=available, 0=not available) |

## Sample Questions 💭

Try these sample questions in the app:

- "Which app has the cheapest onions?"
- "Compare apple prices between all platforms"
- "Show me all fruits available on Zepto"
- "What are the most expensive items on Blinkit?"
- "Find products with more than 20% discount"
- "Compare milk prices across all apps"
- "Show me all snacks under 30 rupees"
- "Which platform has the best vegetable prices?"

## How It Works 🔧

1. **User Input**: Enter a natural language question
2. **AI Processing**: OpenAI GPT converts the question to SQL queries
3. **Database Query**: Execute queries across relevant databases
4. **Results Aggregation**: Combine and format results
5. **Visualization**: Display results with interactive charts

## Technology Stack 💻

- **Frontend**: Streamlit
- **Database**: SQLite
- **AI/ML**: OpenAI GPT-3.5 with LangChain
- **SQL Agents**: LangChain SQL Agent Toolkit
- **RAG System**: FAISS + OpenAI Embeddings
- **Data Processing**: Pandas
- **Environment**: Python 3.8+

## Features in Detail 🔍

### LangChain SQL Agents
- Intelligent tool calling for database operations
- Dynamic SQL query generation and execution
- RAG-enhanced context for better query understanding
- Multi-database coordination

### Interactive Dashboard
- Real-time price comparisons via AI agents
- Natural language to SQL conversion
- Platform-wise intelligent breakdowns
- Summary statistics

### Smart Query Engine
- Automatic database selection
- Query optimization
- Error handling and recovery
- Query explanation and transparency

## Troubleshooting 🛠️

### Common Issues

1. **OpenAI API Key Error**
   - Ensure your API key is correctly set in `.env`
   - Check if you have sufficient OpenAI credits

2. **Database Not Found**
   - Run `python generate_data.py` to create databases
   - Check if `databases/` directory exists

3. **Import Errors**
   - Install all requirements: `pip install -r requirements.txt`
   - Ensure you're using Python 3.8+

### Getting Help

If you encounter issues:
1. Check the Streamlit console for error messages
2. Verify all dependencies are installed
3. Ensure database files exist in the `databases/` directory

## Contributing 🤝

Feel free to contribute by:
- Adding more sample data
- Improving query generation
- Adding new visualization types
- Enhancing the UI/UX

## License 📄

This project is open source and available under the MIT License.

---

Built with ❤️ using Streamlit, OpenAI, and SQLite
