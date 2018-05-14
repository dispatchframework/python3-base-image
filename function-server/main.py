import json
import traceback
import signal
import sys
import io

import falcon
import waitress

from function import handler


INPUT_ERROR = 'InputError'
FUNCTION_ERROR = 'FunctionError'
SYSTEM_ERROR = 'SystemError'


class Health(object):
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


def process_msg(msg, handle):
    r = None
    err = None
    stacktrace = []

    stderr = io.StringIO()
    old_stderr = sys.stderr

    stdout = io.StringIO()
    old_stdout = sys.stdout

    try:
        sys.stderr = stderr
        sys.stdout = stdout
        r = handle(msg['context'], msg['payload'])
    except (ValueError, TypeError) as e:
        stacktrace = traceback.format_exc().splitlines()
        err = {'type': INPUT_ERROR, 'message': str(e), 'stacktrace': stacktrace}
    except Exception as e:
        stacktrace = traceback.format_exc().splitlines()
        err = {'type': FUNCTION_ERROR, 'message': str(e), 'stacktrace': stacktrace}
    finally:
        sys.stderr = old_stderr
        stderr.flush()

        sys.stdout = old_stdout
        stdout.flush()

    return json.dumps({'context': {'error': err, 'logs': {'stdout': read_logs(stdout), 'stderr': read_logs(stderr) + stacktrace}}, 'payload': r}, ensure_ascii=False)


def process_req(req):
    try:
        msg = get_msg(req)
    except Exception as e:
        stacktrace = traceback.format_exc().splitlines()
        err = {'type': SYSTEM_ERROR, 'message': str(e), 'stacktrace': stacktrace}
        return json.dumps({'context': {'error': err, 'logs': {'stdout': [], 'stderr': stacktrace}}, 'payload': None}, ensure_ascii=False)

    return process_msg(msg, handler.handle)


def exec_function(req, res):
    res.body = process_req(req)


def signal_handler(signum, frame):
    sys.exit(0)


def main():
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)

    app = falcon.API()
    app.add_route('/healthz', Health())
    app.add_sink(exec_function, '/')

    waitress.serve(app, threads=1)


if __name__ == "__main__":
    main()
