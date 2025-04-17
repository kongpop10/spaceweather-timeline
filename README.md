# Space Weather Timeline

A Streamlit application that scrapes data from [spaceweather.com](https://spaceweather.com), categorizes space weather events using configurable LLM models, and displays them in an interactive timeline visualization with an admin dashboard for data management and configuration.

## Features

- **Daily Data Scraping**: Automatically scrapes spaceweather.com for the latest space weather information
- **LLM-Powered Analysis**: Uses configurable LLM models to categorize and analyze space weather events
- **Interactive Timeline**: Visual representation of space weather events over time
- **Event Categorization**: Organizes events into four main categories:
  1. Coronal Mass Ejections (CME)
  2. Sunspot Activity
  3. Solar Flares
  4. Coronal Holes
- **Significance Highlighting**: Automatically identifies and highlights significant space weather events
- **Detailed Event Cards**: Click on any date to view detailed information about the events on that day
- **Admin Dashboard**: Password-protected admin section for data management and LLM configuration

## Installation

1. Clone this repository:
   ```
   git clone https://github.com/yourusername/spaceweather-timeline.git
   cd spaceweather-timeline
   ```

2. Install the required dependencies:
   ```
   pip install -r requirements.txt
   ```

3. Set up your configuration:
   - Create a `.streamlit/secrets.toml` file with the following settings:
     ```
     # API Keys
     GROQ_API_KEY = "your-groq-api-key-here"
     OPENROUTER_API_KEY = "your-openrouter-api-key-here"
     XAI_API_KEY = "your-xai-api-key-here"

     # Admin password
     password = "your-admin-password"

     # LLM Configuration
     LLM_PROVIDER = "grok"  # Options: "grok" or "openrouter"
     LLM_BASE_URL = "https://api.x.ai/v1"
     LLM_MODEL = "grok-3-mini-beta"
     LLM_REASONING_EFFORT = "low"  # Options: "low", "medium", "high" (for Grok model)

     # Site information for OpenRouter
     SITE_URL = "https://spaceweather-timeline.streamlit.app"
     SITE_NAME = "Space Weather Timeline"
     ```

## Usage

Run the Streamlit app:
```
streamlit run app.py
```

The app will open in your default web browser. You can:
- Adjust the date range using the slider in the sidebar
- Filter events by category using the checkboxes
- Click on any date in the timeline to view detailed event information

### Admin Features

To access the admin features:
1. Click on the "⚙️ Admin" expander in the sidebar
2. Enter your admin password and click "Login"
3. Once authenticated, you'll have access to:
   - **LLM Configuration**: Select between Grok and OpenRouter LLM providers, and configure their settings
   - **Data Management**: View cache status, clear cached data, and refresh data
   - **Controls**: Adjust display settings and filter event categories
   - **Logout**: End your admin session

## Project Structure

- `app.py`: Main Streamlit application
- `scraper.py`: Functions to scrape spaceweather.com
- `llm_processor.py`: Functions to process text with Grok or OpenRouter LLM
- `data_manager.py`: Functions to store and retrieve data
- `utils.py`: Utility functions
- `data/`: Directory where scraped and processed data is stored

## Requirements

- Python 3.7+
- Streamlit
- Requests
- BeautifulSoup4
- Pandas
- Plotly
- Grok API key (X.AI) or OpenRouter API key

## License

MIT
