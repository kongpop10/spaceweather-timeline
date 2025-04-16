# Space Weather Timeline

A Streamlit application that scrapes data from [spaceweather.com](https://spaceweather.com), categorizes space weather events using the Groq LLM API, and displays them in an interactive timeline visualization.

## Features

- **Daily Data Scraping**: Automatically scrapes spaceweather.com for the latest space weather information
- **LLM-Powered Analysis**: Uses Groq's meta-llama/llama-4-maverick-17b-128e-instruct model to categorize and analyze space weather events
- **Interactive Timeline**: Visual representation of space weather events over time
- **Event Categorization**: Organizes events into four main categories:
  1. Coronal Mass Ejections (CME)
  2. Sunspot Activity
  3. Solar Flares
  4. Coronal Holes
- **Significance Highlighting**: Automatically identifies and highlights significant space weather events
- **Detailed Event Cards**: Click on any date to view detailed information about the events on that day

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

3. Set up your Groq API key:
   - Create a `.streamlit/secrets.toml` file with your API key:
     ```
     GROQ_API_KEY = "your-api-key-here"
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
- Refresh the data to get the latest space weather information

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
