"""
Tool functions for the agent system.
"""

from typing import Dict, Optional
from datetime import datetime, timedelta
import pytz
import json
import requests
import yfinance as yf

from agents import function_tool, FunctionTool
from geopy.geocoders import Nominatim
from pydantic import BaseModel, Field

from src.config import get_config
from src.logging_config import get_logger

logger = get_logger(__name__)


class ToolMetadata(BaseModel):
    """Metadata for a tool that provides human-readable information"""

    name: Optional[str] = Field(None, description="The name of the tool")
    description: str = Field(
        ..., description="Human-readable description of what the tool does"
    )
    image_url: Optional[str] = Field(
        None, description="URL to an image representing the tool for front-end display"
    )
    # Future fields can be added here easily, e.g.:
    # category: Optional[str] = Field(None, description="Category of the tool")
    # difficulty: Optional[str] = Field(None, description="Difficulty level")
    # examples: Optional[List[str]] = Field(None, description="Usage examples")


def tool_metadata(metadata: ToolMetadata):
    """
    Decorator to add metadata to a FunctionTool.

    Args:
        metadata: ToolMetadata object containing tool information
    """

    def decorator(func: FunctionTool) -> FunctionTool:
        func.tool_metadata = metadata
        return func

    return decorator


@tool_metadata(
    ToolMetadata(
        description="Get current weather conditions for any location using latitude and longitude coordinates"
    )
)
@function_tool
async def get_weather(lat: float, long: float) -> str:
    """Get the weather for a given city.
    :param lat: The latitude of the city.
    :param long: The longitude of the city.
    """
    logger.info(f"Weather tool called for coordinates: {lat}, {long}")
    return f"The weather in {lat} {long} is sunny"


@tool_metadata(
    ToolMetadata(
        description="Perform mathematical calculations and evaluate expressions"
    )
)
@function_tool
async def calculator(expression: str) -> str:
    """Can do calculations!"""
    logger.debug(f"Calculator tool called with expression: {expression}")
    return eval(expression)


@tool_metadata(
    ToolMetadata(
        description="Get latitude and longitude coordinates for any place name or address"
    )
)
@function_tool
async def get_latitude_and_longitude(place: str) -> str:
    """Get the latitude and longitude coordinates for a given place name.
    :param place: The name of the place or address to geocode.
    """
    logger.info(f"Geocoding tool called for place: {place}")
    try:
        geolocator = Nominatim(user_agent="actors-backend")
        location = geolocator.geocode(place)

        if location:
            logger.debug(
                f"Found coordinates for {place}: {location.latitude}, {location.longitude}"
            )
            return f"Latitude: {location.latitude}, Longitude: {location.longitude}"
        else:
            logger.warning(f"No coordinates found for place: {place}")
            return f"Could not find coordinates for: {place}"
    except Exception as e:
        logger.error(f"Error geocoding place {place}: {str(e)}", exc_info=True)
        return f"Error getting coordinates for {place}: {str(e)}"


@tool_metadata(
    ToolMetadata(
        description="Get current time in any timezone with formatted output"
    )
)
@function_tool
async def get_current_time(timezone: str = "UTC") -> str:
    """Get the current time in a specific timezone.
    :param timezone: The timezone name (e.g., 'America/New_York', 'Europe/London', 'Asia/Tokyo')
    """
    logger.info(f"Getting current time for timezone: {timezone}")
    try:
        tz = pytz.timezone(timezone)
        current_time = datetime.now(tz)
        logger.debug(f"Current time in {timezone}: {current_time}")
        return f"Current time in {timezone}: {current_time.strftime('%Y-%m-%d %H:%M:%S %Z')}"
    except pytz.exceptions.UnknownTimeZoneError:
        logger.error(f"Unknown timezone: {timezone}")
        available_timezones = ", ".join(pytz.common_timezones[:10])
        return f"Unknown timezone: {timezone}. Some valid timezones are: {available_timezones}..."
    except Exception as e:
        logger.error(f"Error getting time for timezone {timezone}: {str(e)}", exc_info=True)
        return f"Error getting time: {str(e)}"


