from http.server import BaseHTTPRequestHandler, HTTPServer
import json

class HealthCheckHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path == '/health':
            self.send_response(200)
            self.send_header('Content-Type', 'application/json')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            health_data = {"status": "ok", "message": "MegaTTS3 service is running"}
            self.wfile.write(json.dumps(health_data).encode())
        else:
            self.send_response(404)
            self.send_header('Content-Type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps({"detail": "Not Found"}).encode())

def run_server():
    server_address = ('', 7929)
    httpd = HTTPServer(server_address, HealthCheckHandler)
    print('Health check server started on port 7929')
    httpd.serve_forever()

if __name__ == '__main__':
    run_server()