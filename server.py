#!/usr/bin/python2

# Copyright Jon Berg , turtlemeat.com
# Modified by nikomu @ code.google.com
# Modified by Carlos V. <cookyt2@gmail.com>

import cgi
import HTMLParser
import os
import sys

from BaseHTTPServer import BaseHTTPRequestHandler, HTTPServer

class PostError(Exception):
  pass

class GetError(Exception):
  pass

class UploadHandler(BaseHTTPRequestHandler):
  def __init__(self, *args, **kwargs):
    self.file_field_name = 'upfile'
    BaseHTTPRequestHandler.__init__(self, *args, **kwargs)

  def write_upload_form(self, uploaded_file_name=None):
    def uploaded_message():
      if uploaded_file_name == None:
        return ''
      else:
        html_parser = HTMLParser.HTMLParser()
        html_safe_filename = html_parser.unescape(uploaded_file_name)
        return ('<p><em>File uploaded under name: {0}</em></p>'
               .format(html_safe_filename))

    form = """
      <html>
        <body>
          <h1>Upload a file</h1>
          {0}
          <form method='post' enctype='multipart/form-data' action='/'>
            <p><input type="file" name="{1}" /></p>
            <p><input type="submit" value="Upload" /></p>
          </form>
        </body>
      </html>
    """.format(uploaded_message(), self.file_field_name)
    self.wfile.write(form)

  def send_html_response_ok(self):
    self.send_response(200)
    self.send_header('Content-type', 'text/html')
    self.end_headers()

  def do_GET(self):
    try:
      if self.path == '/' :
        self.send_html_response_ok()
        self.write_upload_form()
      else:
        raise GetError('Requested non-root path: {0}'.format(self.path))
    except Exception as e :
      sys.stderr.write(str(e) + '\n')
      self.send_error(404, 'File Not Found: {0}'.format(self.path))

  def do_POST(self):
    try:
      content_type, options = cgi.parse_header(self.headers['content-type'])
      if content_type == 'multipart/form-data':
        # Most of the needed environment variables will be read, instead, from
        # the 'headers' object, but as the FieldStorage object was designed for
        # CGI, absense of 'POST' value in environ will prevent the object from
        # using the 'fp' argument
        fs = cgi.FieldStorage(fp = self.rfile,
                              headers = self.headers,
                              environ={'REQUEST_METHOD': 'POST'})
      else:
        raise PostError("Content is not `multipart/form-data'. "+
                        "Got `{0}' instead".format(content_type))

      def get_unique_filename(filename):
        filename_unique = filename
        i = 1
        while os.path.exists(filename_unique):
          filename_unique = "{0}-copy{1}".format(filename, i)
          i += 1
        return filename_unique

      cwd = os.path.abspath('.')
      fs_up = fs[self.file_field_name]
      filename = os.path.split(fs_up.filename)[1] # strip the path
      fullname = get_unique_filename(os.path.join(cwd, filename))

      sys.stderr.write("Saving file `{0}'... ".format(fullname))
      with open(fullname, 'wb') as outfile:
        outfile.write(fs_up.file.read())
      sys.stderr.write("[saved]\n")

      self.send_response(200)
      self.end_headers()
      self.write_upload_form(os.path.split(fullname)[1])

    except Exception as e:
      sys.stderr.write(str(e) + '\n')
      self.send_error(404, 'Failed post request; path: {0}'.format(self.path))

def main():
  kDefaultPort= 8000
  port_number = int(sys.argv[1]) if len(sys.argv) > 1 else kDefaultPort
  server = None
  try:
    server = HTTPServer(('', port_number), UploadHandler)
    sys.stderr.write('starting HTTP file upload server on port {0}...\n'
                     .format(port_number))
    server.serve_forever()
  except KeyboardInterrupt:
    sys.stderr.write('shutting down server.\n')

if __name__ == '__main__':
  main()