@tool_metadata(
    ToolMetadata(
        description="Calculate dates by adding or subtracting days from a given date"
    )
)
@function_tool
async def date_calculator(date: str, operation: str, days: int) -> str:
    """Add or subtract days from a date.
    :param date: The starting date in YYYY-MM-DD format
    :param operation: Either 'add' or 'subtract'
    :param days: Number of days to add or subtract
    """
    logger.info(f"Date calculation: {operation} {days} days to/from {date}")
    try:
        start_date = datetime.strptime(date, "%Y-%m-%d")
        
        if operation.lower() == "add":
            result_date = start_date + timedelta(days=days)
        elif operation.lower() == "subtract":
            result_date = start_date - timedelta(days=days)
        else:
            return f"Invalid operation: {operation}. Use 'add' or 'subtract'"
        
        logger.debug(f"Date calculation result: {result_date.strftime('%Y-%m-%d')}")
        return f"Result: {result_date.strftime('%Y-%m-%d')} ({result_date.strftime('%A, %B %d, %Y')})"
    except ValueError as e:
        logger.error(f"Invalid date format: {date}")
        return f"Invalid date format. Please use YYYY-MM-DD format (e.g., 2024-12-29)"
    except Exception as e:
        logger.error(f"Error in date calculation: {str(e)}", exc_info=True)
        return f"Error calculating date: {str(e)}"


@tool_metadata(
    ToolMetadata(
        description="Calculate the difference between two dates in days"
    )
)
@function_tool
async def date_difference(start_date: str, end_date: str) -> str:
    """Calculate the difference between two dates.
    :param start_date: The starting date in YYYY-MM-DD format
    :param end_date: The ending date in YYYY-MM-DD format
    """
    logger.info(f"Calculating difference between {start_date} and {end_date}")
    try:
        start = datetime.strptime(start_date, "%Y-%m-%d")
        end = datetime.strptime(end_date, "%Y-%m-%d")
        
        difference = end - start
        days = difference.days
        
        logger.debug(f"Date difference: {days} days")
        
        if days == 0:
            return "The dates are the same"
        elif days > 0:
            return f"{days} days between {start_date} and {end_date}"
        else:
            return f"{abs(days)} days between {end_date} and {start_date} (dates reversed)"
    except ValueError:
        logger.error(f"Invalid date format in date_difference")
        return "Invalid date format. Please use YYYY-MM-DD format (e.g., 2024-12-29)"
    except Exception as e:
        logger.error(f"Error calculating date difference: {str(e)}", exc_info=True)
        return f"Error calculating date difference: {str(e)}"


@tool_metadata(
    ToolMetadata(
        description="Convert between different units of measurement (length, weight, temperature, volume)"
    )
)
@function_tool
async def unit_converter(value: float, from_unit: str, to_unit: str) -> str:
    """Convert between different units of measurement.
    :param value: The numeric value to convert
    :param from_unit: The unit to convert from (e.g., 'meters', 'feet', 'kg', 'pounds', 'celsius', 'fahrenheit')
    :param to_unit: The unit to convert to
    """
    logger.info(f"Unit conversion: {value} {from_unit} to {to_unit}")
    
    # Define conversion factors
    conversions = {
        # Length conversions
        ('meters', 'feet'): 3.28084,
        ('feet', 'meters'): 0.3048,
        ('meters', 'yards'): 1.09361,
        ('yards', 'meters'): 0.9144,
        ('kilometers', 'miles'): 0.621371,
        ('miles', 'kilometers'): 1.60934,
        ('centimeters', 'inches'): 0.393701,
        ('inches', 'centimeters'): 2.54,
        
        # Weight conversions
        ('kilograms', 'pounds'): 2.20462,
        ('pounds', 'kilograms'): 0.453592,
        ('grams', 'ounces'): 0.035274,
        ('ounces', 'grams'): 28.3495,
        ('tons', 'pounds'): 2000,
        ('pounds', 'tons'): 0.0005,
        
        # Volume conversions
        ('liters', 'gallons'): 0.264172,
        ('gallons', 'liters'): 3.78541,
        ('milliliters', 'fluid_ounces'): 0.033814,
        ('fluid_ounces', 'milliliters'): 29.5735,
        ('cubic_meters', 'cubic_feet'): 35.3147,
        ('cubic_feet', 'cubic_meters'): 0.0283168,
    }
    
    from_unit_lower = from_unit.lower().replace(' ', '_')
    to_unit_lower = to_unit.lower().replace(' ', '_')
    
    try:
        # Handle temperature conversions separately
        if from_unit_lower in ['celsius', 'fahrenheit', 'kelvin'] and to_unit_lower in ['celsius', 'fahrenheit', 'kelvin']:
            if from_unit_lower == 'celsius':
                if to_unit_lower == 'fahrenheit':
                    result = (value * 9/5) + 32
                elif to_unit_lower == 'kelvin':
                    result = value + 273.15
                else:
                    result = value
            elif from_unit_lower == 'fahrenheit':
                if to_unit_lower == 'celsius':
                    result = (value - 32) * 5/9
                elif to_unit_lower == 'kelvin':
                    result = (value - 32) * 5/9 + 273.15
                else:
                    result = value
            elif from_unit_lower == 'kelvin':
                if to_unit_lower == 'celsius':
                    result = value - 273.15
                elif to_unit_lower == 'fahrenheit':
                    result = (value - 273.15) * 9/5 + 32
                else:
                    result = value
        else:
            # Check direct conversion
            if (from_unit_lower, to_unit_lower) in conversions:
                result = value * conversions[(from_unit_lower, to_unit_lower)]
            # Check reverse conversion
            elif (to_unit_lower, from_unit_lower) in conversions:
                result = value / conversions[(to_unit_lower, from_unit_lower)]
            # Check if same unit
            elif from_unit_lower == to_unit_lower:
                result = value
            else:
                return f"Conversion from {from_unit} to {to_unit} is not supported"
        
        logger.debug(f"Conversion result: {value} {from_unit} = {result:.4f} {to_unit}")
        return f"{value} {from_unit} = {result:.4f} {to_unit}"
        
    except Exception as e:
        logger.error(f"Error in unit conversion: {str(e)}", exc_info=True)
        return f"Error converting units: {str(e)}"


