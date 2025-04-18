"""
CSS styles for the Space Weather Timeline app
"""

def get_app_styles():
    """
    Returns the CSS styles for the app
    """
    return """<style>
    /* Dark mode compatible event cards */
    .event-card {
        border: 1px solid rgba(221, 221, 221, 0.3);
        border-radius: 5px;
        padding: 10px;
        margin-bottom: 10px;
        background-color: rgba(255, 255, 255, 0.05);
        color: inherit;
        transition: transform 0.2s, box-shadow 0.2s;
        position: relative;
    }
    .event-card:hover {
        transform: translateY(-2px);
    }
    .event-card.significant {
        border-left: 8px solid #ff4b4b;
        background: linear-gradient(90deg, rgba(255, 75, 75, 0.15) 0%, rgba(255, 255, 255, 0.05) 100%);
        box-shadow: 0 4px 8px rgba(255, 75, 75, 0.2);
    }
    .event-card.significant:hover {
        box-shadow: 0 6px 12px rgba(255, 75, 75, 0.3);
    }
    .event-card.significant::before {
        content: "SIGNIFICANT EVENT";
        position: absolute;
        top: -10px;
        right: 10px;
        background-color: #ff4b4b;
        color: white;
        font-size: 10px;
        font-weight: bold;
        padding: 2px 8px;
        border-radius: 10px;
        box-shadow: 0 2px 4px rgba(0, 0, 0, 0.2);
    }
    .event-card h4 {
        margin-top: 0;
        color: inherit;
        font-size: 1.2em;
    }
    .event-card.significant h4 {
        color: #ff4b4b;
        font-weight: bold;
    }
    .event-card p {
        color: inherit;
        margin: 0.5em 0;
    }
    .event-card strong {
        color: inherit;
        font-weight: bold;
    }
    .event-card.significant strong {
        font-weight: bold;
    }
    /* Styling for event card details section */
    .event-card-details {
        margin: 0.5em 0;
        color: inherit;
    }
    .event-card-details p {
        color: inherit;
        margin: 0.5em 0;
    }
    .event-card-image {
        margin-top: 1em;
    }
    /* Ensure proper styling for HTML elements in event details */
    .event-card p strong, .event-card-details p strong {
        font-weight: bold;
    }
    .event-card em, .event-card-details em {
        font-style: italic;
    }
    .event-card ul, .event-card ol, .event-card-details ul, .event-card-details ol {
        margin-left: 1.5em;
        margin-top: 0.5em;
        margin-bottom: 0.5em;
    }
    .event-card li, .event-card-details li {
        margin-bottom: 0.25em;
    }
    .event-card img, .event-card-image img {
        max-width: 100%;
        max-height: 400px;
        height: auto;
        border-radius: 4px;
        margin-top: 10px;
        object-fit: contain;
    }
    /* Date selector styling */
    .timeline-day {
        cursor: pointer;
        transition: transform 0.2s;
    }
    .timeline-day:hover {
        transform: scale(1.05);
    }
    .significant-day {
        font-weight: bold;
        color: #ff4b4b;
    }
    /* Significant date button styling */
    .significant-date-btn {
        background-color: rgba(255, 75, 75, 0.2) !important;
        border: 2px solid #ff4b4b !important;
        color: #ff4b4b !important;
        font-weight: bold !important;
        box-shadow: 0 2px 4px rgba(255, 75, 75, 0.3) !important;
    }
    /* Selected date button styling */
    .selected-date-btn {
        background-color: rgba(75, 181, 255, 0.2) !important;
        border: 2px solid #4bb5ff !important;
        color: #4bb5ff !important;
        font-weight: bold !important;
        box-shadow: 0 2px 4px rgba(75, 181, 255, 0.3) !important;
    }
    /* Pulsing animation for significant events */
    @keyframes pulse {
        0% { transform: scale(1); opacity: 1; }
        50% { transform: scale(1.1); opacity: 0.8; }
        100% { transform: scale(1); opacity: 1; }
    }
    .pulse {
        animation: pulse 2s infinite;
    }

    /* Mobile responsive styles */
    @media (max-width: 768px) {
        /* Make date selector more compact on mobile */
        .mobile-date-selector {
            display: flex;
            flex-direction: column;
            gap: 8px;
            margin-bottom: 10px;
        }

        /* Hide date buttons on mobile and show dropdown instead */
        .desktop-date-buttons,
        div.desktop-date-buttons,
        div[data-testid="stHorizontalBlock"] {
            display: none !important;
            height: 0 !important;
            min-height: 0 !important;
            visibility: hidden !important;
            margin: 0 !important;
            padding: 0 !important;
            overflow: hidden !important;
        }

        .mobile-date-selector {
            display: block;
        }

        /* Make date group selector more compact */
        div.desktop-date-buttons .stSlider {
            min-height: 40px;
            padding-top: 0;
            padding-bottom: 0;
        }

        /* Make selectbox more compact */
        .mobile-date-selector .stSelectbox,
        div[data-testid="stSelectbox"] {
            margin-bottom: 0;
            padding-bottom: 0;
        }

        /* Make the select boxes more compact */
        div[data-testid="stVerticalBlock"] div[data-testid="stSelectbox"] {
            margin-bottom: 0.25rem !important;
        }

        /* Add space above date selector on mobile */
        .mobile-date-selector.date-selector {
            margin-top: 0.5rem !important;
        }

        /* Reduce spacing around date selector section */
        [data-testid="stMarkdownContainer"] h3,
        .date-selector-heading h3 {
            margin-bottom: 0.5rem;
            margin-top: 0.5rem;
            font-size: 1.1rem;
        }

        /* Compact date selector heading */
        .date-selector-heading {
            margin-bottom: 0.25rem;
            padding-bottom: 0;
        }

        /* Hide redundant elements in mobile view */
        .mobile-date-selector + div[data-testid="stHorizontalBlock"],
        div[data-testid="stMarkdownContainer"] + div[data-testid="stHorizontalBlock"] {
            display: none !important;
            height: 0 !important;
            visibility: hidden !important;
            margin: 0 !important;
            padding: 0 !important;
        }

        /* Make the date selection section more compact */
        .mobile-date-selector.date-group-selector + div {
            margin-top: 0 !important;
            padding-top: 0 !important;
        }

        /* Remove extra spacing in mobile view */
        div[data-testid="stVerticalBlock"] > div {
            padding-top: 0 !important;
            padding-bottom: 0 !important;
            margin-top: 0 !important;
            margin-bottom: 0.5rem !important;
        }
    }

    /* Desktop styles */
    @media (min-width: 769px) {
        .mobile-date-selector,
        .date-selector-dropdown {
            display: none !important;
            height: 0 !important;
            visibility: hidden !important;
            margin: 0 !important;
            padding: 0 !important;
            overflow: hidden !important;
        }

        .desktop-date-buttons {
            display: flex;
        }
    }

    /* Mobile date selector styles */
    .mobile-date-selector .stSelectbox > div > div {
        padding-top: 0 !important;
        padding-bottom: 0 !important;
    }
    .mobile-date-selector label {
        font-size: 0.9rem !important;
        margin-bottom: 0 !important;
        padding-bottom: 0 !important;
    }
    /* Ensure no extra space between selectors */
    .date-selector {
        margin-top: 0 !important;
        padding-top: 0 !important;
    }

    /* Desktop date buttons styles */
    @media (max-width: 768px) {
        #desktop-date-section, #desktop-date-section + div {
            display: none !important;
            height: 0 !important;
            visibility: hidden !important;
            margin: 0 !important;
            padding: 0 !important;
        }
    }
    @media (min-width: 769px) {
        /* Improve spacing for desktop date buttons */
        #desktop-date-section {
            margin-top: 0.5rem;
        }
        /* Make date buttons more compact when we have many */
        #desktop-date-section button {
            padding: 0.25rem 0.5rem;
            min-height: 0;
        }
    }
    </style>
    """

def get_mobile_detection_js():
    """
    Returns JavaScript for mobile detection
    """
    return """
    <script>
        // Function to check if the device is mobile
        function isMobile() {
            return window.innerWidth <= 768;
        }

        // Function to hide desktop date buttons on mobile
        function hideDesktopButtonsOnMobile() {
            if (isMobile()) {
                // Find all horizontal blocks that contain date buttons
                const horizontalBlocks = document.querySelectorAll('[data-testid="stHorizontalBlock"]');
                horizontalBlocks.forEach(block => {
                    // Check if this block is part of the date selection
                    const buttons = block.querySelectorAll('button');
                    if (buttons.length > 0 && buttons[0].innerText.length <= 3) {
                        // This is likely a date button block, hide it
                        block.style.display = "none";
                        block.style.height = "0";
                        block.style.visibility = "hidden";
                        block.style.margin = "0";
                        block.style.padding = "0";
                        block.style.overflow = "hidden";
                    }
                });
            }
        }

        // Run on page load
        document.addEventListener("DOMContentLoaded", hideDesktopButtonsOnMobile);

        // Run on window resize
        window.addEventListener("resize", hideDesktopButtonsOnMobile);
    </script>
    """
