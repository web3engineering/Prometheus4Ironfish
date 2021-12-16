#!/usr/bin/env python3

import http.server
import subprocess
import re
import os


EXTRACTOR = re.compile(r"Mining block \d+ on request \d+... (\d+) H/s", re.DOTALL | re.MULTILINE)
HEIGHT_EXTRACTOR = re.compile(r"^Blockchain\s+([A-Z]+).*\((\d+)\)$", re.DOTALL | re.MULTILINE)


class MyHandler(http.server.BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.end_headers()
        self.wfile.write(b"# TYPE ironfish_hashrate gauge\n")
        self.wfile.write(b"ironfish_hashrate ")
        self.wfile.write(self.get_hashrate().encode("utf-8"))
        self.wfile.write(b"\n")

        status, height = self.get_status_and_height()
        self.wfile.write(b"# TYPE ironfish_status gauge\n")
        self.wfile.write(b"ironfish_status ")
        self.wfile.write(status.encode("utf-8"))
        self.wfile.write(b"\n")

        self.wfile.write(b"# TYPE ironfish_height gauge\n")
        self.wfile.write(b"ironfish_height ")
        self.wfile.write(height.encode("utf-8"))
        self.wfile.write(b"\n")

    def get_hashrate(self):
        proc = subprocess.Popen(
            ["journalctl", "-u", "ironfish-miner", "-n", "2"],
            stdout=subprocess.PIPE
        )
        try:
            stdout, _ = proc.communicate()
            lines = stdout.decode("utf-8")
            all_matches = EXTRACTOR.findall(lines)
            if not all_matches:
                return "0"
            return all_matches[-1]
        except:
            return "0"

    def get_status_and_height(self):
        proc = subprocess.Popen(
            ["/usr/bin/yarn", "start:once", "status"],
            stdout=subprocess.PIPE,
            cwd=f"HOME/ironfish/ironfish-cli"
        )
        stdout, _ = proc.communicate()
        lines = stdout.decode("utf-8")
        status = "0"
        height = "0"
        match_obj = HEIGHT_EXTRACTOR.search(lines)
        if match_obj:
            status = "1" if match_obj.group(1) == 'SYNCED' else "0"
            height = match_obj.group(2)
        return status, height


server = http.server.HTTPServer(('', 9113), MyHandler)
server.serve_forever()
