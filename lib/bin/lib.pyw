
if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument('url',
                        help=r'Root directory')
    parser.add_argument('--representation',
                        help='Representation to output')

    args = parser.parse_args()

    from lib import presentation
    presentation.main(url=args.url,
                      representation=args.representation)
