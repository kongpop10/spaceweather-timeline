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
     GROQ_API_KEY = "your-api-key-here"
     password = "your-admin-password"
     LLM_BASE_URL = "https://api.groq.com/openai/v1/chat/completions"
     LLM_MODEL = "meta-llama/llama-4-maverick-17b-128e-instruct"
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
   - **LLM Configuration**: Update the base URL and model for the LLM
   - **Data Management**: Toggle test dates, view cache status, clear cached data, and refresh data
   - **Logout**: End your admin session

## Project Structure

- `app.py`: Main Streamlit application
- `scraper.py`: Functions to scrape spaceweather.com
- `llm_processor.py`: Functions to process text with Groq LLM
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
- Groq API key

## License

MIT
