#!/usr/bin/env python
"""
Test script to diagnose scraping and LLM processing issues
"""
import os
import json
import logging
import sys
from datetime import datetime
import requests
from bs4 import BeautifulSoup
from openai import OpenAI

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('test_scraping_llm.log')
    ]
)
logger = logging.getLogger(__name__)

# Load API keys from environment or hardcode for testing
XAI_API_KEY = os.environ.get("XAI_API_KEY", "xai-JHsClEY97RbmCUpt65nhH3aZeAE6GFZ2SGJ8ZD4m6a7mgAZY4sJsGDidCjDJYLZs5CjwnZyPBaJwImsd")

def scrape_spaceweather(date_str):
    """
    Scrape spaceweather.com for a specific date
    
    Args:
        date_str (str): Date in format YYYY-MM-DD
        
    Returns:
        dict: Scraped data
    """
    logger.info(f"Testing scraping for date: {date_str}")
    
    try:
        # Convert YYYY-MM-DD to YYYYMMDD
        date = date_str.replace("-", "")
        
        # Construct URL
        base_url = "https://spaceweather.com"
        
        # If not today, use the archive URL
        today = datetime.now().strftime("%Y%m%d")
        if date != today:
            url = f"{base_url}/archive.php?view=1&day={date[6:8]}&month={date[4:6]}&year={date[0:4]}"
        else:
            url = base_url
            
        logger.info(f"Scraping URL: {url}")
        
        # Make the request with timeout and retries
        max_retries = 3
        retry_count = 0
        timeout = 15  # 15 seconds timeout
        
        while retry_count < max_retries:
            try:
                logger.info(f"Attempting to scrape {url} (attempt {retry_count + 1}/{max_retries})")
                response = requests.get(url, timeout=timeout)
                response.raise_for_status()
                
                # Log response info
                logger.info(f"Response status code: {response.status_code}")
                logger.info(f"Response content length: {len(response.text)} bytes")
                
                # Save raw HTML for inspection
                with open(f"test_raw_html_{date_str}.html", "w", encoding="utf-8") as f:
                    f.write(response.text)
                logger.info(f"Raw HTML saved to test_raw_html_{date_str}.html")
                
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
            logger.warning(f"Could not find main content for date {date_str}")
            return None
        
        # Check if content is too small or contains error message
        if "Could not find" in str(main_content) or len(str(main_content)) < 1000:
            logger.warning(f"Insufficient content found for date {date_str}")
            return None
        
        # Extract all text
        all_text = main_content.get_text()
        logger.info(f"Extracted text length: {len(all_text)} characters")
        
        # Save extracted text for inspection
        with open(f"test_extracted_text_{date_str}.txt", "w", encoding="utf-8") as f:
            f.write(all_text)
        logger.info(f"Extracted text saved to test_extracted_text_{date_str}.txt")
        
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
        
        logger.info(f"Found {len(images)} images")
        
        # Return the scraped data
        return {
            'date': date_str,
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
    
    # Log section information
    for section, snippets in sections.items():
        logger.info(f"Found {len(snippets)} snippets for {section}")
        if snippets:
            logger.info(f"Sample {section} snippet: {snippets[0][:100]}...")
    
    # Add the full text for LLM processing
    sections['full_text'] = text
    
    # Add date and URL
    sections['date'] = scraped_data['date']
    sections['url'] = scraped_data['url']
    
    # Add images
    sections['images'] = scraped_data['images']
    
    # Save sections for inspection
    with open(f"test_sections_{scraped_data['date']}.json", "w", encoding="utf-8") as f:
        json.dump(sections, f, indent=2)
    logger.info(f"Sections saved to test_sections_{scraped_data['date']}.json")
    
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
    import re
    
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

def call_llm(prompt, provider="grok"):
    """
    Call the LLM API
    
    Args:
        prompt (str): The prompt to send to the LLM
        provider (str): The LLM provider to use
        
    Returns:
        str: The LLM response
    """
    logger.info(f"Testing LLM call with provider: {provider}")
    
    # Save prompt for inspection
    with open(f"test_prompt_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt", "w", encoding="utf-8") as f:
        f.write(prompt)
    logger.info("Prompt saved to test_prompt file")
    
    try:
        # Configure API parameters
        if provider == "grok":
            base_url = "https://api.x.ai/v1"
            api_key = XAI_API_KEY
            model = "grok-3-mini-beta"
            reasoning_effort = "high"  # Try high reasoning effort for testing
        else:
            logger.error(f"Unsupported provider: {provider}")
            return None
        
        # Create OpenAI client
        client = OpenAI(
            base_url=base_url,
            api_key=api_key,
        )
        
        # Common parameters
        common_params = {
            "model": model,
            "messages": [
                {"role": "system", "content": "You are a helpful space weather expert that analyzes data from spaceweather.com and provides structured information about space weather events. Always respond with valid JSON."},
                {"role": "user", "content": prompt}
            ],
            "temperature": 0.2,
            "max_tokens": 4000,
            "response_format": {"type": "json_object"}  # Request JSON format explicitly
        }
        
        # Add provider-specific parameters
        if provider == "grok":
            common_params["reasoning_effort"] = reasoning_effort
            logger.info(f"Using Grok model: {model} with reasoning_effort: {reasoning_effort}")
        
        # Call the API
        logger.info("Sending request to LLM API...")
        completion = client.chat.completions.create(**common_params)
        
        # Extract the response content
        content = completion.choices[0].message.content
        
        # For Grok, also log reasoning content if available
        if provider == "grok" and hasattr(completion.choices[0].message, 'reasoning_content'):
            reasoning = completion.choices[0].message.reasoning_content
            logger.info(f"Grok reasoning: {reasoning[:200]}...")
            
            # Save reasoning for inspection
            with open(f"test_reasoning_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt", "w", encoding="utf-8") as f:
                f.write(reasoning)
            logger.info("Reasoning saved to test_reasoning file")
        
        # Check if the content is empty or doesn't contain valid JSON
        if not content:
            logger.warning("LLM returned empty response")
            return None
            
        # Log the response
        logger.info(f"LLM response length: {len(content)} characters")
        logger.info(f"LLM response sample: {content[:200]}...")
        
        # Save response for inspection
        with open(f"test_response_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json", "w", encoding="utf-8") as f:
            f.write(content)
        logger.info("Response saved to test_response file")
        
        # Validate JSON
        try:
            json_data = json.loads(content)
            logger.info("Response is valid JSON")
            return content
        except json.JSONDecodeError as e:
            logger.error(f"Response is not valid JSON: {e}")
            return None
        
    except Exception as e:
        logger.error(f"Error calling LLM API: {e}")
        return None

def create_analysis_prompt(sections):
    """
    Create a prompt for the LLM to analyze spaceweather data
    
    Args:
        sections (dict): Extracted sections from spaceweather.com
        
    Returns:
        str: Prompt for the LLM
    """
    date = sections.get('date', 'unknown date')
    
    prompt = f"""You are a space weather expert analyzing data from spaceweather.com for {date}.

I will provide you with text snippets from the website, and I need you to identify and categorize space weather events into the following categories:

1. Coronal mass ejection (CME) - Including filament eruptions, their size, and whether they are Earth-facing or not
2. Sunspot activity - Including expansion, creation, extreme maximum or extreme minimum
3. Solar flares - Including C, M, and X class flares
4. Coronal holes - Including coronal holes facing Earth or high-speed solar winds

For each event you identify, please provide the following structured information:
1. Tone of the event: "Normal" or "Significant" (significant means it could have notable effects on Earth or represents an unusual/extreme event)
2. Date of the event (when it was observed)
3. Predicted arrival time at Earth (if mentioned)
4. Detailed description of the event (you can include basic HTML formatting like <p>, <strong>, <em>, <ul>, <li> tags in the detail field)
5. Any image or link associated with this event (if available in the provided data)

Here are the text snippets from the website:

FULL TEXT:
{sections.get('full_text', 'No full text available')}

CME RELATED:
{json.dumps(sections.get('cme', []), indent=2)}

SUNSPOT RELATED:
{json.dumps(sections.get('sunspot', []), indent=2)}

SOLAR FLARES RELATED:
{json.dumps(sections.get('flares', []), indent=2)}

CORONAL HOLES RELATED:
{json.dumps(sections.get('coronal_holes', []), indent=2)}

IMAGES:
{json.dumps(sections.get('images', []), indent=2)}

Please respond with a JSON structure that categorizes all the events you can identify from this data. Use the following format:

```json
{{
  "date": "{date}",
  "events": {{
    "cme": [
      {{
        "tone": "Normal/Significant",
        "date": "{date}",
        "predicted_arrival": null,
        "detail": "Detailed description",
        "image_url": null
      }}
    ],
    "sunspot": [...],
    "flares": [...],
    "coronal_holes": [...]
  }}
}}
```

Only include events that are explicitly mentioned in the provided text. If no events are found for a category, return an empty array for that category. Ensure your response is valid JSON.

IMPORTANT: If you can't find any specific events in the text, please still return a valid JSON structure with the date and empty arrays for each category. DO NOT return null or an empty response.

IMPORTANT: Your response MUST be valid JSON. Double-check your response before returning it.
"""
    
    return prompt

def parse_llm_response(response, sections):
    """
    Parse the LLM response into structured data
    
    Args:
        response (str): The LLM response
        sections (dict): The original sections data
        
    Returns:
        dict: Structured data with categorized events
    """
    # Check if response is None or empty
    if response is None or not response.strip():
        logger.warning(f"LLM returned None or empty response for date {sections.get('date')}")
        return {
            "date": sections.get("date"),
            "url": sections.get("url"),
            "events": {
                "cme": [],
                "sunspot": [],
                "flares": [],
                "coronal_holes": []
            },
            "error": "LLM returned None or empty response"
        }
    
    try:
        # Log the raw response for debugging
        logger.debug(f"Raw LLM response for {sections.get('date')}: {response[:200]}...")
        
        # Extract JSON from the response (it might be wrapped in ```json ... ```)
        json_str = response
        if "```json" in response:
            json_str = response.split("```json")[1].split("```")[0].strip()
        elif "```" in response:
            # Try to find any code block
            parts = response.split("```")
            if len(parts) >= 3:  # At least one complete code block
                json_str = parts[1].strip()
        
        # Try to find JSON object if no code blocks were found
        if not json_str.strip().startswith('{'):
            # Look for a JSON object starting with { and ending with }
            import re
            json_match = re.search(r'(\{.*?\})', response, re.DOTALL)
            if json_match:
                json_str = json_match.group(1)
        
        # Log the extracted JSON string for debugging
        logger.debug(f"Extracted JSON for {sections.get('date')}: {json_str[:200]}...")
        
        # Parse the JSON
        data = json.loads(json_str)
        
        # Add the original URL
        data["url"] = sections.get("url")
        
        # Ensure date is present
        if "date" not in data:
            data["date"] = sections.get("date")
        
        # Ensure all required fields exist
        if "events" not in data:
            data["events"] = {}
        
        for category in ["cme", "sunspot", "flares", "coronal_holes"]:
            if category not in data["events"]:
                data["events"][category] = []
        
        return data
        
    except Exception as e:
        logger.error(f"Error parsing LLM response: {e}")
        logger.error(f"Problematic response: {response[:500]}...")
        
        # Fallback: create a basic structure
        return {
            "date": sections.get("date"),
            "url": sections.get("url"),
            "events": {
                "cme": [],
                "sunspot": [],
                "flares": [],
                "coronal_holes": []
            },
            "error": str(e)
        }

def main():
    """
    Main function to test scraping and LLM processing
    """
    # Get date from command line argument or use today's date
    if len(sys.argv) > 1:
        date_str = sys.argv[1]
    else:
        date_str = datetime.now().strftime("%Y-%m-%d")
    
    logger.info(f"Starting test for date: {date_str}")
    
    # Step 1: Scrape data
    scraped_data = scrape_spaceweather(date_str)
    
    if not scraped_data:
        logger.error("Scraping failed. Exiting.")
        return
    
    # Step 2: Extract sections
    sections = extract_spaceweather_sections(scraped_data)
    
    # Step 3: Create prompt
    prompt = create_analysis_prompt(sections)
    
    # Step 4: Call LLM
    llm_response = call_llm(prompt)
    
    if not llm_response:
        logger.error("LLM call failed. Exiting.")
        return
    
    # Step 5: Parse response
    structured_data = parse_llm_response(llm_response, sections)
    
    # Step 6: Save results
    with open(f"test_results_{date_str}.json", "w", encoding="utf-8") as f:
        json.dump(structured_data, f, indent=2)
    logger.info(f"Results saved to test_results_{date_str}.json")
    
    # Step 7: Print summary
    events = structured_data.get("events", {})
    total_events = sum(len(events.get(cat, [])) for cat in ["cme", "sunspot", "flares", "coronal_holes"])
    logger.info(f"Test completed for {date_str}. Found {total_events} events.")
    
    for category, category_events in events.items():
        logger.info(f"  - {category}: {len(category_events)} events")

if __name__ == "__main__":
    main()
