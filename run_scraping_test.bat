@echo off
echo Running Space Weather Scraping and LLM Test...
echo.
echo Make sure you have set the XAI_API_KEY environment variable or added it to .streamlit/secrets.toml
echo.
python test_scraping_llm.py %1
echo.
echo Test completed. Check test_scraping_llm.log for results.
pause
