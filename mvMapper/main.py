from jinja2 import Environment, FileSystemLoader

from tornado.ioloop import IOLoop
from tornado.web import RequestHandler

from bokeh.application import Application
from bokeh.application.handlers import FunctionHandler
from bokeh.embed import autoload_server
from bokeh.server.server import Server

from app import modify_doc

env = Environment(loader=FileSystemLoader('templates'))


class IndexHandler(RequestHandler):
    def data_received(self, chunk):
        pass

    def get(self):
        template = env.get_template('embed.html')
        script = autoload_server(model=None, url='http://localhost:5006/bkapp')
        self.write(template.render(script=script, template="Tornado"))


bokeh_app = Application(FunctionHandler(modify_doc))

io_loop = IOLoop.current()

server = Server({'/bkapp': bokeh_app}, io_loop=io_loop, extra_patterns=[('/', IndexHandler)])
server.start()

if __name__ == '__main__':
    from bokeh.util.browser import view

    print('Opening Tornado app with embedded Bokeh application on http://localhost:5006/')

    io_loop.add_callback(view, "http://localhost:5006/")
    io_loop.start()
