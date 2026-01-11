"""Common functions."""

import os
from collections import namedtuple
import re
import tempfile

import dateutil.parser
from git import Repo, Tag
import strictyaml  # type: ignore

LICENSES = {
    "cc-by-sa-4.0": "![](/images/license_cc-by-sa.svg){fig-alt='CC BY-SA 4.0' width=120px}",
    "cc-by-nc-sa-4.0": "![](/images/license_cc-by-nc-sa.svg){fig-alt='CC BY-NC-SA 4.0' width=120px}"
}

PART_REPLACE = {
    # instrument names
    "bc_realized": "bc (realizzato)",
    "cord": "cor (D)",
    "corf": "cor (F)",
    "cemb_realized": "cemb (realizzato)",
    "full_score": "full score",
    "oba": "ob d'amore",
    "obdc": "ob da caccia",
    "org_realized": "org (realizzato)",
    "pf_red": "pf (riduzione)",
    "vlada": "vla d'amore",

    # instrument numbers
    r"([\w\)])123$": r"\1 1, 2, 3",
    r"([\w\)])12$": r"\1 1, 2",
    r"([\w\)])(\d)$": r"\1 \2",

    # spaces
    r"[_ ]": r"&nbsp;"
}

SLUG_REPLACE = {
    " ": "-",
    ":": "-",
    "/": "-",
    ".": "-",
    "–": "-",
    ",": "",
    "(": "",
    ")": "",
    "·": "",
    "*": "star",
    "á": "a",
    "ä": "ae",
    "æ": "ae",
    "í": "i",
    "ö": "oe",
    "œ": "oe",
    "ß": "ss",
    "š": "s",
    "ü": "ue",
    "ů": "u",
    "ý": "y"
}

ASSET_FULL_SCORE = "**full&nbsp;score**"
ASSET_MIDI = "midi_collection.zip"

TABLEROW_TEMPLATE = "|[{id}](#work-{id_slug})|{title}|{genre}|"

INTRO_TEMPLATE = """\
::: {{.composer-details}}
|||
|-|-|
|*born*|{born}|
|*died*|{died}|
|*links*|{links}|
|*authorities*|{authorities}|
|*archives*|{archives}|
|*literature*|{literature}|

: {{tbl-colwidths="[15,85]" .composer-table}}

{cv}
:::
"""

# pylint: disable=line-too-long
ENCYCLOPEDIAS = {
    "mgg":          "[MGG](https://www.mgg-online.com/mgg/stable/{})",
    "grove":        "[Grove](https://doi.org/{})",
    "wikipedia_de": "[{{{{< fa brands wikipedia-w >}}}} (de)](https://de.wikipedia.org/wiki/{})",
    "wikipedia_cs": "[{{{{< fa brands wikipedia-w >}}}} (cs)](https://cs.wikipedia.org/wiki/{})",
    "wikipedia_en": "[{{{{< fa brands wikipedia-w >}}}} (en)](https://en.wikipedia.org/wiki/{})",
    "oeml":         "[ÖML](https://doi.org/{})",
    "oebl":         "[ÖBL](https://doi.org/{})",
    "db":           "[DB](https://www.deutsche-biographie.de/{}.html)",
}

AUTHORITIES = {
    "gnd":  "[GND](https://d-nb.info/gnd/{})",
    "viaf": "[VIAF](https://viaf.org/viaf/{})"
}

ARCHIVES = {
    "imslp": "[IMSLP](https://imslp.org/wiki/Category:{})",
    "cpdl":  "[CPDL](https://www.cpdl.org/wiki/index.php/{})"
}

Composer = namedtuple("Composer", "last first suffix", defaults=["", ""])


def format_metadata(metadata: dict) -> dict:
    """Preprocesses metadata.

    Args:
        metadata: Metadata extracted from metadata.yaml

    Returns:
        Reformatted metadata
    """

    # add an id
    if "id" not in metadata or metadata["id"] is None:
        for source in metadata["sources"].values():
            if source.get("principal", False):
                metadata["id"] = f"({source['siglum']} {source['shelfmark']})"
                break

    # add a subtitle
    if "subtitle" not in metadata:
        metadata["subtitle"] = metadata["id"]
    else:
        metadata["subtitle"] = f"{metadata['subtitle']}<br/>{metadata['id']}"
    metadata["subtitle"] = metadata["subtitle"].replace(r"\\", " ")

    # convert LaTeX commands to plain text
    metadata["title"] = latex_to_text(metadata["title"])
    metadata["scoring"] = latex_to_text(metadata["scoring"])

    # misc fields
    metadata["license"] = LICENSES[metadata["license"]]
    metadata["id_slug"] = slugify(metadata["id"])

    # asset links
    metadata = format_asset_list(metadata)

    return metadata


