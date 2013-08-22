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
        return ('<p><em>File uploaded under name: {0}</em></p>'
               .format(cgi.escape(uploaded_file_name)))

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
    def get_unique_local_filename(filename):
      cwd = os.path.abspath('.')
      filename = os.path.split(filename)[1] # strip the path
      local_filename = os.path.join(cwd, filename)

      unique_filename = local_filename
      i = 1
      while os.path.exists(unique_filename):
        unique_filename = "{0}-copy{1}".format(local_filename, i)
        i += 1

      return unique_filename

    def save_file(filename, data):
      sys.stderr.write("Saving file `{0}'... ".format(filename))
      with open(filename, 'wb') as outfile:
        outfile.write(data.read())
      sys.stderr.write("[saved]\n")

    def send_response(filename):
      self.send_response(200)
      self.end_headers()
      self.write_upload_form(os.path.split(filename)[1])

    try:
      content_type, options = cgi.parse_header(self.headers['content-type'])
      if content_type == 'multipart/form-data':
        # Most of the needed environment variables will be read, instead, from
        # the 'headers' object, but as the FieldStorage object was designed for
        # CGI, absense of 'POST' value in environ will prevent the object from
        # using the 'fp' argument
        fields = cgi.FieldStorage(fp = self.rfile,
                                  headers = self.headers,
                                  environ={'REQUEST_METHOD': 'POST'})
      else:
        raise PostError("Content is not `multipart/form-data'. "+
                        "Got `{0}' instead".format(content_type))

      upload_field = fields[self.file_field_name]
      local_filename = get_unique_local_filename(upload_field.filename)
      save_file(local_filename, upload_field.file)
      send_response(local_filename)

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