@tool_metadata(
    ToolMetadata(
        description="Convert currency amounts using real-time exchange rates"
    )
)
@function_tool
async def currency_converter(amount: float, from_currency: str, to_currency: str) -> str:
    """Convert currency amounts using exchange rates.
    :param amount: The amount to convert
    :param from_currency: The source currency code (e.g., 'USD', 'EUR', 'GBP')
    :param to_currency: The target currency code
    """
    logger.info(f"Currency conversion: {amount} {from_currency} to {to_currency}")
    
    from_currency = from_currency.upper()
    to_currency = to_currency.upper()
    
    # For demo purposes, using a free API that doesn't require authentication
    # In production, you'd want to use a more robust service with an API key
    try:
        # Using exchangerate-api.com free tier
        url = f"https://api.exchangerate-api.com/v4/latest/{from_currency}"
        
        response = requests.get(url, timeout=10)
        if response.status_code != 200:
            logger.error(f"API request failed with status {response.status_code}")
            return f"Error: Unable to fetch exchange rates (status {response.status_code})"
        
        data = response.json()
        
        if to_currency not in data['rates']:
            return f"Error: {to_currency} is not a supported currency"
        
        rate = data['rates'][to_currency]
        converted_amount = amount * rate
        
        logger.debug(f"Exchange rate: 1 {from_currency} = {rate} {to_currency}")
        return f"{amount} {from_currency} = {converted_amount:.2f} {to_currency} (Rate: 1 {from_currency} = {rate:.4f} {to_currency})"
        
    except requests.exceptions.Timeout:
        logger.error("Currency API request timed out")
        return "Error: Request timed out. Please try again."
    except requests.exceptions.RequestException as e:
        logger.error(f"Currency API request failed: {str(e)}", exc_info=True)
        return f"Error: Unable to connect to currency service"
    except KeyError as e:
        logger.error(f"Invalid currency code: {str(e)}")
        return f"Error: {from_currency} is not a supported currency"
    except Exception as e:
        logger.error(f"Error in currency conversion: {str(e)}", exc_info=True)
        return f"Error converting currency: {str(e)}"


