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

    # Call the LLM with retry mechanism
    max_retries = 3
    retry_count = 0
    last_error = None

    while retry_count < max_retries:
        try:
            # Log retry attempt
            if retry_count > 0:
                logger.info(f"LLM retry attempt {retry_count + 1}/{max_retries}")

            # Call the LLM
            response = call_llm(prompt)

            # If response is None, retry
            if response is None:
                retry_count += 1
                logger.warning(f"LLM returned None response (attempt {retry_count}/{max_retries})")
                continue

            # Parse the response
            structured_data = parse_llm_response(response, sections)

            # Check if we got valid data with events
            if structured_data and "events" in structured_data:
                events = structured_data["events"]
                total_events = sum(len(events.get(cat, [])) for cat in ["cme", "sunspot", "flares", "coronal_holes"])

                if total_events > 0 or retry_count == max_retries - 1:
                    # We have events or this is our last retry, return the data
                    logger.info(f"LLM analysis successful with {total_events} events")
                    return structured_data
                else:
                    # No events found, but we have more retries
                    logger.warning(f"LLM returned valid JSON but no events (attempt {retry_count + 1}/{max_retries})")
                    retry_count += 1
                    continue
            else:
                # Invalid structure, retry
                logger.warning(f"LLM returned invalid data structure (attempt {retry_count + 1}/{max_retries})")
                retry_count += 1
                continue

        except Exception as e:
            last_error = e
            retry_count += 1
            logger.error(f"Error in LLM analysis (attempt {retry_count}/{max_retries}): {e}")

            # If this is the last retry, break out of the loop
            if retry_count >= max_retries:
                break

            # Wait briefly before retrying
            import time
            time.sleep(1)

    # If we get here, all retries failed
    logger.error(f"All LLM analysis attempts failed after {max_retries} retries")

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
        "error": f"Error analyzing data after {max_retries} attempts: {str(last_error) if last_error else 'Unknown error'}"
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

