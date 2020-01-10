#!/usr/bin/env python3
import logging
import tornado.ioloop
import web

logging.basicConfig(level='INFO')

async def redirect(request):
    return {'code': 301, 'headers': {'Location': 'https://google.com'}}

routes = [('/(.*)', {'get': redirect})]

app = web.app(routes)
server = tornado.httpserver.HTTPServer(app)
server.listen(8080)
logging.info('server started on :8080')
tornado.ioloop.IOLoop.current().start()
