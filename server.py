#!/usr/bin/python2

# Copyright Jon Berg , turtlemeat.com
# Modified by nikomu @ code.google.com
# Modified by Carlos V. <cookyt2@gmail.com>

import cgi
import HTMLParser
import os
import sys

log = sys.stderr.write

from BaseHTTPServer import BaseHTTPRequestHandler, HTTPServer

CWD = os.path.abspath('.')

kPortNumber = 8000
kFileFieldName = "upfile"
kUploadForm = """
<form method='post' enctype='multipart/form-data' action='/'>
  <p><input type="file" name="{0}" /></p>
  <p><input type="submit" value="Upload" /></p>
</form>
""".format(kFileFieldName)

def get_unique_filename(fullname):
  if os.path.exists(fullname):
    fullname_test = fullname + '.copy'
    i = 0
    while os.path.exists( fullname_test ):
      fullname_test = "%s.copy(%d)" % (fullname, i)
      i += 1
    fullname = fullname_test
  return fullname

class PostError(Exception):
  pass

class GetError(Exception):
  pass

class UploadHandler(BaseHTTPRequestHandler):
  def write_html_header(self):
    self.wfile.write('<html><body>')
    self.wfile.write('<h1>Upload a file</h1>')

  def write_html_footer(self):
    self.wfile.write('</body></html>')

  def write_upload_form(self):
    self.wfile.write(kUploadForm)

  def do_GET(self):
    try:
      if self.path == '/' :
        self.send_response(200)
        self.send_header('Content-type', 'text/html')
        self.end_headers()

        self.write_html_header()
        self.write_upload_form()
        self.write_html_footer()
      else:
        raise GetError
    except Exception as e :
      print e
      self.send_error(404, 'File Not Found: %s' % self.path)

  def do_POST(self):
    try:
      ctype, pdict = cgi.parse_header(self.headers['content-type'])
      if ctype == 'multipart/form-data':
        # Most of the needed environment variables will be read, instead, from
        # the 'headers' object, but as the FieldStorage object was designed for
        # CGI, absense of 'POST' value in environ will prevent the object from
        # using the 'fp' argument
        fs = cgi.FieldStorage(fp = self.rfile,
                              headers = self.headers,
                              environ={'REQUEST_METHOD': 'POST'})
      else:
        raise PostError

      fs_up = fs[kFileFieldName]
      filename = os.path.split(fs_up.filename)[1] # strip the path
      fullname = get_unique_filename(os.path.join(CWD, filename))

      log("Saving file `{0}' ".format(fullname))
      with open(fullname, 'wb') as outfile:
        outfile.write(fs_up.file.read())
      log(" [saved]\n")

      self.send_response(200)
      self.end_headers()

      html_parser = HTMLParser.HTMLParser()
      html_safe_filename = html_parser.unescape(os.path.split(fullname)[1])

      self.write_html_header();
      self.wfile.write(
          '<p><em>File uploaded under name: {0}</em></p>'.format(
          html_safe_filename))
      self.write_upload_form()
      self.write_html_footer();

    except Exception as e:
      print e
      self.send_error(404, 'Failed post request; path: %s' % (self.path))

def main():
  port_number = int(sys.argv[1]) if len(sys.argv) > 1 else kPortNumber
  server = None
  try:
    server = HTTPServer(('', port_number), UploadHandler)
    print 'starting HTTP file upload server on port %d...' % port_number
    server.serve_forever()
  except KeyboardInterrupt:
    print 'shutting down server.'

if __name__ == '__main__':
  main()
