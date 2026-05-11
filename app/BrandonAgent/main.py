import httpx
from strands import Agent, tool
from bedrock_agentcore.runtime import BedrockAgentCoreApp
from model.load import load_model

app = BedrockAgentCoreApp()
log = app.logger

EUGENE_LAT = 44.0521
EUGENE_LON = -123.0868

WEATHER_CODE = {
    0: "clear sky",
    1: "mainly clear", 2: "partly cloudy", 3: "overcast",
    45: "fog", 48: "depositing rime fog",
    51: "light drizzle", 53: "moderate drizzle", 55: "dense drizzle",
    56: "light freezing drizzle", 57: "dense freezing drizzle",
    61: "slight rain", 63: "moderate rain", 65: "heavy rain",
    66: "light freezing rain", 67: "heavy freezing rain",
    71: "slight snow", 73: "moderate snow", 75: "heavy snow",
    77: "snow grains",
    80: "slight rain showers", 81: "moderate rain showers", 82: "violent rain showers",
    85: "slight snow showers", 86: "heavy snow showers",
    95: "thunderstorm", 96: "thunderstorm with slight hail", 99: "thunderstorm with heavy hail",
}


@tool
def get_eugene_weather() -> dict:
    """Fetch current weather for Eugene, Oregon from Open-Meteo.

    Returns a dict with temperature_f, wind_mph, precipitation_mm,
    condition (human-readable), and is_day flag.
    """
    url = (
        "https://api.open-meteo.com/v1/forecast"
        f"?latitude={EUGENE_LAT}&longitude={EUGENE_LON}"
        "&current=temperature_2m,precipitation,weather_code,wind_speed_10m,is_day"
        "&temperature_unit=fahrenheit&wind_speed_unit=mph&precipitation_unit=inch"
    )
    with httpx.Client(timeout=10.0) as client:
        resp = client.get(url)
        resp.raise_for_status()
        current = resp.json()["current"]

    code = current["weather_code"]
    return {
        "location": "Eugene, OR",
        "temperature_f": current["temperature_2m"],
        "wind_mph": current["wind_speed_10m"],
        "precipitation_in": current["precipitation"],
        "condition": WEATHER_CODE.get(code, f"code {code}"),
        "is_day": bool(current["is_day"]),
    }


tools = [get_eugene_weather]

SYSTEM_PROMPT = """You are a Eugene, Oregon activity concierge.

When the user asks about weather or what to do, call the get_eugene_weather tool
first, then recommend ONE specific activity. Pick outdoors if it's dry and above
~50F with low wind; pick indoors if it's raining, cold, or after dark.

Outdoor ideas: Pre's Trail at Alton Baker Park, Spencer Butte hike, Ruth Bascom
riverfront path, Hendricks Park rhododendron garden, Saturday Market (Sat only).
Indoor ideas: Jordan Schnitzer Museum of Art, Science Factory, Fifth Street
Public Market, a pint at Ninkasi tasting room, Eugene Public Library.

Be concise: 2-3 sentences. Lead with the current conditions, then the pick and why.
"""

_agent = None


def get_or_create_agent():
    global _agent
    if _agent is None:
        _agent = Agent(
            model=load_model(),
            system_prompt=SYSTEM_PROMPT,
            tools=tools,
        )
    return _agent


@app.entrypoint
async def invoke(payload, context):
    log.info("Invoking Agent.....")

    agent = get_or_create_agent()
    stream = agent.stream_async(payload.get("prompt"))

    async for event in stream:
        if "data" in event and isinstance(event["data"], str):
            yield event["data"]


if __name__ == "__main__":
    app.run()
