import argparse

import config as conf
config = conf.load()

# TODO move to click instead.


def parser():
    """ Command Line Args """

    # Bottom Menu
    leaf = argparse.ArgumentParser(add_help=False)

    leaf.add_argument(
        '-p', '--payload',
        help='Payload to to be injected into file.'
    )

    leaf.add_argument(
        '--debug',
        action='store_true'
    )

    userprovided = leaf.add_argument_group(title='User provided file options')
    userprovided.add_argument(
        '-f', '--file',
        help='Provide a local file.'
    )

    userprovided.add_argument(
        '-u', '--url',
        help='Provide a url to a file.'
    )

    websearch = leaf.add_argument_group(title='Web search options')
    websearch.add_argument(
        '-q', '--query',
        help='Provide a search query.'
    )

    websearch.add_argument(
        '-s', '--searchmode',
        nargs='?',
        choices=config['searchmode'],
        help='Select a searchmode.'
    )


    # Outputs menu
    outputmenu = argparse.ArgumentParser(add_help=False)
    output = outputmenu.add_argument_group(title='Output options')
    
    output.add_argument(
        '-o', '--output',
        help='Provide output path.'
    )

    output.add_argument(
        '--json',
        action='store_true',
        help='Pass result as json object.'
    )


    # Submenu
    submenu = argparse.ArgumentParser(add_help=False)

    typemenu = submenu.add_subparsers(
        dest='type'
    )

    image = typemenu.add_parser(
        'image',
        parents=[leaf, outputmenu],
        help='Use image procedures.'
    )

    image.add_argument(
        'image injection',
        const='comment',
        nargs='?',
        choices=config['injection']['image'],
        help='Select an injection method.'
    )

    pdf = typemenu.add_parser(
        'pdf',
        parents=[leaf, outputmenu],
        help='Use pdf injection procedures.'
    )

    rtf = typemenu.add_parser(
        'rtf',
        parents=[leaf, outputmenu],
        help='Use pdf inject procedures.'
    )


    # Main menu
    menu = argparse.ArgumentParser(
        description='Welcome to Dr. Luigi\'s malware clinic.'
    )

    mainmenu = menu.add_subparsers(
        dest='operation'
    )

    mainmenu.add_parser(
        'inject',
        parents=[submenu],
        help='Use injection options.'
    )

    mainmenu.add_parser(
        'analyse',
        parents=[submenu],
        help='Use analysis options.'
    )

    menu.set_defaults(usage=lambda n: menu.print_usage())
    menu.set_defaults(help=lambda n: menu.print_help())

    args = menu.parse_args()

    # Custom Error handling.
    
    # Currently you cannot nest objects in mutually exclusive groups.
    userprovided_opts = args.url or args.file 
    websearch_opts = args.query or args.searchmode 
    

    # There may be a way to remove a positional argument from the help menu.'
    positional_args = args._get_kwargs()[-1][-1]
    if args.operation == 'analyse'and positional_args:
        menu.error('Analyse option is not compatible with injection options.')
        
    if userprovided_opts and websearch_opts:
        menu.error('User provided options are incompatible with web search options.')
    else:
        return args
