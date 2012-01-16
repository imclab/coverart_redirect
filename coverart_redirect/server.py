# Copyright (C) 2011 Lukas Lalinsky
# Copyright (C) 2011 MetaBrainz Foundation
# Distributed under the MIT license, see the LICENSE file for details.

import sys
import traceback
import cherrypy
import sqlalchemy
from cgi import parse_qs
from contextlib import closing
from coverart_redirect.config import Config
from coverart_redirect.utils import LocalSysLogHandler
from coverart_redirect.request import CoverArtRedirect

class Server(object):

    def __init__(self, config_path, static_path):
        self.config = Config(config_path)
        self.config.static_path = static_path
        self.engine = sqlalchemy.create_engine(self.config.database.create_url())

    def __call__(self, environ, start_response):
        try:
            with closing(self.engine.connect()) as conn:
                conn.execute("SET search_path TO musicbrainz")
                status, txt = CoverArtRedirect(self.config, conn).handle(environ)
            if status.startswith("307"):
                start_response(status, [('Location', txt)])
                return ""
            elif status.startswith("200"):
                start_response('200 OK', [
                ('Content-Type', 'text/html; charset=UTF-8'),
                ('Content-Length', str(len(txt)))])
                return txt
            else:
                start_response(status, [])
                return ""
        except:
            cherrypy.log("Caught exception\n" + traceback.format_exc())
            start_response("500 internal server error", [])
            return "Whoops. Our bad.\n"

def make_application(config_path, static_path):
    app = Server(config_path, static_path)
    return app

