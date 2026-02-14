# Commodity Lab

A comprehensive data analytics platform for commodity trading and analysis. This project provides tools for data ingestion, quality control, feature engineering, strategy development, backtesting, and real-time monitoring.

## Features

- **📊 Data Catalog**: Browse and manage commodity data sources
- **📥 Data Ingestion**: Import historical price data from Yahoo Finance
- **✅ Quality Control**: Validate and clean data with automated QC checks
- **🔄 Data Transforms**: Apply unit conversions and FX normalization
- **🔧 Feature Engineering**: Create and manage trading features
- **📈 Strategy Development**: Build and test trading strategies
- **⏮️ Backtesting**: Simulate strategy performance on historical data
- **🔔 Monitoring**: Real-time monitoring and alerts

## Project Structure

```
Commodity-Lab/
├── app/                          # Streamlit web application
│   ├── main.py                   # Main app entry point
│   └── pages/                    # Multi-page app pages
│       ├── 0_Catalog.py         # Data catalog page
│       ├── 1_Data.py            # Data ingestion page
│       ├── 2_QC.py              # Quality control page
│       ├── 2_Transforms.py      # Data transforms page
│       ├── 3_Features.py        # Feature engineering page
│       ├── 4_Strategies.py      # Strategy development page
│       ├── 5_Backtest.py        # Backtesting page
│       └── 6_Monitor.py         # Monitoring page
├── core/                         # Core business logic
│   ├── db.py                    # Database operations (DuckDB)
│   ├── refresh.py               # Data refresh logic
│   ├── qc.py                    # Quality control functions
│   ├── transforms.py            # Data transformation functions
│   ├── features.py              # Feature engineering
│   ├── strategies.py            # Strategy definitions
│   ├── backtest.py              # Backtesting engine
│   ├── monitor.py               # Monitoring functions
│   ├── yf_provider.py           # Yahoo Finance provider
│   ├── yf_prices.py             # Price fetching functions
│   ├── yf_search.py             # Search functionality
│   ├── io.py                    # I/O utilities
│   ├── schema.py                # Data schema definitions
│   └── watch.py                 # Watch list management
├── data/                         # Data storage
│   └── commodity_lab.duckdb     # DuckDB database
├── pyproject.toml               # Project configuration and dependencies
└── README.md                    # This file
```

## Requirements

- Python 3.12+
- See `pyproject.toml` for detailed dependencies

## Installation

1. **Clone the repository**:
```bash
git clone <repository-url>
cd Commodity-Lab
```

2. **Install the project with dependencies**:
```bash
pip install -e .
```

The `-e` flag installs the project in editable mode, allowing changes to be reflected immediately without reinstalling.

## Usage

Run the Streamlit application:

```bash
streamlit run app/main.py
```

This will start a local web server (typically at `http://localhost:8501`) where you can access the application.

## Workflow

1. **Start with Data**: Go to the Data page to ingest commodity price data
2. **Quality Control**: Use the QC page to validate data integrity
3. **Transforms**: Apply unit and FX standardization as needed
4. **Features**: Engineer features for analysis
5. **Strategies**: Develop trading strategies
6. **Backtest**: Test strategy performance on historical data
7. **Monitor**: Set up real-time monitoring and alerts

## Technologies

- **Streamlit**: Web application framework
- **Pandas**: Data manipulation and analysis
- **DuckDB**: Lightweight SQL database for data storage
- **yfinance**: Financial data fetching
- **Plotly**: Interactive visualizations

## Development

To work with the project:

```bash
# Install in development mode
pip install -e .

# Run the app
streamlit run app/main.py

# Run specific pages for testing
streamlit run app/pages/0_Catalog.py
```

## Database

The project uses DuckDB for data storage. The database file is located at `data/commodity_lab.duckdb`.

## License

[Add your license information here]

## Contributing

[Add contribution guidelines here]