def latex_to_text(s: str) -> str:
    """Converts LaTeX commands to plain text.

    Args:
        s: string to format

    Returns:
        reformatted string
    """
    res = re.sub(r"\\newline", " ", s)
    res = re.sub(r"\\\\", " ", res)
    res = re.sub(r"\\flat\s(.)", r"\1♭", res)
    res = re.sub(r"\\sharp\s(.)", r"\1♯", res)
    res = re.sub(r"\\\s", r" ", res)
    return res


def slugify(s: str) -> str:
    """Formats a string as valid slug.

    Args:
        s (str): string to format

    Returns:
        str: a slug
    """
    slug = s.lower()
    for k, v in SLUG_REPLACE.items():
        slug = slug.replace(k, v)
    return slug


def make_part_name(filename: str) -> str:
    """Formats a part filename.

    Args:
        filename: part file name

    Returns:
        Reformatted part name.
    """
    if filename == ASSET_MIDI:
        return filename

    if filename == "full_score.pdf":
        return ASSET_FULL_SCORE

    name = filename.removesuffix(".pdf")
    if name.startswith("coro_"):
        name = re.sub("_(.+)$", " (\\1)", name)

    for old, new in PART_REPLACE.items():
        name = re.sub(old, new, name)

    return name


def format_asset_list(metadata: dict) -> dict:
    """Formats asset list.

    Args:
        metadata: metadata

    Returns:
        metadata with formatted asset and MIDI links
    """

    asset_link = "[{}]({})"

    try:
        asset_files = metadata["assets_gh"]
        work = ""
    except KeyError:
        asset_files = [a.replace(".ly", ".pdf")
                       for a in metadata["assets_server"]] + [ASSET_MIDI]
        work = metadata["work_dir"] + "/"

    asset_urls = {
        make_part_name(f):
        f"https://edition.esser-skala.at/assets/{metadata['repo']}/{work}{f}"
        for f in asset_files
    }

    # move midi asset to separate variable
    try:
        midi_link = asset_link.format(
            "{{< fa music >}}",
            asset_urls[ASSET_MIDI]
        )
        del asset_urls[ASSET_MIDI]
    except KeyError:
        midi_link = None

    # sort asset list and move full score to the front
    asset_names = sorted(asset_urls.keys())
    try:
        asset_names.remove(ASSET_FULL_SCORE)
        asset_names.insert(0, ASSET_FULL_SCORE)
    except ValueError:
        pass

    write_assets(asset_urls, metadata)
    metadata["asset_links"] = " ".join(
        [asset_link.format(n, asset_urls[n]) for n in asset_names]
    )
    metadata["midi"] = midi_link
    return metadata


def write_assets(asset_urls: dict, metadata: dict) -> None:
    """
    Write assets URLs on the server and their corresponding
    GitHub release URL to a CSV file.

    Args:
        asset_urls: asset URLs on the server
        metadata: work metadata
    """

    url_gh = ("https://github.com/edition-esser-skala/" +
              metadata["repo"] +
              "/releases/download/" +
              metadata["latest_version"] +
              "/")

    with open("data_generated/" + metadata["repo"] + ".csv",
              "w", encoding="utf8") as f:
        f.writelines([f"{url},{url_gh}{os.path.basename(url)}\n"
                      for url in asset_urls.values()])


def format_work_entry(work: dict, page_composer: Composer) -> tuple[str, str]:
    """Formats the work entry.

    Args:
        work: work metadata
        page_composer: composer whose works are presented on the current page

    Returns:
        (1) row for TOC table
        (2) work entry
    """

    work = format_metadata(work)

    # title
    work["distinct_composer"] = ""
    if "composer" in work and Composer(**work["composer"]) != page_composer:
        work["distinct_composer"] = (
            "["
            + format_composer_name(work["composer"])
            + "]{.work-composer}<br/>"
        )
    title = (
        '### {distinct_composer}{title}<br/>[{subtitle}]{{.work-subtitle}}'
        ' {{#work-{id_slug} .unlisted}}\n'
    )
    res = [title.format(**work), "|||\n|-|-|"]

    # table rows
    row = '|*{}*|{}|'

    ## genre
    res.append(row.format("genre", work["genre"]))

    ## festival (optional)
    if "festival" in work:
        res.append(row.format("festival", work["festival"]))

    ## scoring
    res.append(row.format("scoring", work["scoring"]))

    ## full score and parts
    res.append(row.format("scores", work["asset_links"]))

    ## MIDI collection (optional)
    if work["midi"]:
        res.append(row.format("MIDI", work["midi"]))

    ## IMSLP link (optional)
    if "imslp" in work:
        res.append(
            row.format(
                "IMSLP",
                f"[scores and parts](https://imslp.org/wiki/{work['imslp']})"
            )
        )

    ## link to printed edition (optional)
    if "asin" in work:
        res.append(
            row.format(
                "print",
                f"[full score](https://amazon.de/dp/{work['asin']})"
            )
        )

    ## source code
    res.append(
        row.format(
            "source",
            f"[GitHub ({work['latest_version']}, {work['latest_date']})](https://github.com/edition-esser-skala/{work['repo']})"
        )
    )

    ## license
    res.append(row.format("license", work["license"]))

    # CSS class
    res.append('\n: {tbl-colwidths="[10,90]" .work-table}\n')

    return TABLEROW_TEMPLATE.format(**work), "\n".join(res)


