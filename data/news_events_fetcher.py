import feedparser
import logging
import requests
from icalendar import Calendar, Event as CalendarEvent
from datetime import datetime, date, time

# Configure basic logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# --- Financial News Fetching ---

def fetch_financial_news_rss(rss_urls: list, max_items_per_feed: int = 10) -> list:
    """
    Fetches financial news from a list of RSS feeds.

    Args:
        rss_urls (list): A list of RSS feed URLs.
        max_items_per_feed (int): Maximum number of news items to fetch from each feed.

    Returns:
        list: A list of news items, where each item is a dictionary.
    """
    news_items = []
    for url in rss_urls:
        logging.info(f"Fetching news from RSS feed: {url}")
        try:
            feed = feedparser.parse(url)
            count = 0
            for entry in feed.entries:
                if count >= max_items_per_feed:
                    break
                
                published_date = None
                if hasattr(entry, 'published_parsed') and entry.published_parsed:
                    try:
                        published_date = datetime(*entry.published_parsed[:6]).isoformat()
                    except Exception as e:
                        logging.warning(f"Could not parse published_parsed for entry in {url}: {entry.published_parsed}, error: {e}")
                elif hasattr(entry, 'updated_parsed') and entry.updated_parsed: # Fallback to updated
                     try:
                        published_date = datetime(*entry.updated_parsed[:6]).isoformat()
                     except Exception as e:
                        logging.warning(f"Could not parse updated_parsed for entry in {url}: {entry.updated_parsed}, error: {e}")

                news_items.append({
                    'title': getattr(entry, 'title', 'N/A'),
                    'link': getattr(entry, 'link', 'N/A'),
                    'published_date': published_date,
                    'summary': getattr(entry, 'summary', 'N/A'),
                    'source_url': url
                })
                count += 1
            logging.info(f"Fetched {count} items from {url}")
        except Exception as e:
            logging.error(f"Error fetching or parsing RSS feed {url}: {e}")
    return news_items

def fetch_financial_news_mock(count: int = 5) -> list:
    """
    Returns a predefined list of dummy news articles.

    Args:
        count (int): The number of mock news items to return.

    Returns:
        list: A list of mock news items.
    """
    logging.info(f"Returning {count} mock financial news items.")
    mock_news = [
        {
            'title': 'Global Markets Rally on Positive Economic Outlook',
            'link': 'http://example.com/news/1',
            'published_date': datetime(2024, 5, 1, 10, 0, 0).isoformat(),
            'summary': 'Stock markets worldwide saw significant gains today...',
            'source_url': 'mock_source_1'
        },
        {
            'title': 'Tech Stocks Surge After New AI Breakthrough Announcement',
            'link': 'http://example.com/news/2',
            'published_date': datetime(2024, 5, 1, 12, 30, 0).isoformat(),
            'summary': 'Major technology companies experienced a surge in stock prices...',
            'source_url': 'mock_source_2'
        },
        {
            'title': 'Oil Prices Fluctuate Amidst Geopolitical Tensions',
            'link': 'http://example.com/news/3',
            'published_date': datetime(2024, 5, 2, 9, 15, 0).isoformat(),
            'summary': 'Crude oil prices showed volatility as new geopolitical events unfolded...',
            'source_url': 'mock_source_1'
        },
        {
            'title': 'Central Bank Hints at Interest Rate Adjustments',
            'link': 'http://example.com/news/4',
            'published_date': datetime(2024, 5, 2, 14, 0, 0).isoformat(),
            'summary': 'In a recent address, the Central Bank governor hinted at potential changes...',
            'source_url': 'mock_source_3'
        },
        {
            'title': 'Cryptocurrency Market Sees Mixed Reactions to Regulatory News',
            'link': 'http://example.com/news/5',
            'published_date': datetime(2024, 5, 3, 11, 0, 0).isoformat(),
            'summary': 'The cryptocurrency market responded with mixed sentiment to new regulatory proposals...',
            'source_url': 'mock_source_2'
        }
    ]
    return mock_news[:count]

# --- Economic Events Fetching ---

