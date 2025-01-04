from typing import Any
import httpx
from mcp.server.fastmcp import FastMCP
import asyncio

# Initialize FastMCP server
mcp = FastMCP("weather")

# Constants
NWS_API_BASE = "https://api.weather.gov"
USER_AGENT = "weather-app/1.0"

async def make_nws_request(url: str) -> dict[str, Any] | None:
    """Make a request to the NWS API with proper error handling."""
    headers = {
        "User-Agent": USER_AGENT,
        "Accept": "application/geo+json"
    }
    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(url, headers=headers, timeout=30.0)
            response.raise_for_status()
            return response.json()
        except Exception:
            return None

def format_alert(feature: dict) -> str:
    """Format an alert feature into a readable string."""
    props = feature["properties"]
    return f"""
Event: {props.get('event', 'Unknown')}
Area: {props.get('areaDesc', 'Unknown')}
Severity: {props.get('severity', 'Unknown')}
Description: {props.get('description', 'No description available')}
Instructions: {props.get('instruction', 'No specific instructions provided')}
"""

@mcp.tool()
async def get_alerts(state: str) -> str:
    """Get weather alerts for a US state.

    Args:
        state: Two-letter US state code (e.g. CA, NY)
    """
    url = f"{NWS_API_BASE}/alerts/active/area/{state}"
    data = await make_nws_request(url)

    if not data or "features" not in data:
        return "Unable to fetch alerts or no alerts found."
    
    if not data["features"]:
        return "No active alerts for this state."
    
    alerts = [format_alert(feature) for feature in data["features"]]
    return "\n--\n".join(alerts)

@mcp.tool()
async def get_forecast(latitute: float, longtitude: float) -> str:
    """Get weather forecast a location.

    Args:
        latitude: Latitude of the location
        longtitude: Longitude of the location
    """
    points_url = f"{NWS_API_BASE}/points/{latitute},{longtitude}"
    points_data = await make_nws_request(points_url)

    if not points_data:
        return "Unable to fetch points data for this location"
    
    # Get the forecast URL from the points response
    forecast_url = points_data.get("properties", {}).get("forecast")
    if not forecast_url:
        return "No forecast data available for this location"

    forecast_data = await make_nws_request(forecast_url)
    if not forecast_data:
        return "Unable to get forecast data for this location"
    
    # Format the periods into a readable forecast
    periods = forecast_data.get("properties", {}).get("periods", [])
    forecasts = []
    for period in periods[:5]:
        forecast = f"""
{period['name']}:
Tempature: {period['temperature']}°{period['temperatureUnit']}
Wind: {period['windSpeed']} {period['windDirection']}
Forecast: {period['detailedForecast']}
"""
        forecasts.append(forecast)
    
    return "\n--\n".join(forecasts)

# async def main():
#     # Run the server using stdin/stdout streams
#     async with mcp.server.stdio.stdio_server() as (read_stream, write_stream):
#         await server.run(
#             read_stream,
#             write_stream,
#             InitializationOptions(
#                 server_name="weather",
#                 server_version="0.1.0",
#                 capabilities=server.get_capabilities(
#                     notification_options=NotificationOptions(),
#                     experimental_capabilities={},
#                 ),
#             ),
#         )

if __name__ == "__main__":
    asyncio.run(mcp.run())