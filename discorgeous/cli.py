import click
import structlog
import sys
from multiprocessing import Process
from time import sleep

from client import Client
from server import Server

from configuration import GeneralConfiguration, ClientConfiguration, ServerConfiguration

from log import configure_logs
from repl import Repl

from pathlib import Path

import libtmux

logger = structlog.get_logger(__name__)

configure_logs(log_level="INFO")

general_configuration = GeneralConfiguration()
# client_configuration = ClientConfiguration()
#
# for k, v in client_config.items():
#     print(k)
#     print(v)
#

#
# def run_config(configurations, *, section):
#     for name, config in configurations.items():
#         logger.info("Fetching configuration... ", section=section, name=config)
#


# @cli.command()
# @click.option("--config", help="runs configuration by name", type=(str), multiple=True)
# @click.option("--message", help="message to send", default="hello", type=(str))
# def client_config(config, message):
#     client_processes = []
#     for c in config:
#         ip = client_configuration[c]["IP"]
#         port = client_configuration[c]["PORT"]
#
#         logger.info("Running client... ", ip=ip, port=port)
#         click.echo("Running client...")
#
#         client = Client(ip=ip, port=port)
#         client_processes.append(Process(target=client.send, kwargs={"message": message}))
#
#     for p in client_processes:
#         p.start()
#
#     for p in client_processes:
#         p.join()
#
def parse_config_args(config):
    CONFIG = ServerConfiguration()
    ip = CONFIG[config]["IP"]
    port = CONFIG[config]["PORT"]
    token = CONFIG[config]["VOICE_TOKEN"]
    channel = CONFIG[config]["CHANNEL_ID"]
    return ip, port, token, channel


def server_instances_from_configuration_file_in_tmux(config):
    cli_path = Path(__file__).parent
    server = libtmux.Server()
    session = server.new_session(session_name="Discorgous Servers", window_name="Master")
    for section in config:
        print("building", section)
        ip, port, token, channel = parse_config_args(section)
        window = session.new_window(section)
        pane = window.select_pane(target_pane=0)
        pane.send_keys(
            f"python3 {cli_path} server --normal --ip {ip} --port {port} --token {token} --channel {channel}"
        )
    else:
        session.attach_session()

    # sleep(5)
    # server.kill_server()


def server_instances_from_configuration_file(config):
    CONFIG = ServerConfiguration()

    server_processes = []
    for c in config:
        logger.info("Building server configuration:", section=config)
        ip, port, token, channel = parse_config_args(c)
        #
        # ip = CONFIG[c]["IP"]
        # port = CONFIG[c]["PORT"]
        # token = CONFIG[c]["VOICE_TOKEN"]
        # channel = CONFIG[c]["CHANNEL_ID"]

        server = Server(ip=ip, port=port, channel_id=channel, bot_token=token)
        server_processes.append(Process(target=server.run))

        logger.info(
            "Creating server process... ", ip=ip, port=port, channel=channel, token=token[:5]
        )
        click.echo("Creating server process...")

    for p in server_processes:
        p.start()
        logger.info(
            "Starting server process... ", ip=ip, port=port, channel=channel, token=token[:5]
        )

    for p in server_processes:
        p.join()
        logger.info(
            "Joining server process... ", ip=ip, port=port, channel=channel, token=token[:5]
        )


@click.group()
def cli():
    pass


@cli.command()
@click.option("--ip", default="127.0.0.1", help="IP address")
@click.option("--port", default="5000", help="Port")
@click.option(
    "--normal", help="runs one instance of the server. requires --channel --token", is_flag=True
)
@click.option("--config", help="runs configuration by name", type=(str), multiple=True)
@click.option("--tmux", help="runs --config in tmux", is_flag=True, default=False)
@click.option("--channel", help="runs configuration by name", type=(str), multiple=True)
@click.option("--token", help="runs configuration by name", type=(str), multiple=True)
def server(ip, port, channel, token, normal, config, tmux):
    if normal:
        validate_normal = {"channel": channel, "token": token}
        for key, arg in validate_normal.items():
            assert (
                len(arg[0]) > 0
            ), f"{key} is empty. Please add the --{key} flag with the approprate information."

        logger.info("Running server... ", ip=ip, port=port, channel=channel, token=token[:5])
        click.echo("Running server...")
        server = Server(ip=ip, port=port, channel_id=channel[0], bot_token=token[0])
        server.run()

    elif len(config) > 0:
        click.echo("running config")
        if tmux:
            click.echo("running in tmux")
            server_instances_from_configuration_file_in_tmux(config)
        else:
            server_instances_from_configuration_file(config)

    else:
        click.echo("Please choose a config file or run in normal mode.")


@cli.command()
@click.option("--ip", default="127.0.0.1", help="IP address")
@click.option("--port", default="5000", help="Port")
@click.option("--message", help="message to send", default="hello", type=(str))
def client(ip, port, message):
    logger.info("Running client... ", ip=ip, port=port)
    click.echo("Running client...")

    client = Client(ip=ip, port=port)
    ack = client.send(message=message)

    if ack:
        logger.info("Client succesfully send message... ", ip=ip, port=port, ack=ack)
    else:
        logger.info("Client did not send message... ", ip=ip, port=port, ack=ack)


@cli.command()
@click.option("--ip", default="127.0.0.1", help="IP address")
@click.option("--port", default="5000", help="Port")
def repl(ip, port):
    logger.info("Running repl... ", ip=ip, port=port)
    click.echo("Running repl...")

    repl = Repl(ip=ip, port=port)
    try:
        repl.start()
    except KeyboardInterrupt as e:
        click.echo(str(e))
    finally:
        sys.exit()