def fetch_economic_events_ical(ical_url: str) -> list:
    """
    Fetches economic events from an iCalendar (ICS) feed.

    Args:
        ical_url (str): The URL of the iCalendar feed.

    Returns:
        list: A list of economic events, where each event is a dictionary.
    """
    events = []
    logging.info(f"Fetching economic events from iCal feed: {ical_url}")
    try:
        response = requests.get(ical_url, timeout=10)
        response.raise_for_status() # Raise an exception for HTTP errors
        calendar_data = response.text
        cal = Calendar.from_ical(calendar_data)

        for component in cal.walk():
            if component.name == "VEVENT":
                dtstart = component.get('dtstart')
                summary = component.get('summary')
                description = component.get('description', '') # Forex Factory often has impact in description

                event_date = None
                event_time = None
                country = None
                impact = 'N/A' # Default impact

                if dtstart:
                    dt_value = dtstart.dt
                    if isinstance(dt_value, datetime):
                        event_date = dt_value.strftime('%Y-%m-%d')
                        event_time = dt_value.strftime('%H:%M')
                    elif isinstance(dt_value, date): # Handle all-day events
                        event_date = dt_value.strftime('%Y-%m-%d')
                        event_time = 'All-Day'
                
                # Attempt to parse country and impact from summary or description (Forex Factory specific)
                # Example summary: "AUD - RBA Rate Statement" or "USD - FOMC Meeting Minutes"
                # Example description: "Impact: High Expected"
                if summary:
                    summary_str = str(summary)
                    parts = summary_str.split(' - ', 1)
                    if len(parts) > 0:
                        # Basic country code extraction (first 3 chars if uppercase)
                        potential_country = parts[0][:3]
                        if potential_country.isupper() and len(potential_country) == 3:
                            country = potential_country
                    
                    if "High Impact Expected" in description:
                        impact = "High"
                    elif "Med Impact Expected" in description:
                        impact = "Medium"
                    elif "Low Impact Expected" in description:
                        impact = "Low"

                events.append({
                    'date': event_date,
                    'time': event_time,
                    'event_name': str(summary) if summary else 'N/A',
                    'country': country if country else 'N/A',
                    'impact': impact,
                    'description': str(description)
                })
        logging.info(f"Fetched {len(events)} economic events from {ical_url}")
    except requests.exceptions.RequestException as e:
        logging.error(f"Network error fetching iCal feed {ical_url}: {e}")
    except Exception as e:
        logging.error(f"Error parsing iCal feed {ical_url}: {e}")
    return events

def fetch_economic_events_mock(start_date_str: str, end_date_str: str) -> list:
    """
    Returns a predefined list of dummy economic events for a given date range.

    Args:
        start_date_str (str): Start date in 'YYYY-MM-DD' format.
        end_date_str (str): End date in 'YYYY-MM-DD' format. (Note: This mock doesn't currently filter by date)

    Returns:
        list: A list of mock economic events.
    """
    logging.info(f"Returning mock economic events (date range: {start_date_str} to {end_date_str} - currently not filtered).")
    # For simplicity, this mock doesn't filter by date range, but a real implementation would.
    mock_events = [
        {'date': '2024-05-20', 'time': '10:00', 'event_name': 'FOMC Meeting Minutes', 'country': 'USD', 'impact': 'High'},
        {'date': '2024-05-21', 'time': '08:30', 'event_name': 'CPI m/m', 'country': 'CAD', 'impact': 'High'},
        {'date': '2024-05-21', 'time': '14:00', 'event_name': 'ECB President Speaks', 'country': 'EUR', 'impact': 'Medium'},
        {'date': '2024-05-22', 'time': '02:00', 'event_name': 'Retail Sales y/y', 'country': 'CNY', 'impact': 'Medium'},
        {'date': '2024-05-23', 'time': 'All-Day', 'event_name': 'Bank Holiday', 'country': 'GBP', 'impact': 'Low'},
    ]
    return mock_events

# --- Future Enhancements: API-Key Based News Services ---
# 1. NewsAPI.org:
#    - Website: https://newsapi.org/
#    - Authentication: API Key required.
#    - Features: Access to news articles from a wide range of sources, filter by keywords, category, language, country.
#    - Example (conceptual, requires API key):
#      ```python
#      # import requests
#      # API_KEY = 'YOUR_NEWSAPI_KEY'
#      # query = 'quantitative trading OR algorithmic trading'
#      # url = f'https://newsapi.org/v2/everything?q={query}&apiKey={API_KEY}&sortBy=publishedAt&language=en'
#      # response = requests.get(url)
#      # articles = response.json().get('articles', [])
#      # for article in articles:
#      #     print(f"Title: {article['title']}, Source: {article['source']['name']}")
#      ```

