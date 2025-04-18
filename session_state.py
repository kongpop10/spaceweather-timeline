"""
Session state management for the Space Weather Timeline app
"""
import streamlit as st
from datetime import datetime

def initialize_session_state():
    """
    Initialize all session state variables
    """
    # Admin authentication
    if "admin_authenticated" not in st.session_state:
        st.session_state.admin_authenticated = False

    # LLM configuration
    if "llm_provider" not in st.session_state:
        st.session_state.llm_provider = st.secrets.get("LLM_PROVIDER", "grok")

    if "llm_base_url" not in st.session_state:
        st.session_state.llm_base_url = st.secrets.get("LLM_BASE_URL", "https://api.x.ai/v1")

    if "llm_model" not in st.session_state:
        st.session_state.llm_model = st.secrets.get("LLM_MODEL", "grok-3-mini-beta")

    if "llm_reasoning_effort" not in st.session_state:
        st.session_state.llm_reasoning_effort = st.secrets.get("LLM_REASONING_EFFORT", "low")

    # OpenRouter site information
    if "site_url" not in st.session_state:
        st.session_state.site_url = st.secrets.get("SITE_URL", "https://spaceweather-timeline.streamlit.app")

    if "site_name" not in st.session_state:
        st.session_state.site_name = st.secrets.get("SITE_NAME", "Space Weather Timeline")

    # Selected date (default to today's date)
    if "selected_date" not in st.session_state:
        st.session_state.selected_date = datetime.now().strftime("%Y-%m-%d")

    # Admin date picker and days to show
    if "admin_selected_date" not in st.session_state:
        st.session_state.admin_selected_date = None

    if "admin_days_to_show" not in st.session_state:
        st.session_state.admin_days_to_show = None

    # Category filter variables
    if "show_cme" not in st.session_state:
        st.session_state.show_cme = True
    if "show_sunspot" not in st.session_state:
        st.session_state.show_sunspot = True
    if "show_flares" not in st.session_state:
        st.session_state.show_flares = True
    if "show_coronal_holes" not in st.session_state:
        st.session_state.show_coronal_holes = True

    # Significant events filter (hidden feature)
    if "show_significant_only" not in st.session_state:
        st.session_state.show_significant_only = False

    # Confirmation dialogs
    if "show_refresh_confirmation" not in st.session_state:
        st.session_state.show_refresh_confirmation = False
    if "show_cache_clear_confirmation" not in st.session_state:
        st.session_state.show_cache_clear_confirmation = False
    if "show_refresh_empty_confirmation" not in st.session_state:
        st.session_state.show_refresh_empty_confirmation = False

    # Data refresh flag
    if "check_empty_data" not in st.session_state:
        st.session_state.check_empty_data = True

def get_current_llm_info():
    """
    Get current LLM provider and model information
    """
    if "llm_provider" in st.session_state and "llm_model" in st.session_state:
        provider = st.session_state.llm_provider
        model_name = st.session_state.llm_model
    else:
        provider = st.secrets.get("LLM_PROVIDER", "grok")
        model_name = st.secrets.get("LLM_MODEL", "grok-3-mini-beta")

    return provider, model_name
