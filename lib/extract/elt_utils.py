from datetime import datetime
from zoneinfo import ZoneInfo

from rich.prompt import Prompt

from lib.extract.arcgis.types import GeoEnum, GisDataTypeEnum


def log_and_print(logmsg, log):
    now = datetime.now(tz=ZoneInfo("America/Los_Angeles"))
    logmsg = f"{now.strftime('%y%m%d %H:%M:%S')}:: {logmsg}"
    log.write(logmsg)
    print(logmsg)


# Prompt user within a pipestage - do they want to create new data, add to existing data, or skip the stage?
# Returns 'c', 'i', or 's' for create, incremental, or skip
def pipestage_prompt(is_incremental, existing_filename):
    print("Stage options:")
    print(f"C:Create new data")
    prompt_options = ["c", "s"]
    if is_incremental:
        print(f"I:Add to existing data incrementally: {existing_filename}")
        prompt_options += ["i"]
    print(f"S:Skip stage, using latest existing data: {existing_filename}")
    use_file = Prompt.ask("Your choice? ", choices=prompt_options)
    return use_file


def get_elt_pipe_filenames(geo: GeoEnum, datatype: GisDataTypeEnum, stage_dirname: str, extension="jsonl"):
    from lib.extract.arcgis.params import DATA_DIR

    now = datetime.now(tz=ZoneInfo("America/Los_Angeles"))
    output_dir = DATA_DIR / geo.value / "shapes" / datatype.value / stage_dirname
    assert output_dir.is_dir()
    existing_files = sorted(output_dir.iterdir(), reverse=True)
    new_file = output_dir / f"{now.strftime('%y%m%d')}.{extension}" if extension else None
    return existing_files, new_file
