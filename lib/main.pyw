"""Main entry-point for Lib

Usage:
    From a command shell

    $ main.pyw path=/my/path
    $ main.pyw path=/my/path --port=5555

"""


if __name__ == '__main__':
    import logging
    log = logging.getLogger('lib')

    formatter = logging.Formatter(
        '%(asctime)s - '
        '%(levelname)s - '
        '%(name)s - '
        '%(message)s',
        '%H:%M:%S')

    stream_handler = logging.StreamHandler()
    stream_handler.setFormatter(formatter)
    log.addHandler(stream_handler)
    log.setLevel(logging.DEBUG)

    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument('path')
    parser.add_argument('--port', default=None)
    parser.add_argument('--support', default=list(), nargs='*')

    args = parser.parse_args()

    from lib import presentation
    presentation.main(path=args.path,
                      port=args.port,
                      support=args.support)
