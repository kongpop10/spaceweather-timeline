"""
Supabase synchronization for the spaceweather app
"""
import os
import json
import logging
import requests
import streamlit as st
from datetime import datetime

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def get_supabase_client():
    """
    Get a Supabase client instance

    Returns:
        SupabaseClient: Supabase client instance or None if not configured
    """
    try:
        # Check if we have Supabase credentials in Streamlit secrets
        if 'SUPABASE_URL' in st.secrets and 'SUPABASE_API_KEY' in st.secrets:
            url = st.secrets['SUPABASE_URL']
            api_key = st.secrets['SUPABASE_API_KEY']
            return SupabaseClient(url, api_key)
        else:
            logger.warning("Supabase credentials not found in secrets")
            return None
    except Exception as e:
        logger.error(f"Error creating Supabase client: {e}")
        return None

class SupabaseClient:
    """Client for interacting with Supabase"""

    def __init__(self, url, api_key):
        """
        Initialize the Supabase client

        Args:
            url (str): Supabase project URL
            api_key (str): Supabase project API key
        """
        self.url = url
        self.api_key = api_key
        self.headers = {
            "apikey": api_key,
            "Content-Type": "application/json",
            "Prefer": "return=representation"
        }

    def _make_request(self, method, endpoint, data=None, params=None):
        """
        Make a request to the Supabase API

        Args:
            method (str): HTTP method (GET, POST, PUT, DELETE)
            endpoint (str): API endpoint
            data (dict, optional): Data to send in the request body
            params (dict, optional): Query parameters

        Returns:
            dict: Response data
        """
        url = f"{self.url}{endpoint}"

        # Add timeout and retry logic
        max_retries = 3
        retry_count = 0
        timeout = 10  # 10 seconds timeout

        while retry_count < max_retries:
            try:
                logger.info(f"Making {method} request to Supabase: {endpoint} (attempt {retry_count + 1}/{max_retries})")

                if method == "GET":
                    response = requests.get(url, headers=self.headers, params=params, timeout=timeout)
                elif method == "POST":
                    response = requests.post(url, headers=self.headers, json=data, timeout=timeout)
                elif method == "PUT":
                    response = requests.put(url, headers=self.headers, json=data, timeout=timeout)
                elif method == "DELETE":
                    response = requests.delete(url, headers=self.headers, params=params, timeout=timeout)
                else:
                    logger.error(f"Unsupported HTTP method: {method}")
                    return None

                # Check for 4xx or 5xx status codes
                if response.status_code >= 400:
                    logger.warning(f"Supabase API error: {response.status_code} - {response.text}")
                    if response.status_code == 400 and "id" in str(params):
                        # Special handling for 400 errors with id parameter
                        logger.info(f"Attempting to recover from 400 error with id parameter")
                        # Try to continue despite the error
                        return {}

                response.raise_for_status()
                return response.json()

            except requests.exceptions.Timeout:
                retry_count += 1
                if retry_count >= max_retries:
                    logger.error(f"Timeout error after {max_retries} attempts: {url}")
                    return None
                logger.warning(f"Timeout error, retrying ({retry_count}/{max_retries}): {url}")
            except requests.exceptions.RequestException as e:
                retry_count += 1
                if retry_count >= max_retries:
                    logger.error(f"Request error after {max_retries} attempts: {e}")
                    return None
                logger.warning(f"Request error, retrying ({retry_count}/{max_retries}): {e}")

    def init_tables(self):
        """
        Initialize the tables in Supabase

        This function is meant to be run once to set up the tables in Supabase.
        It's not needed for normal operation since the tables should already exist.
        """
        # This is a placeholder. In a real implementation, you would use Supabase migrations
        # or the Supabase dashboard to create the tables.
        logger.info("Supabase tables should be created manually in the Supabase dashboard")
        logger.info("Required tables: dates, events, settings")
        logger.info("See the README for more information")

    def sync_date(self, data):
        """
        Sync a date record to Supabase

        Args:
            data (dict): Date data to sync

        Returns:
            bool: True if successful, False otherwise
        """
        try:
            # Extract the date information
            date_str = data.get("date")
            url = data.get("url")
            error = data.get("error")

            # Check if the date already exists in Supabase
            existing = self._make_request(
                "GET",
                "/rest/v1/dates",
                params={"date": f"eq.{date_str}", "select": "id"})

            if existing and len(existing) > 0:
                # Update existing record
                supabase_id = existing[0]["id"]
                date_data = {
                    "url": url,
                    "error": error,
                    "last_updated": datetime.now().isoformat()
                }

                self._make_request(
                    "PUT",
                    f"/rest/v1/dates?id=eq.{supabase_id}",
                    data=date_data
                )

                # Delete existing events for this date
                self._make_request(
                    "DELETE",
                    f"/rest/v1/events",
                    params={"date_id": f"eq.{supabase_id}"}
                )
            else:
                # Insert new record
                date_data = {
                    "date": date_str,
                    "url": url,
                    "error": error,
                    "last_updated": datetime.now().isoformat()
                }

                result = self._make_request(
                    "POST",
                    "/rest/v1/dates",
                    data=date_data
                )

                if not result or len(result) == 0:
                    logger.error(f"Failed to insert date record for {date_str}")
                    return False

                supabase_id = result[0]["id"]

            # Insert events
            events = data.get("events", {})
            for category in ["cme", "sunspot", "flares", "coronal_holes"]:
                category_events = events.get(category, [])
                for event in category_events:
                    tone = event.get("tone")
                    event_date = event.get("date")
                    predicted_arrival = event.get("predicted_arrival")
                    detail = event.get("detail")
                    image_url = event.get("image_url")
                    is_significant = True if tone and tone.lower() == "significant" else False

                    event_data = {
                        "date_id": supabase_id,
                        "category": category,
                        "tone": tone,
                        "event_date": event_date,
                        "predicted_arrival": predicted_arrival,
                        "detail": detail,
                        "image_url": image_url,
                        "is_significant": is_significant
                    }

                    self._make_request(
                        "POST",
                        "/rest/v1/events",
                        data=event_data
                    )

            logger.info(f"Data for {date_str} synced to Supabase")
            return True

        except Exception as e:
            logger.error(f"Error syncing date to Supabase: {e}")
            return False

    def get_date(self, date_str):
        """
        Get a date record from Supabase

        Args:
            date_str (str): Date in format YYYY-MM-DD

        Returns:
            dict: Date data
        """
        try:
            # Get the date record
            date_result = self._make_request(
                "GET",
                "/rest/v1/dates",
                params={"date": f"eq.{date_str}", "select": "*"}
            )

            if not date_result or len(date_result) == 0:
                logger.info(f"No data found in Supabase for {date_str}")
                return None

            date_record = date_result[0]
            supabase_id = date_record["id"]

            # Get all events for this date
            events_result = self._make_request(
                "GET",
                "/rest/v1/events",
                params={
                    "date_id": f"eq.{supabase_id}",
                    "select": "*",
                    "order": "category.asc,is_significant.desc"
                }
            )

            # Convert to the expected format
            result = {
                "date": date_record["date"],
                "url": date_record["url"],
                "events": {
                    "cme": [],
                    "sunspot": [],
                    "flares": [],
                    "coronal_holes": []
                }
            }

            if date_record.get("error"):
                result["error"] = date_record["error"]

            # Group events by category
            for event in events_result:
                category = event["category"]
                event_data = {
                    "tone": event["tone"],
                    "date": event["event_date"],
                    "predicted_arrival": event["predicted_arrival"],
                    "detail": event["detail"],
                    "image_url": event["image_url"]
                }
                result["events"][category].append(event_data)

            logger.info(f"Data for {date_str} retrieved from Supabase")
            return result

        except Exception as e:
            logger.error(f"Error getting date from Supabase: {e}")
            return None

    def get_all_dates(self):
        """
        Get all date records from Supabase

        Returns:
            list: List of all date records
        """
        try:
            # Get all date records
            date_result = self._make_request(
                "GET",
                "/rest/v1/dates",
                params={"select": "*", "order": "date.desc"}
            )

            if not date_result:
                logger.info("No data found in Supabase")
                return []

            all_data = []

            for date_record in date_result:
                supabase_id = date_record["id"]

                # Get all events for this date
                events_result = self._make_request(
                    "GET",
                    "/rest/v1/events",
                    params={
                        "date_id": f"eq.{supabase_id}",
                        "select": "*",
                        "order": "category.asc,is_significant.desc"
                    }
                )

                # Convert to the expected format
                result = {
                    "date": date_record["date"],
                    "url": date_record["url"],
                    "events": {
                        "cme": [],
                        "sunspot": [],
                        "flares": [],
                        "coronal_holes": []
                    }
                }

                if date_record.get("error"):
                    result["error"] = date_record["error"]

                # Group events by category
                for event in events_result:
                    category = event["category"]
                    event_data = {
                        "tone": event["tone"],
                        "date": event["event_date"],
                        "predicted_arrival": event["predicted_arrival"],
                        "detail": event["detail"],
                        "image_url": event["image_url"]
                    }
                    result["events"][category].append(event_data)

                all_data.append(result)

            logger.info(f"Retrieved {len(all_data)} records from Supabase")
            return all_data

        except Exception as e:
            logger.error(f"Error getting all dates from Supabase: {e}")
            return []

    def sync_setting(self, key, value, description=None):
        """
        Sync a setting to Supabase

        Args:
            key (str): Setting key
            value (str): Setting value
            description (str, optional): Setting description

        Returns:
            bool: True if successful, False otherwise
        """
        try:
            # Check if the setting already exists in Supabase
            existing = self._make_request(
                "GET",
                "/rest/v1/settings",
                params={"key": f"eq.{key}", "select": "*"})

            if existing and len(existing) > 0:
                # Update existing record
                setting_data = {
                    "value": value,
                    "last_updated": datetime.now().isoformat()
                }

                if description:
                    setting_data["description"] = description

                self._make_request(
                    "PUT",
                    f"/rest/v1/settings?key=eq.{key}",
                    data=setting_data
                )
            else:
                # Insert new record
                setting_data = {
                    "key": key,
                    "value": value,
                    "description": description if description else "",
                    "last_updated": datetime.now().isoformat()
                }

                self._make_request(
                    "POST",
                    "/rest/v1/settings",
                    data=setting_data
                )

            logger.info(f"Setting {key} synced to Supabase with value {value}")
            return True

        except Exception as e:
            logger.error(f"Error syncing setting to Supabase: {e}")
            return False

    def get_setting(self, key, default=None):
        """
        Get a setting from Supabase

        Args:
            key (str): Setting key
            default: Default value to return if the setting doesn't exist

        Returns:
            str: Setting value or default if not found
        """
        try:
            # Get the setting record
            setting_result = self._make_request(
                "GET",
                "/rest/v1/settings",
                params={"key": f"eq.{key}", "select": "*"}
            )

            if not setting_result or len(setting_result) == 0:
                logger.info(f"No setting found in Supabase for {key}")
                return default

            setting_record = setting_result[0]
            return setting_record["value"]

        except Exception as e:
            logger.error(f"Error getting setting from Supabase: {e}")
            return default

    def get_all_settings(self):
        """
        Get all settings from Supabase

        Returns:
            dict: Dictionary of all settings
        """
        try:
            # Get all setting records
            setting_result = self._make_request(
                "GET",
                "/rest/v1/settings",
                params={"select": "*"}
            )

            if not setting_result:
                logger.info("No settings found in Supabase")
                return {}

            settings = {}
            for setting in setting_result:
                settings[setting["key"]] = {
                    "value": setting["value"],
                    "description": setting["description"]
                }

            logger.info(f"Retrieved {len(settings)} settings from Supabase")
            return settings

        except Exception as e:
            logger.error(f"Error getting all settings from Supabase: {e}")
            return {}
