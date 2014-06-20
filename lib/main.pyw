"""Main entry-point for Lib

Usage:
    From a command shell

    $ main.pyw path=/my/path
    $ main.pyw path=/my/path --port=5555

"""


if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument('path')
    parser.add_argument('--port', default=None)

    args = parser.parse_args()

    from lib import presentation
    presentation.main(path=args.path,
                      port=args.port)