# 2. The Guardian API:
#    - Website: https://open-platform.theguardian.com/
#    - Authentication: API Key required.
#    - Features: Access to articles from The Guardian, search by keywords, sections, tags.
#    - Example (conceptual, requires API key):
#      ```python
#      # import requests
#      # API_KEY = 'YOUR_GUARDIAN_API_KEY'
#      # query = 'financial markets'
#      # url = f'https://content.guardianapis.com/search?q={query}&api-key={API_KEY}&show-fields=headline,shortUrl,firstPublicationDate'
#      # response = requests.get(url)
#      # results = response.json().get('response', {}).get('results', [])
#      # for result in results:
#      #     print(f"Title: {result['fields']['headline']}, URL: {result['fields']['shortUrl']}")
#      ```
# Other potential APIs: Alpha Vantage (has news sentiment), Bloomberg API (enterprise), Reuters API (enterprise).


if __name__ == '__main__':
    logging.info("--- Starting News & Events Fetcher Example ---")

    # --- RSS News Example ---
    sample_rss_feeds = [
        'https://finance.yahoo.com/news/rss',  # General financial news
        'https://www.nasdaq.com/feed/nasdaq-original/rss.xml', # Market specific news
        'http://feeds.marketwatch.com/marketwatch/topstories/' # Top stories
    ]
    # A more specific MarketWatch feed might be better, e.g., for a specific section if available.
    # Note: The reliability and content of public RSS feeds can vary.
    
    logging.info("\n--- Fetching Financial News from RSS ---")
    news = fetch_financial_news_rss(sample_rss_feeds, max_items_per_feed=3)
    if news:
        for i, item in enumerate(news):
            logging.info(f"News {i+1}: {item['title']} ({item['published_date']}) - {item['link']} (Source: {item['source_url']})")
    else:
        logging.info("No news fetched from RSS. Trying mock news...")
        news = fetch_financial_news_mock(3)
        for i, item in enumerate(news):
            logging.info(f"Mock News {i+1}: {item['title']} ({item['published_date']}) - {item['link']}")

    # --- Economic Events iCal Example ---
    # Using a static link to a weekly Forex Factory calendar.
    # For a real application, you might want to fetch this URL dynamically or have a more persistent source.
    # The version hash in the URL might change weekly.
    # A more stable (though potentially less detailed) alternative could be sought.
    # Example: https://www.forexfactory.com/calendar.php?week=this.ics (this format often works for webcal)
    # For this example, using the direct .ics link found previously.
    # It's possible the direct nfs.faireconomy.media link changes its version parameter frequently.
    # Let's try a more generic one, if it fails, the mock will be used.
    # forex_factory_ical_url = "https://www.forexfactory.com/calendar.php?download=this.ics" # Common pattern for webcal
    # The direct link from research was:
    forex_factory_ical_url = "https://nfs.faireconomy.media/ff_calendar_thisweek.ics" 
    # This URL structure might change, so error handling is important.

    logging.info(f"\n--- Fetching Economic Events from iCal ({forex_factory_ical_url}) ---")
    economic_events = fetch_economic_events_ical(forex_factory_ical_url)
    if economic_events:
        # Sort events by date and time for better readability
        economic_events.sort(key=lambda x: (x['date'] or '', x['time'] or ''))
        for i, event in enumerate(economic_events[:5]): # Display first 5 events
            logging.info(f"Event {i+1}: {event['date']} {event['time']} - {event['event_name']} (Country: {event['country']}, Impact: {event['impact']})")
    else:
        logging.info("No economic events fetched from iCal. Trying mock events...")
        economic_events = fetch_economic_events_mock('2024-05-20', '2024-05-25')
        for i, event in enumerate(economic_events):
            logging.info(f"Mock Event {i+1}: {event['date']} {event['time']} - {event['event_name']} (Country: {event['country']}, Impact: {event['impact']})")
    
    logging.info("\n--- News & Events Fetcher Example Finished ---")
