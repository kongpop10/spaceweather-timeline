@echo off
echo Running Space Weather Scraping and LLM Test...
python test_scraping_llm.py %1
echo Test completed. Check test_scraping_llm.log for results.
pause
