from http.server import HTTPServer, SimpleHTTPRequestHandler
import json
import subprocess
import sys
from urllib.parse import parse_qs, urlparse
import logging
import os

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class SteamHandler(SimpleHTTPRequestHandler):
    def log_message(self, format, *args):
        logger.info("%s - %s", self.address_string(), format % args)

    def _set_headers(self, content_type='text/html'):
        logger.info(f"Setting headers with content type: {content_type}")
        self.send_header('Content-type', content_type)
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        self.send_header('Cache-Control', 'no-cache, no-store, must-revalidate')
        self.send_header('Pragma', 'no-cache')
        self.send_header('Expires', '0')

    def do_OPTIONS(self):
        logger.info("Handling OPTIONS request")
        self.send_response(200)
        self._set_headers()
        self.end_headers()

    def do_POST(self):
        logger.info(f"Received POST request for path: {self.path}")
        logger.info(f"Request headers: {dict(self.headers)}")
        
        if self.path == '/fetch_data':
            try:
                # Read the request body
                content_length = int(self.headers.get('Content-Length', 0))
                logger.info(f"Content length: {content_length}")
                
                if content_length > 0:
                    post_data = self.rfile.read(content_length)
                    logger.info(f"Raw post data: {post_data}")
                    try:
                        data = json.loads(post_data.decode('utf-8'))
                        logger.info(f"Parsed data: {data}")
                    except json.JSONDecodeError as e:
                        logger.error(f"Failed to decode JSON: {e}")
                        self.send_error_response('Invalid JSON data')
                        return
                    
                    steam_id = data.get('steamId')
                    steam_api_key = data.get('steamApiKey')
                    logger.info(f"Extracted steam_id: {steam_id}")
                    logger.info(f"Extracted steam_api_key: {'<provided>' if steam_api_key else '<missing>'}")
                    
                    if not steam_id or not steam_id.isdigit() or len(steam_id) != 17:
                        logger.error(f"Invalid Steam64 ID: {steam_id}")
                        self.send_error_response('Invalid Steam64 ID. Please enter a valid 17-digit Steam64 ID.')
                        return
                    if not steam_api_key or not isinstance(steam_api_key, str) or len(steam_api_key) < 10:
                        logger.error(f"Invalid Steam API Key: {steam_api_key}")
                        self.send_error_response('Invalid Steam API Key. Please enter a valid Steam Web API Key.')
                        return

                    logger.info(f"Running fetchsteamgametime.py with Steam ID and API Key")
                    # Run the Python script with the Steam ID and API Key
                    result = subprocess.run(
                        [sys.executable, 'fetchsteamgametime.py', steam_id, steam_api_key],
                        capture_output=True,
                        text=True
                    )

                    logger.info(f"Script output: {result.stdout}")
                    logger.info(f"Script error: {result.stderr}")
                    logger.info(f"Script return code: {result.returncode}")

                    if result.returncode == 0:
                        logger.info("Successfully fetched Steam data")
                        self.send_success_response()
                    else:
                        # Use the error message from the script's output
                        error_msg = result.stdout.strip() or result.stderr.strip() or 'Failed to fetch Steam data'
                        logger.error(f"Error fetching Steam data: {error_msg}")
                        self.send_error_response(error_msg)
                else:
                    logger.error("No content in POST request")
                    self.send_error_response('No data received')
            except Exception as e:
                logger.error(f"Exception during POST request: {str(e)}", exc_info=True)
                self.send_error_response(str(e))
        else:
            logger.error(f"Invalid POST path: {self.path}")
            self.send_error(404, 'Not Found')

    def send_success_response(self):
        logger.info("Sending success response")
        self.send_response(200)
        self._set_headers('application/json')
        self.end_headers()
        response = json.dumps({
            'success': True,
            'redirect': '/index.html'
        })
        logger.info(f"Sending response: {response}")
        self.wfile.write(response.encode())

    def send_error_response(self, error_message):
        logger.info(f"Sending error response: {error_message}")
        self.send_response(200)  # Still 200 to handle it on client side
        self._set_headers('application/json')
        self.end_headers()
        response = json.dumps({
            'success': False,
            'error': error_message
        })
        logger.info(f"Sending response: {response}")
        self.wfile.write(response.encode())

    def do_GET(self):
        logger.info(f"Received GET request for path: {self.path}")
        
        # For root and index.html, serve index.html directly
        if self.path in ['/', '/index.html']:
            try:
                with open('index.html', 'rb') as f:
                    self.send_response(200)
                    self._set_headers('text/html')
                    self.end_headers()
                    self.wfile.write(f.read())
            except Exception as e:
                logger.error(f"Error reading index.html: {e}")
                self.send_error(500, f"Error reading index.html: {e}")
            return

        # For fetch.html, serve it directly
        if self.path == '/fetch.html':
            try:
                with open('fetch.html', 'rb') as f:
                    self.send_response(200)
                    self._set_headers('text/html')
                    self.end_headers()
                    self.wfile.write(f.read())
            except Exception as e:
                logger.error(f"Error reading fetch.html: {e}")
                self.send_error(500, f"Error reading fetch.html: {e}")
            return

        # For all other files, use the default handler
        return SimpleHTTPRequestHandler.do_GET(self)

def run_server(port=8080):
    # Verify fetch.html exists
    if not os.path.exists('fetch.html'):
        logger.error("fetch.html not found in the current directory!")
        return

    server_address = ('', port)
    httpd = HTTPServer(server_address, SteamHandler)
    logger.info(f"Server running at http://localhost:{port}")
    logger.info("Serving fetch.html as the default page")
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        logger.info("Server stopped by user")
    except Exception as e:
        logger.error(f"Server error: {e}")

if __name__ == '__main__':
    run_server() 