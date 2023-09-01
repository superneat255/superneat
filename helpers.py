import os
import errno
import signal
from functools import wraps


class TimeoutError(Exception):
    pass


def timeout(seconds=10, error_message=os.strerror(errno.ETIME)):
    def decorator(func):
        def _handle_timeout(signum, frame):
            raise TimeoutError(error_message)

        def wrapper(*args, **kwargs):
            signal.signal(signal.SIGALRM, _handle_timeout)
            signal.alarm(seconds)
            try:
                result = func(*args, **kwargs)
            finally:
                signal.alarm(0)
            return result

        return wraps(func)(wrapper)

    return decorator



def runSh(args, *, output=False, shell=False, cd=None):
    import subprocess, shlex

    if not shell:
        if output:
            proc = subprocess.Popen(
                shlex.split(args), stdout=subprocess.PIPE, stderr=subprocess.STDOUT, cwd=cd
            )
            while True:
                output = proc.stdout.readline()
                if output == b"" and proc.poll() is not None:
                    return
                if output:
                    print(output.decode("utf-8").strip())
        return subprocess.run(shlex.split(args), cwd=cd).returncode
    else:
        if output:
            return (
                subprocess.run(
                    args,
                    shell=True,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.STDOUT,
                    cwd=cd,
                )
                .stdout.decode("utf-8")
                .strip()
            )
        return subprocess.run(args, shell=True, cwd=cd).returncode


def b64_encode(s):
    from base64 import b64encode
    return b64encode(s.encode('utf-8')).decode('utf-8')


def b64_decode(s):
    from base64 import b64decode
    return b64decode(s).decode('utf-8')


def binary_encode(s): return str(''.join(format(ord(i), '08b') for i in s))


def binary_decode(b):
    chunks = [b[i:i+8] for i in range(0, len(b), 8)]
    integers = [int(chunk, 2) for chunk in chunks]
    return str(''.join(chr(i) for i in integers))


def build_query(payload, quote_via='quote_plus'):
    from urllib.parse import urlencode, quote_plus, quote
    return urlencode(payload, quote_via=locals()[quote_via])


def build_query_v2(payload):
    query = ''
    for k,v in payload.items(): query += f'{k}={v}&'
    return query[:-1]
