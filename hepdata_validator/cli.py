import sys

import click

from .full_submission_validator import FullSubmissionValidator


@click.command()
@click.option('--directory', '-d', default='.', help='Directory to check (defaults to current working directory)')
@click.option('--file', '-f', default=None, help='Single .yaml or .yaml.gz file (but not submission.yaml or a YAML data file) to check - see https://hepdata-submission.readthedocs.io/en/latest/single_yaml.html. (Overrides directory)')
@click.option('--archive', '-a', default=None, help='Archive file (.zip, .tar, .tar.gz, .tgz) to check. (Overrides directory and file)')
def validate(directory, file, archive):  # pragma: no cover
    """
    Offline validation of submission.yaml and YAML data files.
    Can check either a directory, an archive file, or the single YAML file format.
    """
    file_or_dir_checked = archive if archive else (file if file else directory)
    validator = FullSubmissionValidator()
    is_valid = validator.validate(directory, file, archive)
    if is_valid:
        click.echo(f"{file_or_dir_checked} is valid.")
    else:
        click.echo(f"ERROR: {file_or_dir_checked} is invalid.")

    validator.print_valid_files()
    for f in validator.messages.keys():
        validator.print_errors(f)

    if not is_valid:
        sys.exit(1)
