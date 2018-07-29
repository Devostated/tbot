import logging, json
from tornado import web, escape

class Base_handler(web.RequestHandler):

    @property
    def db(self):
        return self.application.db

    def get_current_user(self):
        data = self.get_secure_cookie('data', max_age_days=0.14)
        if not data:
            return
        return json.loads(escape.native_str(data))