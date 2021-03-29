import argparse
import logging
import sys

from openfisca_core.scripts import add_tax_benefit_system_arguments

"""Launch the HTTP & WebSocket server."""


HOST = '127.0.0.1'
PORT = '5000'


log = logging.getLogger(__name__)


def get_parser():
    parser = argparse.ArgumentParser()

    # Define OpenFisca modules configuration.
    parser = add_tax_benefit_system_arguments(parser)

    # Define server configuration.
    parser.add_argument('-p', '--port', action='store', help="port to serve on (use --bind to specify host and port)", type=int)
    parser.add_argument('-f', '--configuration-file', action='store', help="configuration file", type=str)

    return parser


def read_user_configuration(default_configuration, command_line_parser):
    configuration = default_configuration
    args, unknown_args = command_line_parser.parse_known_args()

    if args.configuration_file:
        file_configuration = {}
        with open(args.configuration_file, "r") as file:
            exec(file.read(), {}, file_configuration)

        # Configuration file overrides default configuration.
        update(configuration, file_configuration)

    # Command line configuration overrides all configuration options.
    configuration = update(configuration, vars(args))
    if configuration.get('args'):
        command_line_parser.print_help()
        log.error('Unexpected positional argument {}'.format(configuration['args']))
        sys.exit(1)

    return configuration


def update(configuration, new_options):
    for key, value in new_options.items():
        if value is not None:
            configuration[key] = value
            if key == "port":
                configuration['bind'] = configuration['bind'][:-4] + str(configuration['port'])
    return configuration


def main():
    parser = get_parser()
    args, _ = parser.parse_known_args()

    configuration = {
        'bind': '{}:{}'.format(HOST, PORT),
        'port': PORT,
        }
    configuration = read_user_configuration(configuration, parser)

    # from openfisca_web_api.scripts.serve import main
    # return sys.exit(main(parser))
    print("ok")


if __name__ == '__main__':
    sys.exit(main())
