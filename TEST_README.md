# Space Weather Scraping and LLM Test

This test script helps diagnose issues with scraping data from spaceweather.com and processing it with the LLM.

## Setup

Before running the test, you need to set up the API key:

1. **Option 1**: Set the API key as an environment variable:
   ```
   set XAI_API_KEY=your-api-key-here
   ```

2. **Option 2**: Add the API key to `.streamlit/secrets.toml`:
   ```toml
   XAI_API_KEY = "your-api-key-here"
   ```

## How to Run the Test

1. Run the test script with a specific date:
   ```
   python test_scraping_llm.py 2023-04-23
   ```

2. Or use the batch file:
   ```
   run_scraping_test.bat 2023-04-23
   ```

3. If no date is provided, today's date will be used.

## Test Output Files

The test script generates several output files for inspection:

- `test_scraping_llm.log`: Detailed log of the test run
- `test_raw_html_YYYY-MM-DD.html`: Raw HTML from spaceweather.com
- `test_extracted_text_YYYY-MM-DD.txt`: Extracted text from the HTML
- `test_sections_YYYY-MM-DD.json`: Extracted sections for LLM processing
- `test_prompt_YYYYMMDD_HHMMSS.txt`: Prompt sent to the LLM
- `test_reasoning_YYYYMMDD_HHMMSS.txt`: Reasoning from the LLM (Grok only)
- `test_response_YYYYMMDD_HHMMSS.json`: Raw response from the LLM
- `test_results_YYYY-MM-DD.json`: Final structured data

## Troubleshooting

If the test fails, check the log file for error messages. Common issues include:

1. **Scraping Failures**:
   - Network connectivity issues
   - Website structure changes
   - Timeout errors

2. **LLM Processing Failures**:
   - Invalid API key
   - Empty or invalid responses from the LLM
   - JSON parsing errors

## Interpreting Results

The test script logs detailed information about each step of the process. Look for:

- Response status codes and content lengths
- Number of snippets found for each category
- LLM response validation
- Total events found in the final structured data

If the LLM returns empty responses, check:
1. The extracted text to ensure it contains meaningful content
2. The prompt to ensure it's properly formatted
3. The LLM API response for any error messages
