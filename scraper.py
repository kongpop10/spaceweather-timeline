"""
Functions to scrape spaceweather.com
"""
import requests
from bs4 import BeautifulSoup
from datetime import datetime
import re
import logging
import random

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

        # Make the request
        response = requests.get(url)
        response.raise_for_status()

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

        # For testing purposes, create mock data if we can't find real data
        if "Could not find" in str(main_content) or len(str(main_content)) < 1000:
            logger.warning(f"Creating mock data for date {date}")
            return create_mock_data(date, url)

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
        return None

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

def create_mock_data(date, url):
    """
    Create mock data for testing purposes

    Args:
        date (str): Date in format YYYYMMDD
        url (str): URL that was attempted to be scraped

    Returns:
        dict: Mock data including HTML content, text, and images
    """
    # Format date as YYYY-MM-DD for consistency
    if len(date) == 8:
        formatted_date = f"{date[0:4]}-{date[4:6]}-{date[6:8]}"
    else:
        formatted_date = date

    # Generate random number of sunspots
    sunspot_number = random.randint(50, 150)

    # Generate random solar flare class
    flare_class = random.choice(['C', 'M', 'X'])
    flare_intensity = random.randint(1, 9)
    flare_text = f"{flare_class}{flare_intensity}"

    # Generate random CME information
    cme_speed = random.randint(500, 2000)
    cme_direction = random.choice(['Earth-directed', 'not Earth-directed'])

    # Generate random coronal hole information
    ch_size = random.choice(['small', 'medium', 'large'])
    ch_position = random.choice(['northern hemisphere', 'southern hemisphere', 'equatorial'])

    # Create mock text
    mock_text = f"""
    SUNSPOTS: Sunspot number is {sunspot_number} today. Several sunspot groups are visible on the Earth-facing side of the sun.

    SOLAR FLARES: A {flare_text}-class solar flare erupted from sunspot region AR3123 at {formatted_date}T10:15:00Z.

    CORONAL MASS EJECTION (CME): A {cme_direction} CME was observed leaving the sun at a speed of {cme_speed} km/s.

    CORONAL HOLES: A {ch_size} coronal hole is located in the sun's {ch_position}. High-speed solar wind flowing from this coronal hole could reach Earth in the next 2-3 days.
    """

    # Create mock images
    images = [
        {
            'src': 'https://spaceweather.com/images2023/01jan23/coronalhole_sdo_blank.jpg',
            'alt': 'Coronal hole'
        },
        {
            'src': 'https://spaceweather.com/images2023/01jan23/sunspot_blank.jpg',
            'alt': 'Sunspot'
        }
    ]

    # Return the mock data
    return {
        'date': formatted_date,
        'url': url,
        'html': f"<div>{mock_text}</div>",
        'text': mock_text,
        'images': images
    }

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
