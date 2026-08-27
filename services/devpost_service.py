import requests
import logging
import time
from threading import Lock
from concurrent.futures import ThreadPoolExecutor

logger = logging.getLogger(__name__)

# Known Indian cities for location matching
INDIA_LOCATION_TERMS = [
    'india', 'mumbai', 'delhi', 'bangalore', 'bengaluru', 'hyderabad', 'chennai',
    'kolkata', 'pune', 'jaipur', 'ahmedabad', 'lucknow', 'indore', 'chandigarh',
    'kochi', 'coimbatore', 'thiruvananthapuram', 'gurgaon', 'noida', 'goa',
    'bhubaneswar', 'bhopal', 'nagpur', 'visakhapatnam', 'surat', 'vadodara'
]

# Thread-safe in-memory cache configuration
_cache_lock = Lock()
_DEVPOST_CACHE = {}  # Keys: (type, page) -> { "data": [...], "timestamp": float }
CACHE_TTL_SECONDS = 600  # 10 minutes cache lifespan

def _get_cached_data(cache_type, page):
    """Retrieve items from cache if present and valid."""
    with _cache_lock:
        key = (cache_type, page)
        if key in _DEVPOST_CACHE:
            cached = _DEVPOST_CACHE[key]
            if time.time() - cached['timestamp'] < CACHE_TTL_SECONDS:
                logger.info(f"Cache HIT for {cache_type} events, page {page}")
                return cached['data']
            else:
                logger.info(f"Cache EXPIRED for {cache_type} events, page {page}")
                del _DEVPOST_CACHE[key]
    return None

def _set_cached_data(cache_type, page, data):
    """Store fetched items in the cache."""
    with _cache_lock:
        key = (cache_type, page)
        _DEVPOST_CACHE[key] = {
            'data': data,
            'timestamp': time.time()
        }
        logger.info(f"Cache SET for {cache_type} events, page {page}")

def _fix_thumbnail(hackathon):
    """Ensure thumbnail URLs have a proper scheme."""
    if hackathon.get('thumbnail_url') and not hackathon['thumbnail_url'].startswith('http'):
        hackathon['thumbnail_url'] = 'https:' + hackathon['thumbnail_url']

def fetch_india_hackathons(page=1, max_results=10):
    """Fetch hackathons in India from Devpost API (uses cache)."""
    # Check Cache
    cached = _get_cached_data('india', page)
    if cached is not None:
        return cached

    logger.info(f"Cache MISS: Fetching page {page} India events from Devpost API")
    try:
        r = requests.get(
            f"https://devpost.com/api/hackathons?page={page}&search=india",
            timeout=5
        )
        if r.status_code == 200:
            data = r.json()
            hackathons = []
            for h in data.get('hackathons', []):
                location = h.get('displayed_location', {}).get('location', '').lower()
                if any(term in location for term in INDIA_LOCATION_TERMS):
                    _fix_thumbnail(h)
                    hackathons.append(h)
                    if len(hackathons) >= max_results:
                        break
            _set_cached_data('india', page, hackathons)
            return hackathons
        else:
            logger.warning(f"Devpost API returned status code {r.status_code} for India hackathons")
    except requests.exceptions.Timeout:
        logger.warning("Devpost API request timed out (India hackathons).")
    except requests.exceptions.RequestException as e:
        logger.warning(f"Failed to fetch India hackathons from Devpost: {e}")
    except Exception as e:
        logger.error(f"Unexpected error fetching India hackathons: {e}")
    return []

def fetch_global_hackathons(page=1, max_results=10):
    """Fetch global/online hackathons from Devpost API (uses cache)."""
    # Check Cache
    cached = _get_cached_data('global', page)
    if cached is not None:
        return cached

    logger.info(f"Cache MISS: Fetching page {page} Global events from Devpost API")
    try:
        r = requests.get(
            f"https://devpost.com/api/hackathons?page={page}",
            timeout=5
        )
        if r.status_code == 200:
            data = r.json()
            hackathons = data.get('hackathons', [])[:max_results]
            for h in hackathons:
                _fix_thumbnail(h)
            _set_cached_data('global', page, hackathons)
            return hackathons
        else:
            logger.warning(f"Devpost API returned status code {r.status_code} for global hackathons")
    except requests.exceptions.Timeout:
        logger.warning("Devpost API request timed out (global hackathons).")
    except requests.exceptions.RequestException as e:
        logger.warning(f"Failed to fetch global hackathons from Devpost: {e}")
    except Exception as e:
        logger.error(f"Unexpected error fetching global hackathons: {e}")
    return []

def fetch_upcoming_events(india_page=1, global_page=1, max_results=10):
    """Fetch both India and Global events in parallel using ThreadPoolExecutor."""
    with ThreadPoolExecutor(max_workers=2) as executor:
        india_future = executor.submit(fetch_india_hackathons, page=india_page, max_results=max_results)
        global_future = executor.submit(fetch_global_hackathons, page=global_page, max_results=max_results)
        
        india_events = india_future.result()
        global_events = global_future.result()
        
    return india_events, global_events
