#!/usr/bin/python2

import HTMLParser
import cgi
import httplib
import logging
import os
import sys

from wsgiref.simple_server import make_server


kFileFieldName = 'upfile'


def SendUploadForm(response, uploaded_file_name=None):
  response('200 OK', [('Content-Type','text/html')])

  uploaded_file_message = ''
  if uploaded_file_name:
    html_parser = HTMLParser.HTMLParser()
    html_safe_filename = html_parser.unescape(uploaded_file_name)
    uploaded_file_message = ('<p><em>File uploaded under name: {0}</em></p>'
                             .format(html_safe_filename))

  return '''
    <html>
      <body>
        <h1>Upload a file</h1>
        {0}
        <form method='post' enctype='multipart/form-data' action='/'>
          <p><input type='file' name='{1}' /></p>
          <p><input type='submit' value='Upload' /></p>
        </form>
      </body>
    </html>
  '''.format(uploaded_file_message, kFileFieldName)


def SendErrorPage(response, error_code, message):
  error_message = httplib.responses[error_code]
  error_status = '%d %s' % (error_code, error_message)
  headers = [('Content-Type','text/html')]
  response(error_status, headers)
  return """
    <html>
      <body>
        <h1>{0}</h1>
        <p>{1}</p>
      </body>
    </html>
  """.format(error_status, cgi.escape(message))


def UniqueLocalFilename(filename):
  filename = os.path.split(filename)[1]  # strip the path
  local_filename = os.path.join(os.getcwd(), filename)

  new_filename = local_filename
  i = 0
  while os.path.exists(new_filename):
    new_filename = '%s-%d' % (local_filename, i)
    i += 1

  return new_filename


def SaveFile(filename, data):
  logging.info("saving file %r", filename)
  with open(filename, 'wb') as outfile:
    outfile.write(data.read())
  logging.info("saved file as %r", filename)


class UploaderApp(object):
  def __call__(self, environ, response):
    if environ['PATH_INFO'] != '/':
      error_message = 'Not found: %s' % (environ['PATH_INFO'],)
      return SendErrorPage(response, httplib.NOT_FOUND, error_message)

    method_handler = getattr(self, environ['REQUEST_METHOD'],
                             self.DefaultMethodHandler)
    method_handler(environ, response)

  def DefaultMethodHandler(self, environ, response):
    error_message = 'Method not allowed: %s' % (environ['REQUEST_METHOD'],)
    return SendErrorPage(response, httplib.METHOD_NOT_ALLOWED, error_message)

  def POST(self, environ, response):
    field_storage = cgi.FieldStorage(fp=environ['wsgi.input'], environ=environ)
    if kFileFieldName not in field_storage:
      return SendErrorPage(response, httplib.PRECONDITION_FAILED,
                           'No file data sent.')
    upload_field = field_storage[kFileFieldName]
    filename = UniqueLocalFilename(upload_field.filename)
    SaveFile(filename, upload_field.file)
    return SendUploadForm(response, filename)

  def GET(self, environ, response):
    return SendUploadForm(response)

def main():
  logging.basicConfig(level=logging.INFO)

  # TODO use argparse for arguments
  kDefaultPort= 8000
  port_number = int(sys.argv[1]) if len(sys.argv) > 1 else kDefaultPort

  httpd = make_server('', port_number, UploaderApp())
  logging.info('starting HTTP file upload server on port %d', port_number)
  httpd.serve_forever()

if __name__ == '__main__':
  main()
