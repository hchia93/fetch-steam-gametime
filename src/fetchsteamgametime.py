import requests
import json
import sys
import argparse
import logging
import time
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def create_session():
    session = requests.Session()
    retry_strategy = Retry(
        total=3,  # number of retries
        backoff_factor=1,  # wait 1, 2, 4 seconds between retries
        status_forcelist=[429, 500, 502, 503, 504]  # HTTP status codes to retry on
    )
    adapter = HTTPAdapter(max_retries=retry_strategy)
    session.mount("http://", adapter)
    session.mount("https://", adapter)
    return session

def fetch_playtime(steam_id, api_key):
    url = f'https://api.steampowered.com/IPlayerService/GetOwnedGames/v1/?key={api_key}&steamid={steam_id}&include_appinfo=true&format=json'
    logger.info(f"Fetching data from Steam API for ID: {steam_id}")
    
    try:
        session = create_session()
        response = session.get(url)
        logger.info(f"Steam API Response Status: {response.status_code}")
        
        if response.status_code == 429:
            logger.error("Rate limit exceeded. Please wait a few minutes before trying again.")
            return False, "Steam API rate limit exceeded. Please wait a few minutes before trying again."
        
        response.raise_for_status()
        data = response.json()

        if 'response' not in data or 'games' not in data['response']:
            error_msg = "Could not fetch games data from Steam API. The profile might be private or the Steam ID might be invalid."
            logger.error(error_msg)
            return False, error_msg

        games = data['response']['games']
        formatted = []
        
        for game in games:
            if game['playtime_forever'] > 0:
                game_data = {
                    'name': game['name'],
                    'playtime_hours': round(game['playtime_forever'] / 60, 1),
                }
                if 'img_logo_url' in game:
                    game_data['img_logo_url'] = f"https://cdn.cloudflare.steamstatic.com/steamcommunity/public/images/apps/{game['appid']}/{game['img_logo_url']}.jpg"
                formatted.append(game_data)

        # Save as JSON
        with open('steam_playtime.json', 'w', encoding='utf-8') as f:
            json.dump(formatted, f, indent=4)

        logger.info(f"Successfully saved {len(formatted)} games to steam_playtime.json")
        return True, f"Successfully fetched data for {len(formatted)} games"
        
    except requests.exceptions.RequestException as e:
        error_msg = f"Error connecting to Steam API: {str(e)}"
        logger.error(error_msg)
        if hasattr(e, 'response') and e.response is not None:
            logger.error(f"Steam API Error Response: {e.response.text}")
        return False, error_msg
    except json.JSONDecodeError as e:
        error_msg = f"Error parsing Steam API response: {str(e)}"
        logger.error(error_msg)
        return False, error_msg
    except Exception as e:
        error_msg = f"An unexpected error occurred: {str(e)}"
        logger.error(error_msg, exc_info=True)
        return False, error_msg

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Fetch Steam playtime data for a given Steam64 ID')
    parser.add_argument('steam_id', help='Steam64 ID to fetch data for')
    parser.add_argument('api_key', help='Steam Web API Key to use for fetching data')
    args = parser.parse_args()
    
    success, message = fetch_playtime(args.steam_id, args.api_key)
    if not success:
        print(message)  # Print the error message for the server to capture
    sys.exit(0 if success else 1)
