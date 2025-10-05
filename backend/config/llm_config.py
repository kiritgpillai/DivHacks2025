# Gemini Model Configuration
GEMINI_MODEL = "gemini-2.0-flash-001"

# Temperature settings for different agent types
TEMPERATURE_EVENT_GENERATOR = 0.7  # Creative for event generation
TEMPERATURE_PORTFOLIO = 0.3  # Low for precise calculations
TEMPERATURE_NEWS = 0.2  # Very low for accurate stance detection
TEMPERATURE_PRICE = 0.1  # Minimal for data analysis
TEMPERATURE_VILLAIN = 0.9  # High for creative trash talk
TEMPERATURE_INSIGHT = 0.4  # Moderate for balanced coaching
TEMPERATURE_SUPERVISOR = 0.0  # Deterministic for routing
