from jinja2 import Environment, FileSystemLoader

from tornado.ioloop import IOLoop
from tornado.web import RequestHandler, StaticFileHandler

from bokeh.application import Application as bkApplication
from bokeh.application.handlers import FunctionHandler as bkFunctionHandler
from bokeh.embed import autoload_server as bk_autoload_server
from bokeh.server.server import Server as bkServer

from app import modify_doc

import uuid
import tornado
import json

env = Environment(loader=FileSystemLoader('templates'))


class IndexHandler(RequestHandler):
    def data_received(self, chunk):
        pass

    def get(self):
        template = env.get_template('embed.html')
        script = bk_autoload_server(model=None, url='/bkapp')

        arguments = {}
        id = self.get_argument("id", default="None")
        if id is not "None":
            arguments["id"] = id

        script_list = script.split("\n")
        script_list[2] = script_list[2][:-1]
        for key in arguments.keys():
            script_list[2] = script_list[2] + "&{}={}".format(key, arguments[key])
        script_list[2] = script_list[2] + '"'
        script = "\n".join(script_list)

        self.write(template.render(script=script, template="Tornado"))


class POSTHandler(tornado.web.RequestHandler):
    def post(self):
        excepted_type = ['text/csv']
        response_to_send = {"success": False}
        for field_name, files in self.request.files.items():
            for info in files:
                filename, content_type = info.get("qqfilename") or info['filename'], info['content_type']
                body = info['body']
                new_filename = str(uuid.uuid4().hex)
                response_to_send["newUuid"] = new_filename

                if content_type in excepted_type:
                    with open("data/" + new_filename, 'wb') as outfile:
                        outfile.write(body)
                        response_to_send["success"] = True
                        response_to_send["filePath"] = "?id={}".format(new_filename)


        self.write(json.dumps(response_to_send))


bokeh_app = bkApplication(bkFunctionHandler(modify_doc))

io_loop = IOLoop.current()
fineUploaderPath = "fine-uploader"
server = bkServer({'/bkapp': bokeh_app}, io_loop=io_loop, extra_patterns=[('/', IndexHandler),
                                                                          (r"/server/upload", POSTHandler),
                                                                          (r'/fine-uploader/(.*)', StaticFileHandler,
                                                                           {'path': fineUploaderPath})
                                                                          ])
server.start()

if __name__ == '__main__':

    io_loop.start()
