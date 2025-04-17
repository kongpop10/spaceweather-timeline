"""
Functions to process text with LLM (Grok or OpenRouter)
"""
import json
import requests
import streamlit as st
import logging
from openai import OpenAI

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def get_llm_config():
    """Get the LLM configuration from Streamlit secrets or session state"""
    try:
        # Get LLM provider from session state if available, otherwise from secrets
        if "llm_provider" in st.session_state and st.session_state.llm_provider:
            provider = st.session_state.llm_provider
        else:
            provider = st.secrets.get("LLM_PROVIDER", "grok")

        # Get base URL and model from session state if available, otherwise from secrets
        if "llm_base_url" in st.session_state and st.session_state.llm_base_url:
            base_url = st.session_state.llm_base_url
        else:
            base_url = st.secrets.get("LLM_BASE_URL", "https://api.x.ai/v1")

        if "llm_model" in st.session_state and st.session_state.llm_model:
            model = st.session_state.llm_model
        else:
            model = st.secrets.get("LLM_MODEL", "grok-3-mini-beta")

        # Get reasoning effort for Grok model
        if "llm_reasoning_effort" in st.session_state and st.session_state.llm_reasoning_effort:
            reasoning_effort = st.session_state.llm_reasoning_effort
        else:
            reasoning_effort = st.secrets.get("LLM_REASONING_EFFORT", "low")

        # Get API key based on provider
        if provider == "grok":
            api_key = st.secrets.get("XAI_API_KEY", "")
        else:  # openrouter
            api_key = st.secrets.get("OPENROUTER_API_KEY", st.secrets.get("GROQ_API_KEY", ""))

        # Get site info for OpenRouter from session state if available, otherwise from secrets
        if "site_url" in st.session_state and st.session_state.site_url:
            site_url = st.session_state.site_url
        else:
            site_url = st.secrets.get("SITE_URL", "https://spaceweather-timeline.streamlit.app")

        if "site_name" in st.session_state and st.session_state.site_name:
            site_name = st.session_state.site_name
        else:
            site_name = st.secrets.get("SITE_NAME", "Space Weather Timeline")

        return {
            "provider": provider,
            "api_key": api_key,
            "base_url": base_url,
            "model": model,
            "reasoning_effort": reasoning_effort,
            "site_url": site_url,
            "site_name": site_name
        }
    except Exception as e:
        logger.warning(f"Error getting LLM configuration: {e}")
        return {
            "provider": "grok",
            "api_key": "",
            "base_url": "https://api.x.ai/v1",
            "model": "grok-3-mini-beta",
            "reasoning_effort": "low",
            "site_url": "https://spaceweather-timeline.streamlit.app",
            "site_name": "Space Weather Timeline"
        }

def analyze_spaceweather_data(sections):
    """
    Analyze spaceweather data using Grok or OpenRouter LLM

    Args:
        sections (dict): Extracted sections from spaceweather.com

    Returns:
        dict: Structured data with categorized events
    """
    if not sections:
        logger.warning("No sections data provided for LLM analysis")
        return {
            "date": "unknown",
            "url": "unknown",
            "events": {
                "cme": [],
                "sunspot": [],
                "flares": [],
                "coronal_holes": []
            },
            "error": "No sections data provided"
        }

    # Prepare the prompt
    prompt = create_analysis_prompt(sections)

    # Call the LLM
    try:
        response = call_llm(prompt)

        # Parse the response
        structured_data = parse_llm_response(response, sections)

        return structured_data

    except Exception as e:
        logger.error(f"Error analyzing spaceweather data: {e}")
        # Return a basic structure instead of None
        return {
            "date": sections.get("date", "unknown"),
            "url": sections.get("url", "unknown"),
            "events": {
                "cme": [],
                "sunspot": [],
                "flares": [],
                "coronal_holes": []
            },
            "error": f"Error analyzing data: {str(e)}"
        }

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

def call_llm(prompt):
    """
    Call the LLM API using Grok or OpenRouter

    Args:
        prompt (str): The prompt to send to the LLM

    Returns:
        str: The LLM response
    """
    config = get_llm_config()
    provider = config["provider"]
    api_key = config["api_key"]
    base_url = config["base_url"]
    model = config["model"]
    site_url = config["site_url"]
    site_name = config["site_name"]
    reasoning_effort = config["reasoning_effort"]

    try:
        # Create OpenAI client with appropriate base URL
        client = OpenAI(
            base_url=base_url,
            api_key=api_key,
        )

        # Common parameters for both providers
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

        # Provider-specific parameters
        if provider == "grok":
            # Add Grok-specific parameters
            common_params["reasoning_effort"] = reasoning_effort
            logger.info(f"Using Grok model: {model} with reasoning_effort: {reasoning_effort}")
        else:  # openrouter
            # Add OpenRouter-specific parameters
            common_params["extra_headers"] = {
                "HTTP-Referer": site_url,  # Site URL for rankings on openrouter.ai
                "X-Title": site_name,  # Site title for rankings on openrouter.ai
            }
            logger.info(f"Using OpenRouter model: {model}")

        # Call the API
        completion = client.chat.completions.create(**common_params)

        # Extract the response content
        content = completion.choices[0].message.content

        # For Grok, also log reasoning content if available
        if provider == "grok" and hasattr(completion.choices[0].message, 'reasoning_content'):
            reasoning = completion.choices[0].message.reasoning_content
            logger.debug(f"Grok reasoning: {reasoning[:200]}...")

        # Log a sample of the response for debugging
        logger.debug(f"LLM response sample: {content[:200]}...")

        return content

    except Exception as e:
        logger.error(f"Error calling {provider.capitalize()} LLM API: {e}")
        return None



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
