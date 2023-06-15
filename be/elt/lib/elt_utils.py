import sys
from datetime import datetime
from itertools import chain
from zoneinfo import ZoneInfo

from rich.prompt import Prompt

from elt.lib.types import GisData, Juri


def log_and_print(logmsg, log):
    now = datetime.now(tz=ZoneInfo("America/Los_Angeles"))
    logmsg = f"{now.strftime('%y%m%d %H:%M:%S')}:: {logmsg}"
    log.write(logmsg)
    print(logmsg)


# Prompt user within a pipestage - do they want to create new data, add to existing data, or skip the stage?
# Returns 'c', 'i', or 's' for create, incremental, or skip
def pipestage_prompt(is_incremental, existing_filename):
    print("Stage options:")
    print("C:Create new data")
    prompt_options = ["c", "s"]
    if is_incremental:
        print(f"I:Add to existing data incrementally: {existing_filename}")
        prompt_options += ["i"]
    print(f"S:Skip stage, using latest existing data: {existing_filename}")
    use_file = Prompt.ask("Your choice? ", choices=prompt_options)
    return use_file


def get_elt_pipe_filenames(
    geo: Juri, datatype: GisData, stage_dirname: str, extension="jsonl", expect_existing=False
):
    """Find filenames ."""
    from elt.lib.arcgis.params import DATA_DIR

    # stage_dir = (DATA_DIR / geo.value / datatype.value / stage_dirname).resolve()
    stage_dir = (DATA_DIR / geo.value).resolve()
    matching_data_dirs = list(chain(stage_dir.glob("zoning_*"), stage_dir.glob("zoning")))
    if len(matching_data_dirs) > 1:
        print("Choose which data dir to use:")
        for i, data_dir in enumerate(matching_data_dirs):
            print(f"{i+1}: {data_dir.name}")
        choice = int(Prompt.ask("Your choice? ", choices=[str(i + 1) for i in range(len(matching_data_dirs))]))
        stage_dir = matching_data_dirs[choice - 1]
    resolved_datatype = stage_dir.name
    stage_dir = stage_dir / stage_dirname
    if not stage_dir.is_dir() and not expect_existing:
        # Confirm with the user that we should make the directory
        print(f"Directory {stage_dir} does not exist.")
        make_the_dir = Prompt.ask("Create it?", choices=["y", "n"])
        if make_the_dir == "y":
            stage_dir.mkdir(parents=True)
        assert stage_dir.is_dir()

    existing_dirs = sorted(stage_dir.iterdir(), reverse=True) if stage_dir.is_dir() else []
    now = datetime.now(tz=ZoneInfo("America/Los_Angeles"))
    new_file = stage_dir / f"{now.strftime('%y%m%d')}.{extension}"
    if expect_existing:
        if not existing_dirs:
            print(f"Error: no existing files found in {stage_dir}. " f"\nYou should create a file like {new_file}")
            sys.exit(1)
        new_file = None
    return existing_dirs, resolved_datatype, new_file
