import sys
import warnings
from copy import deepcopy
from datetime import date, datetime
from itertools import chain, islice
from zoneinfo import ZoneInfo

from django.db import models
from rich.prompt import Prompt

from elt import models as elt_models
from elt.lib.types import GisData, Juri


def log_and_print(logmsg, log):
    now = datetime.now(tz=ZoneInfo("America/Los_Angeles"))
    logmsg = f"{now.strftime('%y%m%d %H:%M:%S')}:: {logmsg}"
    log.write(logmsg)
    print(logmsg)


# Prompt user within a pipestage - do they want to create new data, add to existing data, or skip the stage?
# Returns 'c', 'i', or 's' for create, incremental, or skip
def pipestage_prompt(is_incremental, existing_filename=None, num_existing_entries=None, run_date=None):
    print("Stage options:")
    # print options for this stage. run_date and num_existing won't print if num_existing_entries is 0.
    num_existing_str = f" {num_existing_entries}" if num_existing_entries else ""
    run_date_str = f" with run_date={run_date}" if run_date and num_existing_entries else ""
    fname_str = f" from {existing_filename}" if existing_filename else ""
    print(f"C:Create new data, replacing{num_existing_str} existing entries{run_date_str}{fname_str}")
    prompt_options = ["c", "s"]
    if is_incremental and (num_existing_entries or existing_filename):
        print(f"I:Add to{num_existing_str} existing entires{run_date_str} incrementally{fname_str}")
        prompt_options += ["i"]
    if num_existing_entries or existing_filename:
        print(f"S:Skip stage, using latest{num_existing_str} existing entries{run_date_str}{fname_str}")
    else:
        print("Note: no existing data found for this stage. Choosing C...")
        return "c"
    use_file = Prompt.ask("Your choice? ", choices=prompt_options)
    return use_file


def batched(iterable, n):
    """Yield tuples of n items at a time from iterable."""
    # batched is in the std library in python 3.12.
    if sys.version_info >= (3, 12):
        warnings.warn("batched is in the std library in python 3.12.", DeprecationWarning, stacklevel=2)

    if n < 1:
        raise ValueError("n must be at least one")
    it = iter(iterable)
    # yield one tuple at a time until it's exhausted
    while batch := tuple(islice(it, n)):
        yield batch


def get_elt_pipe_filenames(
    geo: Juri, datatype: GisData, stage_dirname: str, extension="jsonl", expect_existing=False
):
    """Find filenames for current pipestage. Filenames should be dates. Return sorted by date from newest."""
    from elt.lib.extract.params import DATA_DIR

    # stage_dir = (DATA_DIR / geo.value / datatype.value / stage_dirname).resolve()
    stage_dir = (DATA_DIR / geo.value).resolve()
    matching_data_dirs = list(chain(stage_dir.glob(f"{datatype.value}_*"), stage_dir.glob(datatype.value)))
    if len(matching_data_dirs) > 1:
        print("Choose which data dir to use:")
        for i, data_dir in enumerate(matching_data_dirs):
            print(f"{i+1}: {data_dir.name}")
        choice = int(Prompt.ask("Your choice? ", choices=[str(i + 1) for i in range(len(matching_data_dirs))]))
        stage_dir = matching_data_dirs[choice - 1]
    elif len(matching_data_dirs) == 1:
        stage_dir = matching_data_dirs[0]
    else:
        print(f"Error: no data directory found for {geo.value}/{datatype.value}")
        sys.exit(1)
    resolved_datatype = stage_dir.name
    stage_dir = stage_dir / stage_dirname
    if not stage_dir.is_dir() and not expect_existing:
        # Confirm with the user that we should make the directory
        print(f"Directory {stage_dir} does not exist.")
        make_the_dir = Prompt.ask("Create it?", choices=["y", "n"])
        if make_the_dir == "y":
            stage_dir.mkdir(parents=True)
        assert stage_dir.is_dir()

    existing_files = sorted(stage_dir.glob(f"*.{extension}"), reverse=True) if stage_dir.is_dir() else []
    # files should be named YYMMDD[_more_stuff].extension
    date_files = [f for f in existing_files if f.name[:6].isdigit()]
    now = datetime.now(tz=ZoneInfo("America/Los_Angeles"))
    new_file = stage_dir / f"{now.strftime('%y%m%d')}.{extension}"
    if expect_existing:
        if not date_files:
            print(f"Error: no matched files of extension {extension} found in {stage_dir}. ")
            print(f"\nYou should create a file like {new_file}")
            sys.exit(1)
        new_file = None
    return date_files, resolved_datatype, new_file


def elt_model_with_run_date(model_name_camel: str, run_date: date) -> models.Model | None:
    """Return a version of the given ELT DB model which sets run-date as specified
    Args:
        model_name_camel (str): DB model name in CamelCase
        run_date (date): date to set in run_date field when saving
    Returns:
        models.Model: a Django model with a run_date field
    """
    try:
        raw_model = deepcopy(elt_models.__dict__[model_name_camel])
    except KeyError:
        return None

    # class WrappedDbModel(raw_model):
    def custom_save(self, *args, **kwargs):
        self.run_date = run_date
        super(raw_model, self).save(*args, **kwargs)

    custom_save.__dict__["alters_data"] = True
    raw_model.save = custom_save
    return raw_model
