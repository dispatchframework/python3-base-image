import json
import traceback
import signal
import sys
import io

import falcon
import waitress

from function import handler


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
    stacktrace = None

    stderr = io.StringIO()
    old_stderr = sys.stderr

    stdout = io.StringIO()
    old_stdout = sys.stdout

    try:
        sys.stderr = stderr
        sys.stdout = stdout
        r = handle(msg['context'], msg['payload'])
    except Exception as e:
        err = e
        stacktrace = traceback.format_exc().rstrip()
        print(stacktrace, file=sys.stderr)
    finally:
        sys.stderr = old_stderr
        stderr.flush()

        sys.stdout = old_stdout
        stdout.flush()

        # Exception is not json-serializable, so have to serialize ourselves
        if err is not None:
            err = {'message': str(err), 'stacktrace': stacktrace, 'type': err.__class__.__name__}

    return json.dumps({'context': {'error': err, 'logs': {'stdout': read_logs(stdout), 'stderr': read_logs(stderr)}}, 'payload': r}, ensure_ascii=False)


def exec_function(req, res):
    msg = get_msg(req)
    res.body = process_msg(msg, handler.handle)


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