def format_composer_details(data: dict) -> str:
    """Format composer details from YAML front  matter.

    Args:
        data:dict with composer details

    Returns:
        composer details formatted as markdown
    """

    # born date and possibly location
    born = "(unknown)"
    if "born" in data:
        born = data["born"]["date"]
        if "location" in data["born"]:
            born = f'{data["born"]["date"]} ({data["born"]["location"]})'

    # died date and possibly location
    died = "(unknown)"
    if "died" in data:
        died = data["died"]["date"]
        if "location" in data["died"]:
            died = f'{data["died"]["date"]} ({data["died"]["location"]})'

    # encyclopedia links (if available)
    links = "–"
    if "encyclopedia" in data:
        links = " ".join([ENCYCLOPEDIAS[k].format(v)
                          for k, v in data["encyclopedia"].items()])

    # authority files (if available)
    authorities = "–"
    if "authority" in data:
        authorities = " ".join([AUTHORITIES[k].format(v)
                                for k, v in data["authority"].items()])

    # sheet music archives (if available)
    archives = "–"
    if "archive" in data:
        archives = " ".join([ARCHIVES[k].format(v)
                             for k, v in data["archive"].items()])

    # literature (if available)
    literature = "–"
    if "literature" in data:
        literature = data["literature"]

    # cv (if available)
    cv = data.get("cv", "")

    return INTRO_TEMPLATE.format(
        born=born,
        died=died,
        links=links,
        authorities=authorities,
        archives=archives,
        cv=cv,
        literature=literature
    )


def get_tag_date(tag: Tag) -> str:
    """Return the date of a git tag in ISO 8601 format.

    Args:
        tag: git tag

    Returns:
        tag date
    """
    return (dateutil.parser.parse(tag.commit.commit.last_modified)
                           .strftime("%Y-%m-%d"))


def get_coll_metadata(metadata: dict) -> list:
    """Collects metadata for collection repos.

    Args:
        metadata: metadata of parent repository

    Returns:
        work metadata
    """

    with tempfile.TemporaryDirectory() as repo_dir:
        Repo.clone_from(
            "https://github.com/edition-esser-skala/" + metadata["repo"],
            repo_dir,
            multi_options=["--depth 1",
                           "--branch " + metadata["latest_version"]]
        )

        try:
            with open(f"{repo_dir}/ignored_works", encoding="utf8") as f:
                ignored_works = [w.strip() for w in f.read().splitlines()
                                 if not w.startswith("#")]
        except FileNotFoundError:
            ignored_works = ["template"]

        work_dirs = os.listdir(f"{repo_dir}/works")

        works = []
        for counter, work_dir in enumerate(work_dirs):
            counter_str = f"({counter + 1}/{len(work_dirs)})"

            if work_dir in ignored_works:
                print(f"     {counter_str} Ignoring {work_dir}")
                continue

            print(f"     {counter_str} Adding {work_dir}")
            with open(f"{repo_dir}/works/{work_dir}/metadata.yaml",
                      encoding="utf-8") as f:
                work = strictyaml.load(f.read()).data

            work["repo"] = metadata["repo"]
            work["latest_version"] = metadata["latest_version"]
            work["latest_date"] = metadata["latest_date"]
            work["work_dir"] = work_dir
            work["assets_server"] = os.listdir(f"{repo_dir}/works/{work_dir}/scores")
            works.append(work)

    return works


def format_composer_name(name: dict) -> str:
    """Format the composer name.

    Args:
        name: dict with fields last, first (optional) and suffix (optional)

    Returns:
        formatted composer name 'Last, First Suffix'
    """

    res = name["last"]
    try:
        res += ", " + name["first"]
        res += " " + name["suffix"]
    except KeyError:
        pass
    return res
