from typing import Any
from typing import List
from typing import Optional
from typing import Tuple

import click


# Inspired by https://github.com/pallets/click/issues/430#issuecomment-207580492
class DefaultGroup(click.Group):
    """
    Example Usage:

    python3 cmd.py <==> python3 cmd.py run
    python3 cmd.py --test foo bar <==> python3 cmd.py run --test foo bar

    cmd.py

    @click.group(cls=DefaultGroup, default_command="run")
    def cli():
        pass

    @cli.command()
    @click.option('--test')
    @click.option('--config')
    @click.option('--blah')
    def run(test, config, blah):
        click.echo("a")
        click.echo(test)

    @cli.command()
    def init()
        click.echo('The subcommand')

    cli()
    """

    ignore_unknown_options = True

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        default_command = kwargs.pop("default_command", None)
        super(DefaultGroup, self).__init__(*args, **kwargs)
        self.default_command_name = None
        if default_command is not None:
            self.default_command_name = default_command

    def get_help(self, ctx: click.Context) -> str:
        """
        Override `semgrep --help` to print out `semgrep scan --help`
        for backwards compatibility
        """
        command = self.get_command(ctx, "scan")
        assert command
        return command.get_help(ctx)

    def parse_args(self, ctx: click.Context, args: List[str]) -> List[str]:
        """
        If there are no arguments, insert default command
        """
        if not args and self.default_command_name is not None:
            args.insert(0, self.default_command_name)
        return super(DefaultGroup, self).parse_args(ctx, args)

    def get_command(
        self, ctx: click.Context, command_name: str
    ) -> Optional[click.Command]:
        """
        If COMMAND_NAME is not in self.commands then it means
        it is an option/arg to the default command. So place
        this in the context for retrieval in resolve_command.

        Also replace COMMAND_NAME with the self.default_command_name

        """
        if command_name not in self.commands and self.default_command_name:
            click.echo("No subcommand passed so running `semgrep scan`", err=True)
            click.echo(
                "Note that running semgrep without subcommand will be deprecated in 0.89.0",
                err=True,
            )
            click.echo(
                "Please update invocations of `semgrep ...` to `semgrep scan ...`",
                err=True,
            )
            ctx._default_command_overwrite_args0 = command_name  # type: ignore
            command_name = self.default_command_name

        return super(DefaultGroup, self).get_command(ctx, command_name)

    def resolve_command(
        self, ctx: click.Context, args: List[str]
    ) -> Tuple[str, click.Command, List[str]]:
        """
        MultiCommand.resolve_command assumes args[0] is the command name
        if we are running a default command then args[0] will actually be
        an option/arg to the default command.

        In get_command we put this first arg into _default_command_overwrite_arg0
        in the context. So here we just read it from context again

        If args[0] is actually a command name then _default_command_overwrite_args0
        will not be set so this function is equivalent to existing behavior
        """
        cmd_name, cmd, args = super(DefaultGroup, self).resolve_command(ctx, args)
        if hasattr(ctx, "_default_command_overwrite_args0"):
            args.insert(0, ctx._default_command_overwrite_args0)  # type: ignore
        return cmd_name, cmd, args
