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
HEALTHY = True


class Health:
    @staticmethod
    def on_get(req, res):
        if not HEALTHY:
            res.status = falcon.HTTP_500
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
    response = None
    err = None
    stacktrace = []

    stderr = io.StringIO()
    old_stderr = sys.stderr

    stdout = io.StringIO()
    old_stdout = sys.stdout

    try:
        sys.stderr = stderr
        sys.stdout = stdout
        with ThreadPoolExecutor(max_workers=1) as executor:
            future = executor.submit(handle, msg['context'], msg['payload'])
            timeout = msg['context'].get('timeout', None)
            r = future.result(None if timeout == None or timeout == 0 else timeout / 1000)
    except (ValueError, TypeError) as e:
        stacktrace = traceback.format_exc().splitlines()
        err = {'type': INPUT_ERROR, 'message': str(e), 'stacktrace': stacktrace}
    except TimeoutError as e:
        stacktrace = traceback.format_exc().splitlines()
        err = {'type': SYSTEM_ERROR, 'message': str(e), 'stacktrace': stacktrace}
        if not future.cancel():
            global HEALTHY
            HEALTHY = False
    except Exception as e:
        stacktrace = traceback.format_exc().splitlines()
        err = {'type': FUNCTION_ERROR, 'message': str(e), 'stacktrace': stacktrace}
    finally:
        sys.stderr = old_stderr
        stderr.flush()

        sys.stdout = old_stdout
        stdout.flush()

    context = {'error': err, 
               'logs': {'stdout': read_logs(stdout), 
                        'stderr': read_logs(stderr) + stacktrace}}

    try:
        response = json.dumps({'context': context, 'payload': r}, ensure_ascii=False)
    except TypeError as e:
        # Non-json serializable payload
        stacktrace = traceback.format_exc().splitlines()
        err = {'type': FUNCTION_ERROR, 'message': str(e), 'stacktrace': stacktrace}
        context['error'] = err
        context['logs']['stderr'].extend(stacktrace)
        response = json.dumps({'context': context, 'payload': None}, ensure_ascii=False)
    except Exception as e:
        stacktrace = traceback.format_exc().splitlines()
        err = {'type': SYSTEM_ERROR, 'message': str(e), 'stacktrace': stacktrace}
        context['error'] = err
        context['logs']['stderr'].extend(stacktrace)
        response = json.dumps({'context': context, 'payload': None}, ensure_ascii=False)

    return response


def process_req(req, f):
    try:
        msg = get_msg(req)
    except Exception as e:
        stacktrace = traceback.format_exc().splitlines()
        err = {'type': SYSTEM_ERROR, 'message': str(e), 'stacktrace': stacktrace}
        return json.dumps({'context': {'error': err,
                                       'logs': {'stdout': [],
                                                'stderr': stacktrace}},
                           'payload': None},
                          ensure_ascii=False)

    return process_msg(msg, f)

def module_and_name(s):
    return s.rsplit('.', 1)


def import_function(wd, func_fqn):
    sys.path.insert(0, wd)

    [mod_name, func_name] = module_and_name(func_fqn)
    module = importlib.import_module(mod_name)

    return getattr(module, func_name)


def exec_function(f):
    def handler(req, res):
        res.body = process_req(req, f)

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
