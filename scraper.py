"""
Functions to scrape spaceweather.com
"""
import requests
from bs4 import BeautifulSoup
from datetime import datetime
import re
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def scrape_spaceweather(date=None):
    """
    Scrape spaceweather.com for a specific date

    Args:
        date (str, optional): Date in format YYYYMMDD. Defaults to today.

    Returns:
        dict: Scraped data including HTML content, text, and images
    """
    try:
        today = datetime.now()

        # If no date is provided, use today's date
        if date is None:
            date = today.strftime("%Y%m%d")
        elif isinstance(date, str) and len(date) == 10 and "-" in date:
            # Convert YYYY-MM-DD to YYYYMMDD
            date = date.replace("-", "")

            # Check if the date is in the future
            date_obj = datetime.strptime(date, "%Y%m%d")
            if date_obj > today:
                logger.warning(f"Date {date} is in the future. Using today's date instead.")
                date = today.strftime("%Y%m%d")

        # Construct URL
        base_url = "https://spaceweather.com"
        url = base_url

        # If not today, use the archive URL
        if date != today.strftime("%Y%m%d"):
            url = f"{base_url}/archive.php?view=1&day={date[6:8]}&month={date[4:6]}&year={date[0:4]}"

        logger.info(f"Scraping URL: {url}")

        # Make the request with timeout and retries
        max_retries = 3
        retry_count = 0
        timeout = 10  # 10 seconds timeout

        while retry_count < max_retries:
            try:
                logger.info(f"Attempting to scrape {url} (attempt {retry_count + 1}/{max_retries})")
                response = requests.get(url, timeout=timeout)
                response.raise_for_status()
                break  # Success, exit the loop
            except requests.exceptions.Timeout:
                retry_count += 1
                if retry_count >= max_retries:
                    logger.error(f"Timeout error after {max_retries} attempts: {url}")
                    raise
                logger.warning(f"Timeout error, retrying ({retry_count}/{max_retries}): {url}")
            except requests.exceptions.RequestException as e:
                retry_count += 1
                if retry_count >= max_retries:
                    logger.error(f"Request error after {max_retries} attempts: {e}")
                    raise
                logger.warning(f"Request error, retrying ({retry_count}/{max_retries}): {e}")

        # Parse the HTML
        soup = BeautifulSoup(response.text, 'html.parser')

        # Extract the main content
        main_content = soup.find('td', width="100%")
        if not main_content:
            # Try alternative selectors
            main_content = soup.find('div', class_='content')
            if not main_content:
                main_content = soup.find('body')

        if not main_content:
            logger.warning(f"Could not find main content for date {date}")
            return None

        # Check if content is too small or contains error message
        if "Could not find" in str(main_content) or len(str(main_content)) < 1000:
            logger.warning(f"Insufficient content found for date {date}")
            return None

        # Extract all text
        all_text = main_content.get_text()

        # Extract all images
        images = []
        for img in main_content.find_all('img'):
            src = img.get('src', '')
            if src and not src.startswith('http'):
                src = f"{base_url}/{src}"
            if src:
                alt = img.get('alt', '')
                images.append({
                    'src': src,
                    'alt': alt
                })

        # Format date as YYYY-MM-DD for consistency
        formatted_date = f"{date[0:4]}-{date[4:6]}-{date[6:8]}"

        # Return the scraped data
        return {
            'date': formatted_date,
            'url': url,
            'html': str(main_content),
            'text': all_text,
            'images': images
        }

    except Exception as e:
        logger.error(f"Error scraping spaceweather.com: {e}")
        return None

def extract_spaceweather_sections(scraped_data):
    """
    Extract relevant sections from the scraped data

    Args:
        scraped_data (dict): Data scraped from spaceweather.com

    Returns:
        dict: Extracted sections
    """
    if not scraped_data:
        logger.warning("No scraped data provided for extraction")
        return {
            'cme': [],
            'sunspot': [],
            'flares': [],
            'coronal_holes': [],
            'full_text': 'No data available',
            'date': 'unknown',
            'url': 'unknown',
            'images': []
        }

    text = scraped_data['text']

    # Extract sections related to our categories of interest
    sections = {
        'cme': extract_text_around_keywords(text, ['coronal mass ejection', 'CME', 'filament eruption']),
        'sunspot': extract_text_around_keywords(text, ['sunspot', 'sunspots', 'AR']),
        'flares': extract_text_around_keywords(text, ['solar flare', 'X-class', 'M-class', 'C-class']),
        'coronal_holes': extract_text_around_keywords(text, ['coronal hole', 'solar wind'])
    }

    # Add the full text for LLM processing
    sections['full_text'] = text

    # Add date and URL
    sections['date'] = scraped_data['date']
    sections['url'] = scraped_data['url']

    # Add images
    sections['images'] = scraped_data['images']

    return sections



def extract_text_around_keywords(text, keywords, context_chars=500):
    """
    Extract text around keywords with context

    Args:
        text (str): The text to search in
        keywords (list): List of keywords to search for
        context_chars (int): Number of characters to include before and after the keyword

    Returns:
        list: List of text snippets containing the keywords with context
    """
    snippets = []

    for keyword in keywords:
        # Find all occurrences of the keyword (case insensitive)
        for match in re.finditer(re.escape(keyword), text, re.IGNORECASE):
            start = max(0, match.start() - context_chars)
            end = min(len(text), match.end() + context_chars)
            snippet = text[start:end]
            snippets.append(snippet)

    # Remove duplicates while preserving order
    unique_snippets = []
    for snippet in snippets:
        if snippet not in unique_snippets:
            unique_snippets.append(snippet)

    return unique_snippets
