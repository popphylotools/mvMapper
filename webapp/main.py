from jinja2 import Environment, FileSystemLoader

from tornado.ioloop import IOLoop
from tornado.web import RequestHandler, StaticFileHandler

from bokeh.application import Application as bkApplication
from bokeh.application.handlers import FunctionHandler as bkFunctionHandler
from bokeh.embed import autoload_server as bk_autoload_server
from bokeh.server.server import Server as bkServer

# noinspection PyUnresolvedReferences
from app import modify_doc

import uuid
import tornado
import json

import sys

import markdown2

env = Environment(loader=FileSystemLoader('templates'))

appAddress = [element.strip() for element in sys.argv[1].split(',')]
appPort = int(sys.argv[2])


class IndexHandler(RequestHandler):
    def get(self):
        template = env.get_template('embed.html')
        script = bk_autoload_server(model=None, url='/bkapp')

        arguments = {}
        userConfig = self.get_argument("c", default="None")
        if userConfig is not "None":
            arguments["c"] = userConfig
        userData = self.get_argument("d", default="None")
        if userData is not "None":
            arguments["d"] = userData

        script_list = script.split("\n")
        script_list[2] = script_list[2][:-1]
        for key in arguments.keys():
            script_list[2] += "&{}={}".format(key, arguments[key])
        script_list[2] += '"'
        script = "\n".join(script_list)

        self.write(template.render(script=script, template="Tornado"))


class POSTHandler(tornado.web.RequestHandler):
    def post(self):
        accepted_type = {"application/csv", "application/x-csv", "text/csv", "text/comma-separated-values",
                         "text/x-comma-separated-values", "text/tab-separated-values", "text/plain",
                         "text/x-csv", "application/vnd.ms-excel"}
        response_to_send = {"success": False}
        for field_name, files in self.request.files.items():
            for info in files:
                filename, content_type = info.get("qqfilename") or info['filename'], info['content_type']
                body = info['body']

                new_filename = str(uuid.uuid4().hex)
                response_to_send["newUuid"] = new_filename

                print(content_type)
                if content_type in accepted_type:
                    try:
                        outfile = open("data/" + new_filename, 'wb')
                        outfile.write(body)
                    except Exception as e:
                        response_to_send["success"] = False
                        response_to_send["error"] = "Oops, that wasn't supposed to happen. This is bad."
                        print(str(e))
                    else:
                        response_to_send["success"] = True
                        response_to_send["linkArguments"] = "?d={}".format(new_filename)
                    finally:
                        outfile.close()
                else:
                    response_to_send["success"] = False
                    response_to_send["error"] = "content_type {} not in accepted_type {}".format(content_type, accepted_type)

        print(json.dumps(response_to_send))
        self.write(json.dumps(response_to_send))

class helpHandler(tornado.web.RequestHandler):
    def get(self):
        template = env.get_template('help.html')
        rendered = template.render(fragment=markdown2.markdown_path("helpPage.md",
                                                                    extras=['fenced-code-blocks',
                                                                            'code-friendly',
                                                                            'target-blank-links',
                                                                            'toc',
                                                                            'tables']))
        self.write(rendered)

class uploadPageHandler(tornado.web.RequestHandler):
    def get(self):
        self.write(env.get_template('upload.html').render())

bokeh_app = bkApplication(bkFunctionHandler(modify_doc))

io_loop = IOLoop.current()
server = bkServer({'/bkapp': bokeh_app}, io_loop=io_loop, host=appAddress, port=appPort,
                  extra_patterns=[('/', IndexHandler),
                                  (r'/help', helpHandler),
                                  (r'/upload', uploadPageHandler),
                                  (r'/server/upload', POSTHandler),
                                  (r'/stat/(.*)', StaticFileHandler, {'path': "stat"})
                                  ])
server.start()

if __name__ == '__main__':
    io_loop.start()
