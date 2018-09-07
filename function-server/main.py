import importlib
import io
import json
import os
import signal
import sys
import traceback
from concurrent.futures import ThreadPoolExecutor
from concurrent.futures import TimeoutError

import falcon
import waitress

INPUT_ERROR = 'InputError'
FUNCTION_ERROR = 'FunctionError'
SYSTEM_ERROR = 'SystemError'


class Health:
    @staticmethod
    def on_get(req, res):
        res.body = '{}'


def read_logs(text_io):
    text_io.seek(0)
    return [line.rstrip('\n') for line in text_io]


def get_msg(req):
    msg = None
    if req.content_length:
        msg = json.load(req.stream)
    return msg


def process_req(req, res, handle):
    r = None
    response = None

    try:
        msg = get_msg(req)
    except ValueError as e:
        res.status = falcon.HTTP_500
        return json.dumps({'type':SYSTEM_ERROR, 'stacktrace':traceback.format_exc().splitlines(), 'message' : str(e)}, ensure_ascii=False)

    try:
        r = handle(msg['context'], msg['payload'])
    except (ValueError, TypeError) as e:
        res.status = falcon.HTTP_400
        return json.dumps({'type':INPUT_ERROR, 'stacktrace':traceback.format_exc().splitlines(), 'message' : str(e)}, ensure_ascii=False)
    except Exception as e:
        res.status = falcon.HTTP_500
        return json.dumps({'type':FUNCTION_ERROR, 'stacktrace':traceback.format_exc().splitlines(), 'message' : str(e)}, ensure_ascii=False)

    try:
        response = json.dumps(r, ensure_ascii=False)
    except TypeError as e:
        # Non-json serializable payload
        res.status = falcon.HTTP_422
        return json.dumps({'type':FUNCTION_ERROR, 'stacktrace':traceback.format_exc().splitlines(), 'message' : str(e)}, ensure_ascii=False)
    except Exception as e:
        res.status = falcon.HTTP_502
        return json.dumps({'type':SYSTEM_ERROR, 'stacktrace':traceback.format_exc().splitlines(), 'message' : str(e)}, ensure_ascii=False)

    return response

def module_and_name(s):
    return s.rsplit('.', 1)


def import_function(wd, func_fqn):
    sys.path.insert(0, wd)

    [mod_name, func_name] = module_and_name(func_fqn)
    module = importlib.import_module(mod_name)

    return getattr(module, func_name)


def exec_function(f):
    def handler(req, res):
        res.body = process_req(req, res, f)
        sys.stdout.flush()
        sys.stderr.flush()

    return handler


def signal_handler(signum, frame):
    sys.exit(0)


def main():
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)

    f = import_function(os.getcwd(), sys.argv[1])

    app = falcon.API()
    app.add_route('/healthz', Health())
    app.add_sink(exec_function(f), '/')

    waitress.serve(app, threads=1, port=os.environ.get('PORT'))


if __name__ == "__main__":
    main()