IMPORTANT GUIDELINES:
1. Only include events that are explicitly mentioned in the provided text.
2. Keep descriptions concise and focused on key information.
3. If no events are found for a category, return an empty array for that category.
4. Ensure your response is valid JSON with no trailing commas or syntax errors.
5. Keep your total response under 2000 tokens to avoid truncation.
6. If you can't find any specific events in the text, please still return a valid JSON structure with the date and empty arrays for each category.
7. DO NOT return null or an empty response.
8. DO NOT include any explanatory text outside the JSON structure.
"""

    return prompt

def call_llm(prompt):
    """
    Call the LLM API using Grok or OpenRouter

    Args:
        prompt (str): The prompt to send to the LLM

    Returns:
        str: The LLM response or None if there's an error
    """
    # Check if the prompt contains meaningful data to analyze
    if "No data available" in prompt or "No full text available" in prompt:
        logger.warning("Skipping LLM call for empty or minimal data")
        return None

    config = get_llm_config()
    provider = config["provider"]
    api_key = config["api_key"]
    base_url = config["base_url"]
    model = config["model"]
    site_url = config["site_url"]
    site_name = config["site_name"]
    reasoning_effort = config["reasoning_effort"]

    # Check if API key is missing or empty
    if not api_key:
        logger.error(f"Missing API key for {provider}. Check your secrets.toml file.")
        return None

    try:
        # Create OpenAI client with appropriate base URL
        client = OpenAI(
            base_url=base_url,
            api_key=api_key,
            timeout=60.0,  # Increase timeout to 60 seconds
        )

        # Common parameters for both providers
        common_params = {
            "model": model,
            "messages": [
                {"role": "system", "content": "You are a helpful space weather expert that analyzes data from spaceweather.com and provides structured information about space weather events. Always respond with valid JSON. Keep your response concise and focused on the events mentioned in the text."},
                {"role": "user", "content": prompt}
            ],
            "temperature": 0.2,
            "max_tokens": 3000,  # Reduced from 4000 to avoid potential truncation issues
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
        reasoning = None

        # For Grok, also log reasoning content if available
        if provider == "grok" and hasattr(completion.choices[0].message, 'reasoning_content'):
            reasoning = completion.choices[0].message.reasoning_content
            logger.debug(f"Grok reasoning: {reasoning[:200]}...")

        # Check if the content is empty or doesn't contain valid JSON
        if not content or not ('{' in content and '}' in content):
            logger.warning(f"LLM returned empty or invalid JSON response: {content}")

            # Try to extract JSON from reasoning content if available
            if reasoning and '{' in reasoning and '}' in reasoning:
                logger.info("Attempting to extract JSON from reasoning content")
                content = reasoning

                # Check if the reasoning content contains valid JSON
                if not ('{' in content and '}' in content):
                    logger.warning("Reasoning content does not contain valid JSON")
                    return None
            else:
                # For Grok, try to extract any JSON-like structure from the content
                if provider == "grok" and content:
                    logger.info("Attempting to extract JSON-like structure from Grok response")
                    import re

                    # Look for anything that resembles a JSON object
                    json_match = re.search(r'(\{[\s\S]*?\})', content, re.DOTALL)
                    if json_match:
                        content = json_match.group(1)
                        logger.info(f"Extracted potential JSON structure: {content[:100]}...")
                        return content

                return None

        # Log a sample of the response for debugging
        logger.debug(f"LLM response sample: {content[:200]}...")

        return content

    except Exception as e:
        logger.error(f"Error calling {provider.capitalize()} LLM API: {e}")
        return None



def sanitize_json_response(response):
    """
    Sanitize and clean up a JSON response from an LLM

    Args:
        response (str): The raw LLM response

    Returns:
        str: Cleaned JSON string
    """
    if not response:
        return response

    # Remove any null bytes or other control characters that might corrupt the JSON
    import re
    response = re.sub(r'[\x00-\x1F\x7F]', '', response)

    # Remove any trailing commas in arrays or objects (common JSON error)
    response = re.sub(r',\s*}', '}', response)
    response = re.sub(r',\s*]', ']', response)

    # Fix missing quotes around keys (another common error)
    response = re.sub(r'([{,])\s*([a-zA-Z0-9_]+)\s*:', r'\1"\2":', response)

    # Ensure boolean values are lowercase (JSON standard)
    response = re.sub(r':\s*True\b', r':true', response)
    response = re.sub(r':\s*False\b', r':false', response)

    # Replace single quotes with double quotes (JSON standard)
    # This is tricky because we need to avoid replacing quotes within quotes
    # A simple approach that works for most cases:
    if "'" in response and '"' not in response:
        response = response.replace("'", '"')

    return response

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
            else:
                # Try a more aggressive approach to find any JSON-like structure
                json_match = re.search(r'(\{[\s\S]*?"events"[\s\S]*?\})', response, re.DOTALL)
                if json_match:
                    json_str = json_match.group(1)

        # Sanitize the JSON string to fix common issues
        json_str = sanitize_json_response(json_str)

        # Log the extracted JSON string for debugging
        logger.debug(f"Extracted JSON for {sections.get('date')}: {json_str[:200]}...")

        # Try to fix truncated or malformed JSON
        try:
            # First attempt: Try to parse as is
            data = json.loads(json_str)
        except json.JSONDecodeError as e:
            logger.warning(f"Initial JSON parsing failed: {e}")

            # Second attempt: Try to fix common JSON issues
            try:
                # Check if it's a truncation issue (missing closing braces)
                if json_str.count('{') > json_str.count('}'):
                    logger.info("Attempting to fix truncated JSON (missing closing braces)")
                    missing_braces = json_str.count('{') - json_str.count('}')
                    json_str = json_str + ('}' * missing_braces)

                # Check for unterminated strings
                import re
                # Find strings that start with " but don't have a matching closing "
                # This is a simplified approach and might not catch all cases
                unterminated_strings = re.findall(r'"[^"]*$', json_str)
                if unterminated_strings:
                    logger.info("Attempting to fix unterminated strings")
                    for s in unterminated_strings:
                        json_str = json_str.replace(s, s + '"')

                # Try parsing again after fixes
                data = json.loads(json_str)
                logger.info("Successfully fixed and parsed JSON")
            except json.JSONDecodeError:
                # Third attempt: Try to extract a partial valid JSON structure
                logger.warning("JSON fixing failed, attempting to extract partial valid structure")
                try:
                    # Extract the date and create a minimal valid structure
                    date_match = re.search(r'"date"\s*:\s*"([^"]+)"', json_str)
                    date = date_match.group(1) if date_match else sections.get("date")

                    # Try to extract event data for each category
                    events = {}
                    for category in ["cme", "sunspot", "flares", "coronal_holes"]:
                        events[category] = []
                        # Look for event entries in this category
                        category_pattern = rf'"{category}"\s*:\s*\[(.*?)\]'
                        category_match = re.search(category_pattern, json_str, re.DOTALL)
                        if category_match:
                            category_content = category_match.group(1).strip()
                            if category_content:
                                # Try to extract individual event objects
                                event_objects = re.finditer(r'\{(.*?)\}', category_content, re.DOTALL)
                                for event_match in event_objects:
                                    event_str = '{' + event_match.group(1) + '}'
                                    try:
                                        event_data = json.loads(event_str)
                                        events[category].append(event_data)
                                    except:
                                        # Skip invalid event objects
                                        continue

                    # Create a valid data structure
                    data = {
                        "date": date,
                        "events": events
                    }
                    logger.info(f"Created partial data structure with {sum(len(events[cat]) for cat in events)} events")
                except Exception as ex:
                    logger.error(f"Failed to extract partial data: {ex}")
                    # Fall back to empty structure
                    raise

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