@tool_metadata(
    ToolMetadata(
        description="Get current stock price and basic information for a given stock symbol"
    )
)
@function_tool
async def get_stock_price(symbol: str) -> str:
    """Get current stock price for a given symbol.
    :param symbol: The stock symbol (e.g., 'AAPL', 'GOOGL', 'MSFT')
    """
    logger.info(f"Getting stock price for symbol: {symbol}")
    
    symbol = symbol.upper()
    
    try:
        # Using Alpha Vantage free API (requires API key)
        # For demo, using a mock response. In production, you'd need to:
        # 1. Get a free API key from https://www.alphavantage.co/support/#api-key
        # 2. Store it in environment variable
        config = get_config()
        api_key = config.alpha_vantage_api_key or 'JIM66K3NE67V5YEG'
        
        if api_key == 'demo':
            # Mock response for demo
            logger.warning("Using demo mode for stock prices. Set ALPHA_VANTAGE_API_KEY for real data.")
            mock_prices = {
                'AAPL': {'price': 195.89, 'change': 2.34, 'change_percent': '1.21%', 'volume': '52,345,678'},
                'GOOGL': {'price': 141.23, 'change': -0.87, 'change_percent': '-0.61%', 'volume': '23,456,789'},
                'MSFT': {'price': 378.91, 'change': 4.56, 'change_percent': '1.22%', 'volume': '29,876,543'},
                'TSLA': {'price': 242.84, 'change': -3.21, 'change_percent': '-1.30%', 'volume': '87,654,321'},
            }
            
            if symbol in mock_prices:
                data = mock_prices[symbol]
                change_symbol = '+' if data['change'] > 0 else ''
                return f"{symbol}: ${data['price']} {change_symbol}{data['change']} ({data['change_percent']}) Volume: {data['volume']}"
            else:
                return f"Demo mode: {symbol} not in sample data. Available: {', '.join(mock_prices.keys())}"
        
        # Real API call (when API key is set)
        url = f"https://www.alphavantage.co/query?function=GLOBAL_QUOTE&symbol={symbol}&apikey={api_key}"
        
        response = requests.get(url, timeout=10)
        if response.status_code != 200:
            return f"Error: Unable to fetch stock data (status {response.status_code})"
        
        data = response.json()
        
        if 'Global Quote' not in data or not data['Global Quote']:
            if 'Note' in data:
                return "Error: API rate limit reached. Please try again later."
            return f"Error: No data found for symbol {symbol}"
        
        quote = data['Global Quote']
        price = float(quote['05. price'])
        change = float(quote['09. change'])
        change_percent = quote['10. change percent']
        volume = int(quote['06. volume'])
        
        change_symbol = '+' if change > 0 else ''
        return f"{symbol}: ${price:.2f} {change_symbol}{change:.2f} ({change_percent}) Volume: {volume:,}"
        
    except requests.exceptions.Timeout:
        logger.error("Stock API request timed out")
        return "Error: Request timed out. Please try again."
    except Exception as e:
        logger.error(f"Error getting stock price: {str(e)}", exc_info=True)
        return f"Error getting stock price: {str(e)}"


