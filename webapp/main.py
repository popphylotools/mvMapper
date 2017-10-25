import argparse
import io
import json
import logging
import os
import uuid

import markdown2
import pandas
import pytoml
import tornado
# noinspection PyUnresolvedReferences
from app import modify_doc
from bokeh.application import Application as bkApplication
from bokeh.application.handlers import FunctionHandler as bkFunctionHandler
from bokeh.embed import autoload_server as bk_autoload_server
from bokeh.server.server import Server as bkServer
from jinja2 import Environment, FileSystemLoader
from tornado.ioloop import IOLoop
from tornado.web import RequestHandler, StaticFileHandler


# logging configuration
class OneLineExceptionFormatter(logging.Formatter):
    def formatException(self, exc_info):
        result = super().formatException(exc_info)
        return repr(result)

    def format(self, record):
        result = super().format(record)
        if record.exc_text:
            result = result.replace(r"\n", "")
        return result


handler = logging.StreamHandler()
formatter = OneLineExceptionFormatter(logging.BASIC_FORMAT)
handler.setFormatter(formatter)
root = logging.getLogger()
root.setLevel(os.environ.get("LOGLEVEL", "INFO"))
root.addHandler(handler)

log = logging.getLogger("mvMapper")

env = Environment(loader=FileSystemLoader('templates'))


class IndexHandler(RequestHandler):
    def get(self):

        # validate and foreword parameters
        try:
            parameters = {}

            # validate config parameter
            userConfig = self.get_argument("c", default="None")
            if userConfig != "None":
                # check that file name is valid
                cleanName = "".join(c for c in userConfig if c.isalnum() or (c in ".-_"))  # insure filename is safe
                if cleanName != userConfig:
                    # emit error, load error page: invalid character(s) in config parameter
                    message = "Invalid character(s) in config parameter: {}".format(userConfig)
                    log.info(message)
                    raise ValueError(message)
                # check that file exists
                elif not os.path.isfile("config/" + userConfig):
                    # emit error, load error page: no such config file found
                    message = "No such config file found: {}".format(userConfig)
                    log.info(message)
                    raise FileNotFoundError(message)
                # valid name and file exists, therefore pass argument
                else:
                    parameters["c"] = userConfig

            # validate data parameter
            userData = self.get_argument("d", default="None")
            if userData != "None":
                # check that file name is valid
                cleanName = "".join(c for c in userData if c.isalnum() or (c in ".-_"))  # insure filename is safe
                if cleanName != userData:
                    # emit error, load error page: invalid character(s) in data parameter
                    message = "Invalid character(s) in data parameter: {}".format(userData)
                    log.info(message)
                    raise ValueError(message)
                # check that file exists
                elif not os.path.isfile("data/" + userData):
                    # emit error, load error page: no such data file found
                    message = "No such data file found: {}".format(userData)
                    log.info(message)
                    raise FileNotFoundError(message)
                # valid name and file exists, therefore pass argument
                else:
                    parameters["d"] = userData

            # special case where user config is given without valid defaultDataPath and userData isn't passed to URL
            if userConfig != "None" and userData == "None":
                # load config file
                with open("config/" + userConfig) as toml_data:
                    config = pytoml.load(toml_data)
                if "defaultDataPath" in config:
                    dataPath = config.get("defaultDataPath")
                else:
                    raise ValueError(
                        'Config file "{}" has no "defaultDataPath" parameter, and no "d=" parameter was passed in the URL.'.format(
                            userConfig))
                if not os.path.isfile(dataPath):
                    raise FileNotFoundError(
                        'No such data file exists: "defaultDataPath" parameter "{}" passed in config file "{}".'.format(
                            dataPath, userConfig))

        except ValueError as e:
            template = env.get_template('error.html')
            self.write(template.render(message=e))

        except FileNotFoundError as e:
            template = env.get_template('error.html')
            self.write(template.render(message=e))

        else:
            # load template and script
            template = env.get_template('embed.html')
            script = bk_autoload_server(model=None, url='/bkapp')

            # insert parameters into script
            script_list = script.split("\n")
            script_list[2] = script_list[2][:-1]
            for key in parameters.keys():
                script_list[2] += "&{}={}".format(key, parameters[key])
            script_list[2] += '"'
            script = "\n".join(script_list)

            # return bokeh app
            self.write(template.render(script=script))


class POSTHandler(tornado.web.RequestHandler):
    def post(self):
        response_to_send = {"success": False}
        for field_name, files in self.request.files.items():
            for file_data in files:
                filename, content_type = file_data.get("qqfilename") or file_data.get('filename'), file_data.get(
                    'content_type')
                body = file_data['body']

                new_filename = str(uuid.uuid4().hex)
                response_to_send["newUuid"] = new_filename

                # validation
                # check if .csv extension
                if ".csv" not in filename:
                    response_to_send["success"] = False
                    response_to_send["error"] = 'Only .csv extension allowed.'
                else:
                    # check if parses with pandas
                    try:
                        df = pandas.read_csv(io.BytesIO(body))
                    except Exception as e:
                        response_to_send["success"] = False
                        response_to_send["error"] = "Failed to parse uploaded data."
                        log.error(str(e))
                    else:  # if correctly parsed, continue with additional tests
                        columns = set(df.columns)
                        max_lon = df['lon'].max()
                        min_lon = df['lon'].min()
                        max_lat = df['lat'].max()
                        min_lat = df['lat'].min()
                        # check if has needed columns
                        if not {"key", "lat", "lon"}.issubset(columns):
                            response_to_send["success"] = False
                            response_to_send["error"] = 'Ensure that "key", "lat", and "lon" columns exist.'
                        # check if lat/lon in range
                        elif not (     (-180 <= max_lon <= 180)
                                  and  (-180 <= min_lon <= 180)
                                  and  (-90  <= max_lat <= 90)
                                  and  (-90  <= min_lat <= 90)):
                            response_to_send["success"] = False
                            response_to_send["error"] = ('Ensure that "lat" in range -90 to 90, '
                                                             'and "lon" in range -180 to 180.')
                        # passed all tests
                        else:
                            df.to_csv("data/" + new_filename, header=True, index=False)
                            response_to_send["success"] = True

        log.info(json.dumps(response_to_send))
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


def main():
    parser = argparse.ArgumentParser(description='Run mvMapper server.')
    parser.add_argument('--host', type=str, nargs='+', required=True)
    parser.add_argument('--port', type=int, required=True)
    args = parser.parse_args()

    bokeh_app = bkApplication(bkFunctionHandler(modify_doc))

    io_loop = IOLoop.current()
    server = bkServer({'/bkapp': bokeh_app}, io_loop=io_loop, host=args.host, port=args.port,
                      extra_patterns=[('/', IndexHandler),
                                      (r'/help', helpHandler),
                                      (r'/upload', uploadPageHandler),
                                      (r'/server/upload', POSTHandler),
                                      (r'/stat/(.*)', StaticFileHandler, {'path': "stat"}),
                                      (r'/(favicon.ico)', StaticFileHandler, {"path": ""})
                                      ])
    server.start()

    if __name__ == '__main__':
        io_loop.start()


try:
    exit(main())
except Exception as e:
    log.exception("Exception in main(): {}".format(e))
    exit(1)
