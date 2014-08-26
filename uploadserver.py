#!/usr/bin/python2
#
# The MIT License (MIT)
#
# Copyright (c) 2014 Carlos Valera
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in
# all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
# THE SOFTWARE.
#
#
# Single-file HTTP server for uploading files. Meant to be a quick and dirty
# solution to transfering files on a local network. Uses just the python2.7
# stdlib.
#
# OUTSTANDING ISSUES
# ==================
# + Interfaces w/ OS don't catch errors, so, for example, if this fails to save
#   a file, it'll kill the application.
# + Should add a flag to denote which directory to save files in, rather than
#   just using the CWD.
# + Free-standing functions should be folded into private methods of UploaderApp

import HTMLParser
import argparse
import cgi
import httplib
import logging
import os

from wsgiref.simple_server import make_server


FILE_FIELD_NAME = 'upfile'

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
  '''.format(uploaded_file_message, FILE_FIELD_NAME)


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
  ''' Simple WSGI CGI app which controls the upload process. '''

  def __call__(self, environ, response):
    if environ['PATH_INFO'] != '/':
      error_message = 'Not found: %s' % (environ['PATH_INFO'],)
      return SendErrorPage(response, httplib.NOT_FOUND, error_message)

    handlers = {
      'GET': self.GET,
      'POST': self.POST,
    }
    handler = handlers.get(environ['REQUEST_METHOD'], self.DefaultHandler)
    return handler(environ, response)

  def DefaultHandler(self, environ, response):
    error_message = 'Method not allowed: %s' % (environ['REQUEST_METHOD'],)
    return SendErrorPage(response, httplib.METHOD_NOT_ALLOWED, error_message)

  def POST(self, environ, response):
    field_storage = cgi.FieldStorage(fp=environ['wsgi.input'], environ=environ)
    if FILE_FIELD_NAME not in field_storage:
      return SendErrorPage(response, httplib.PRECONDITION_FAILED,
                           'No file data recieved.')
    upload_field = field_storage[FILE_FIELD_NAME]
    filename = UniqueLocalFilename(upload_field.filename)
    SaveFile(filename, upload_field.file)
    return SendUploadForm(response, filename)

  def GET(self, environ, response):
    return SendUploadForm(response)


def ParseArguments():
  ''' Uses argparse to parse command line arguments and flags in sys.argv for
  the cmd-line interface to uploadserver.
  Returns an argparse namespace with the parsed arguments.
  '''
  parser = argparse.ArgumentParser(
      description=('A simple HTTP server which allows files to be uploaded '
                   'to the directory the server was started in.'),
  )
  parser.add_argument('-h', '--host',
      help=('The host to listen on. Defaults to "0.0.0.0" to listen on all '
            'hosts. This allows anyone on the same network to reach '
            'the server.'),
      default='0.0.0.0',
  )
  parser.add_argument('-p', '--port',
      help='The port number to start the server on. Default is 8000.',
      type=int,
      default=8000,
  )
  return parser.parse_args()


def main():
  logging.basicConfig(level=logging.INFO)
  args = ParseArguments()
  logging.info('Starting HTTP file upload server on host %r and port %d',
               args.host, args.port)
  httpd = make_server(args.host, args.port, UploaderApp())
  httpd.serve_forever()


if __name__ == '__main__':
  main()
