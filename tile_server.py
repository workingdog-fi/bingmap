#!/usr/bin/env python3
import http.server
import urllib.request
import urllib.parse
from http.server import HTTPServer, BaseHTTPRequestHandler, ThreadingHTTPServer
import re
import os
import logging
import signal
import sys
import time
from concurrent.futures import ThreadPoolExecutor
import threading

# Configure logging
logging.basicConfig(
    level=getattr(logging, os.environ.get('LOG_LEVEL', 'INFO')),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class TileProxyHandler(BaseHTTPRequestHandler):
    # Class-level thread pool for tile fetching
    executor = ThreadPoolExecutor(max_workers=int(os.environ.get('WORKERS', '4')))
    
    def quadkey_to_zxy(self, quadkey):
        """Convert quadkey to z/x/y coordinates"""
        z = len(quadkey)
        x = 0
        y = 0
        
        for i in range(z):
            mask = 1 << (z - 1 - i)
            digit = quadkey[i]
            
            if digit == '1':
                x |= mask
            elif digit == '2':
                y |= mask
            elif digit == '3':
                x |= mask
                y |= mask
        
        return z, x, y
    
    def zxy_to_quadkey(self, z, x, y):
        """Convert z/x/y coordinates to quadkey"""
        quadkey = ''
        
        for i in range(z, 0, -1):
            digit = 0
            mask = 1 << (i - 1)
            
            if (x & mask) != 0:
                digit += 1
            if (y & mask) != 0:
                digit += 2
                
            quadkey += str(digit)
        
        return quadkey
    
    def do_GET(self):
        # Health check endpoint
        if self.path == '/health':
            self.send_response(200)
            self.send_header('Content-Type', 'text/plain')
            self.end_headers()
            self.wfile.write(b'OK')
            return
        
        # Parse URL path for z/x/y pattern
        match = re.match(r'^/(\d+)/(\d+)/(\d+)\.(?:jpg|jpeg|png)$', self.path)
        
        if match:
            try:
                z = int(match.group(1))
                x = int(match.group(2))
                y = int(match.group(3))
                
                # Validate zoom level
                if z < 0 or z > 23:
                    self.send_error(400, "Invalid zoom level")
                    return
                
                # Validate x and y coordinates
                max_val = 2 ** z
                if x < 0 or x >= max_val or y < 0 or y >= max_val:
                    self.send_error(400, "Invalid tile coordinates")
                    return
                
                # Convert to quadkey
                quadkey = self.zxy_to_quadkey(z, x, y)
                
                # Construct Bing Maps URL
                bing_url = f'http://ecn.t3.tiles.virtualearth.net/tiles/a{quadkey}.jpeg?g=1'
                
                # Fetch tile
                start_time = time.time()
                
                # Create request with timeout
                req = urllib.request.Request(bing_url)
                req.add_header('User-Agent', 'TileProxyServer/1.0')
                
                with urllib.request.urlopen(req, timeout=10) as response:
                    tile_data = response.read()
                
                fetch_time = time.time() - start_time
                
                # Send response
                self.send_response(200)
                self.send_header('Content-Type', 'image/jpeg')
                self.send_header('Content-Length', str(len(tile_data)))
                self.send_header('Cache-Control', 'public, max-age=86400')
                self.send_header('Access-Control-Allow-Origin', '*')
                self.send_header('X-Fetch-Time', f'{fetch_time:.3f}')
                self.end_headers()
                self.wfile.write(tile_data)
                
                logger.info(f"Served tile: z={z}, x={x}, y={y} -> quadkey={quadkey} in {fetch_time:.3f}s")
                
            except urllib.error.HTTPError as e:
                logger.error(f"HTTP error fetching tile: {e.code} - {e.reason}")
                self.send_error(e.code, f"Error fetching tile: {e.reason}")
            except urllib.error.URLError as e:
                logger.error(f"URL error fetching tile: {e.reason}")
                self.send_error(500, f"Error fetching tile: {e.reason}")
            except Exception as e:
                logger.error(f"Unexpected error: {str(e)}", exc_info=True)
                self.send_error(500, f"Internal server error")
        else:
            self.send_error(404, "Invalid tile URL format. Use: /z/x/y.jpg")
    
    def log_message(self, format, *args):
        # Use logger instead of print
        logger.debug(f"{self.address_string()} - {format % args}")

class ProductionServer:
    def __init__(self, port):
        self.port = port
        self.httpd = None
        self.running = False
        
    def signal_handler(self, signum, frame):
        logger.info(f"Received signal {signum}, shutting down gracefully...")
        self.shutdown()
        
    def shutdown(self):
        self.running = False
        if self.httpd:
            # Shutdown in a separate thread to avoid blocking
            threading.Thread(target=self.httpd.shutdown).start()
            
    def run(self):
        # Set up signal handlers
        signal.signal(signal.SIGTERM, self.signal_handler)
        signal.signal(signal.SIGINT, self.signal_handler)
        
        server_address = ('', self.port)
        # Use ThreadingHTTPServer for better concurrency
        self.httpd = ThreadingHTTPServer(server_address, TileProxyHandler)
        
        logger.info(f"Tile proxy server running on port {self.port}")
        logger.info(f"Workers: {os.environ.get('WORKERS', '4')}")
        logger.info(f"Log level: {os.environ.get('LOG_LEVEL', 'INFO')}")
        
        self.running = True
        try:
            self.httpd.serve_forever()
        except KeyboardInterrupt:
            pass
        finally:
            logger.info("Server shutdown complete")
            # Cleanup thread pool
            TileProxyHandler.executor.shutdown(wait=True)

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 8080))
    server = ProductionServer(port)
    server.run()