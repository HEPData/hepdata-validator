import sys

import click

from . import full_submission_validator


@click.command()
@click.option('--directory', '-d', default='.', help='Directory to check (defaults to current working directory)')
@click.option('--file', '-f', default=None, help='Single submission yaml file to check - see https://hepdata-submission.readthedocs.io/en/latest/single_yaml.html. (Overrides directory)')
@click.option('--zipfile', '-z', default=None, help='Zipped file (e.g. .zip, .tar.gz, .gzip) to check. (Overrides directory and file)')
def validate(directory, file, zipfile):  # pragma: no cover
    """
    Offline validation of submission.yaml and YAML data files.
    Can check either a single file or a directory
    """
    try:
        is_valid = full_submission_validator.validate(directory, file, zipfile)
        if not is_valid:
            sys.exit(1)
    except ValueError as e:
        import traceback

        print(''.join(traceback.format_exception(None, e, e.__traceback__)))
        click.echo(f"ERROR: {e}")
        sys.exit(2)