@tool_metadata(
    ToolMetadata(
        description="Get detailed stock information using Yahoo Finance (price, metrics, company info)"
    )
)
@function_tool
async def get_stock_info_yfinance(symbol: str, info_type: str = "summary") -> str:
    """Get detailed stock information using Yahoo Finance.
    :param symbol: The stock symbol (e.g., 'AAPL', 'GOOGL', 'MSFT')
    :param info_type: Type of info to retrieve - 'summary', 'price', 'financials', 'holders', 'news'
    """
    logger.info(f"Getting detailed stock info for {symbol}, type: {info_type}")
    
    try:
        # Create ticker object
        ticker = yf.Ticker(symbol.upper())
        
        if info_type.lower() == "summary":
            # Get basic info and current price
            info = ticker.info
            
            # Extract key information
            current_price = info.get('currentPrice', info.get('regularMarketPrice', 'N/A'))
            prev_close = info.get('previousClose', 'N/A')
            open_price = info.get('open', info.get('regularMarketOpen', 'N/A'))
            day_high = info.get('dayHigh', info.get('regularMarketDayHigh', 'N/A'))
            day_low = info.get('dayLow', info.get('regularMarketDayLow', 'N/A'))
            volume = info.get('volume', info.get('regularMarketVolume', 'N/A'))
            market_cap = info.get('marketCap', 'N/A')
            pe_ratio = info.get('trailingPE', 'N/A')
            dividend_yield = info.get('dividendYield', 0)
            
            # Calculate change
            if current_price != 'N/A' and prev_close != 'N/A':
                change = current_price - prev_close
                change_pct = (change / prev_close) * 100
                change_str = f"{'+' if change >= 0 else ''}{change:.2f} ({change_pct:.2f}%)"
            else:
                change_str = "N/A"
            
            # Format market cap
            if market_cap != 'N/A':
                if market_cap >= 1e12:
                    market_cap_str = f"${market_cap/1e12:.2f}T"
                elif market_cap >= 1e9:
                    market_cap_str = f"${market_cap/1e9:.2f}B"
                elif market_cap >= 1e6:
                    market_cap_str = f"${market_cap/1e6:.2f}M"
                else:
                    market_cap_str = f"${market_cap:,.0f}"
            else:
                market_cap_str = "N/A"
            
            # Format dividend yield
            div_yield_str = f"{dividend_yield*100:.2f}%" if dividend_yield else "N/A"
            
            return f"""
{info.get('longName', symbol.upper())} ({symbol.upper()})
Current Price: ${current_price} {change_str}
Previous Close: ${prev_close}
Open: ${open_price}
Day Range: ${day_low} - ${day_high}
Volume: {volume:,} if isinstance(volume, (int, float)) else volume
Market Cap: {market_cap_str}
P/E Ratio: {pe_ratio:.2f} if isinstance(pe_ratio, (int, float)) else pe_ratio
Dividend Yield: {div_yield_str}
52-Week Range: ${info.get('fiftyTwoWeekLow', 'N/A')} - ${info.get('fiftyTwoWeekHigh', 'N/A')}
"""
            
        elif info_type.lower() == "price":
            # Get detailed price history
            hist = ticker.history(period="5d")
            if hist.empty:
                return f"No price history available for {symbol}"
            
            result = f"5-Day Price History for {symbol.upper()}:\n"
            for date, row in hist.iterrows():
                result += f"{date.strftime('%Y-%m-%d')}: Open=${row['Open']:.2f}, High=${row['High']:.2f}, Low=${row['Low']:.2f}, Close=${row['Close']:.2f}, Volume={row['Volume']:,}\n"
            return result
            
        elif info_type.lower() == "financials":
            # Get financial data
            info = ticker.info
            financials = ticker.quarterly_financials
            
            revenue = info.get('totalRevenue', 'N/A')
            profit = info.get('netIncomeToCommon', 'N/A')
            eps = info.get('trailingEps', 'N/A')
            
            result = f"Financial Summary for {symbol.upper()}:\n"
            result += f"Total Revenue: ${revenue:,.0f}\n" if isinstance(revenue, (int, float)) else f"Total Revenue: {revenue}\n"
            result += f"Net Income: ${profit:,.0f}\n" if isinstance(profit, (int, float)) else f"Net Income: {profit}\n"
            result += f"EPS (TTM): ${eps:.2f}\n" if isinstance(eps, (int, float)) else f"EPS (TTM): {eps}\n"
            result += f"Profit Margin: {info.get('profitMargins', 'N/A'):.2%}\n" if info.get('profitMargins') else "Profit Margin: N/A\n"
            
            return result
            
        elif info_type.lower() == "holders":
            # Get major holders information
            try:
                holders = ticker.major_holders
                institutional = ticker.institutional_holders
                
                result = f"Major Holders for {symbol.upper()}:\n"
                if not holders.empty:
                    for _, row in holders.iterrows():
                        result += f"{row[0]}: {row[1]}\n"
                
                if not institutional.empty:
                    result += f"\nTop Institutional Holders:\n"
                    for i, row in institutional.head(5).iterrows():
                        result += f"{row['Holder']}: {row['% Out']:.2f}% ({row['Shares']:,} shares)\n"
                
                return result
            except:
                return f"Holder information not available for {symbol}"
                
        elif info_type.lower() == "news":
            # Get recent news
            news = ticker.news
            if not news:
                return f"No recent news available for {symbol}"
                
            result = f"Recent News for {symbol.upper()}:\n"
            for item in news[:5]:  # Get top 5 news items
                title = item.get('title', 'No title')
                publisher = item.get('publisher', 'Unknown')
                link = item.get('link', '')
                result += f"• {title} ({publisher})\n"
                
            return result
            
        else:
            return f"Invalid info_type. Choose from: 'summary', 'price', 'financials', 'holders', 'news'"
            
    except Exception as e:
        logger.error(f"Error getting stock info from yfinance: {str(e)}", exc_info=True)
        return f"Error retrieving stock information for {symbol}: {str(e)}"


# Registry of all available tools
AVAILABLE_TOOLS: Dict[str, FunctionTool] = {
    "get_weather": get_weather,
    "calculator": calculator,
    "get_latitude_and_longitude": get_latitude_and_longitude,
    "get_current_time": get_current_time,
    "date_calculator": date_calculator,
    "date_difference": date_difference,
    "unit_converter": unit_converter,
    "currency_converter": currency_converter,
    "get_stock_price": get_stock_price,
    "get_stock_info_yfinance": get_stock_info_yfinance,
}
