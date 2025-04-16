"""
Functions to process text with Groq LLM
"""
import json
import requests
import streamlit as st
import logging
import random
import re

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def get_groq_api_key():
    """Get the Groq API key from Streamlit secrets"""
    try:
        return st.secrets["GROQ_API_KEY"]
    except Exception as e:
        logger.warning(f"Error getting Groq API key: {e}")
        return "dummy_api_key_for_testing"

def analyze_spaceweather_data(sections):
    """
    Analyze spaceweather data using Groq LLM

    Args:
        sections (dict): Extracted sections from spaceweather.com

    Returns:
        dict: Structured data with categorized events
    """
    if not sections:
        return None

    # Prepare the prompt
    prompt = create_analysis_prompt(sections)

    # Call the LLM
    try:
        response = call_groq_llm(prompt)

        # Parse the response
        structured_data = parse_llm_response(response, sections)

        return structured_data

    except Exception as e:
        logger.error(f"Error analyzing spaceweather data: {e}")
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
4. Detailed description of the event
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
        "date": "YYYY-MM-DD",
        "predicted_arrival": "YYYY-MM-DD" or null,
        "detail": "Detailed description",
        "image_url": "URL" or null
      }}
    ],
    "sunspot": [...],
    "flares": [...],
    "coronal_holes": [...]
  }}
}}
```

Only include events that are explicitly mentioned in the provided text. If no events are found for a category, return an empty array for that category. Ensure your response is valid JSON.
"""

    return prompt

def call_groq_llm(prompt):
    """
    Call the Groq LLM API

    Args:
        prompt (str): The prompt to send to the LLM

    Returns:
        str: The LLM response
    """
    api_key = get_groq_api_key()
    url = "https://api.groq.com/openai/v1/chat/completions"

    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }

    data = {
        "model": "meta-llama/llama-4-maverick-17b-128e-instruct",
        "messages": [
            {"role": "system", "content": "You are a helpful space weather expert that analyzes data from spaceweather.com and provides structured information about space weather events."},
            {"role": "user", "content": prompt}
        ],
        "temperature": 0.2,
        "max_tokens": 4000
    }

    try:
        # For testing purposes, if we're using a dummy API key, return a mock response
        if api_key == "dummy_api_key_for_testing":
            logger.warning("Using mock LLM response for testing")
            return create_mock_llm_response(prompt)

        response = requests.post(url, headers=headers, json=data)
        response.raise_for_status()

        result = response.json()
        return result["choices"][0]["message"]["content"]

    except Exception as e:
        logger.error(f"Error calling Groq LLM API: {e}")
        # Return a mock response for testing
        logger.warning("Falling back to mock LLM response")
        return create_mock_llm_response(prompt)

def create_mock_llm_response(prompt):
    """
    Create a mock LLM response for testing purposes

    Args:
        prompt (str): The prompt that would have been sent to the LLM

    Returns:
        str: A mock LLM response in JSON format
    """
    # Extract date from the prompt
    date_match = re.search(r'for (\d{4}-\d{2}-\d{2})', prompt)
    if date_match:
        date = date_match.group(1)
    else:
        date = "2023-04-15"  # Default date

    # Generate random events
    cme_events = []
    sunspot_events = []
    flare_events = []
    coronal_hole_events = []

    # Add a random number of events for each category
    if random.random() > 0.3:  # 70% chance of having a CME event
        cme_events.append({
            "tone": random.choice(["Normal", "Significant"]),
            "date": date,
            "predicted_arrival": random.choice([None, f"{date}T{random.randint(0, 23):02d}:{random.randint(0, 59):02d}:00Z"]),
            "detail": f"A {'Earth-directed' if random.random() > 0.5 else 'non-Earth-directed'} CME was observed leaving the sun at a speed of {random.randint(500, 2000)} km/s.",
            "image_url": random.choice([None, "https://spaceweather.com/images2023/01jan23/cme_blank.jpg"])
        })

    if random.random() > 0.2:  # 80% chance of having a sunspot event
        sunspot_events.append({
            "tone": random.choice(["Normal", "Significant"]),
            "date": date,
            "predicted_arrival": None,
            "detail": f"Sunspot AR{random.randint(3000, 3999)} is {'growing' if random.random() > 0.5 else 'stable'} with a {'beta-gamma-delta' if random.random() > 0.7 else 'beta'} magnetic configuration.",
            "image_url": random.choice([None, "https://spaceweather.com/images2023/01jan23/sunspot_blank.jpg"])
        })

    if random.random() > 0.4:  # 60% chance of having a solar flare event
        flare_class = random.choice(['C', 'M', 'X'])
        flare_intensity = random.randint(1, 9)
        flare_events.append({
            "tone": "Significant" if flare_class == 'X' else ("Normal" if flare_class == 'C' else random.choice(["Normal", "Significant"])),
            "date": date,
            "predicted_arrival": None,
            "detail": f"A {flare_class}{flare_intensity} solar flare erupted from sunspot region AR{random.randint(3000, 3999)} at {date}T{random.randint(0, 23):02d}:{random.randint(0, 59):02d}:00Z.",
            "image_url": random.choice([None, "https://spaceweather.com/images2023/01jan23/flare_blank.jpg"])
        })

    if random.random() > 0.5:  # 50% chance of having a coronal hole event
        ch_size = random.choice(['small', 'medium', 'large'])
        ch_position = random.choice(['northern hemisphere', 'southern hemisphere', 'equatorial'])
        coronal_hole_events.append({
            "tone": "Significant" if ch_size == 'large' and ch_position == 'equatorial' else "Normal",
            "date": date,
            "predicted_arrival": random.choice([None, f"{date}T{random.randint(0, 23):02d}:{random.randint(0, 59):02d}:00Z"]),
            "detail": f"A {ch_size} coronal hole is located in the sun's {ch_position}. High-speed solar wind flowing from this coronal hole could reach Earth in the next 2-3 days.",
            "image_url": random.choice([None, "https://spaceweather.com/images2023/01jan23/coronalhole_sdo_blank.jpg"])
        })

    # Create the mock response
    mock_response = {
        "date": date,
        "events": {
            "cme": cme_events,
            "sunspot": sunspot_events,
            "flares": flare_events,
            "coronal_holes": coronal_hole_events
        }
    }

    # Return as JSON string
    return json.dumps(mock_response, indent=2)

def parse_llm_response(response, sections):
    """
    Parse the LLM response into structured data

    Args:
        response (str): The LLM response
        sections (dict): The original sections data

    Returns:
        dict: Structured data with categorized events
    """
    try:
        # Extract JSON from the response (it might be wrapped in ```json ... ```)
        json_str = response
        if "```json" in response:
            json_str = response.split("```json")[1].split("```")[0].strip()
        elif "```" in response:
            json_str = response.split("```")[1].split("```")[0].strip()

        # Parse the JSON
        data = json.loads(json_str)

        # Add the original URL
        data["url"] = sections.get("url")

        return data

    except Exception as e:
        logger.error(f"Error parsing LLM response: {e}")

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
