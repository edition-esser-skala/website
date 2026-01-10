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

FULL_SCORE_ASSET_NAME = "**full&nbsp;score**"

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

: {{tbl-colwidths="[15,85]" .composer-table}}

{cv}

{literature}
:::
"""

# pylint: disable=line-too-long
ENCYCLOPEDIAS = {
    "mgg": "[[MGG](https://www.mgg-online.com/mgg/stable/{})]{{.asset-link}}",
    "grove": "[[Grove](https://doi.org/{})]{{.asset-link}}",
    "wikipedia_de": '[[{{{{< fa brands wikipedia-w >}}}} (de)](https://de.wikipedia.org/wiki/{})]{{.asset-link}}',
    "wikipedia_cs": '[[{{{{< fa brands wikipedia-w >}}}} (cs)](https://cs.wikipedia.org/wiki/{})]{{.asset-link}}',
    "wikipedia_en": '[[{{{{< fa brands wikipedia-w >}}}} (en)](https://en.wikipedia.org/wiki/{})]{{.asset-link}}',
    "oeml": "[[ÖML](https://doi.org/{})]{{.asset-link}}",
    "oebl": "[[ÖBL](https://doi.org/{})]{{.asset-link}}",
    "db": "[[DB](https://www.deutsche-biographie.de/{}.html)]{{.asset-link}}",
}

AUTHORITIES = {
    "gnd": "[[GND](https://d-nb.info/gnd/{})]{{.asset-link}}",
    "viaf": "[[VIAF](https://viaf.org/viaf/{})]{{.asset-link}}"
}

ARCHIVES = {
    "imslp": "[[IMSLP](https://imslp.org/wiki/Category:{})]{{.asset-link}}",
    "cpdl": "[[CPDL](https://www.cpdl.org/wiki/index.php/{})]{{.asset-link}}"
}

REFERENCE_TEMPLATE = {
    "article": "- {author} ({year}). {title}. {journal} {volume}:{pages}.",
    "book": "- {author} ({year}). {title}. {publisher}, {location}.",
    "website": "- {author} ({year}). {title}."
}

Composer = namedtuple("Composer", "last first suffix", defaults=["", ""])


def format_metadata(metadata: dict) -> dict:
    """Preprocesses metadata.

    Args:
        metadata (dict): Metadata extracted from metadata.yaml

    Returns:
        dict: Reformatted metadata.
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
    if "assets_gh" in metadata:
        metadata = format_asset_list("assets_gh", metadata)
    else:
        metadata = format_asset_list("assets_server", metadata)

    return metadata


def latex_to_text(s: str) -> str:
    """Converts LaTeX commands to plain text.

    Args:
        s (str): string to format

    Returns:
        str: reformatted string.
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


def make_part_name(filename: str, extension: str) -> str:
    """Formats a part filename.

    Args:
        filename (str): part file name
        extension (str): part file extension

    Returns:
        str: Reformatted part name.
    """
    if filename == "midi_collection.zip":
        return filename

    if filename.startswith("full_score"):
        return FULL_SCORE_ASSET_NAME

    name = filename.removesuffix(extension)
    if name.startswith("coro_"):
        name = re.sub("_(.+)$", " (\\1)", name)

    for old, new in PART_REPLACE.items():
        name = re.sub(old, new, name)

    return name


def format_asset_list(asset_key: str, metadata: dict) -> dict:
    """Formats asset list.

    Args:
        asset_key (str): key of dict entry with assets
        metadata (dict): metadata

    Returns:
        dict: metadata with formatted asset and MIDI links
    """

    asset_link_github = "](https://github.com/edition-esser-skala/{repo}/releases/download/{version}/{file})]{{.asset-link}}"

    asset_link_server = "](https://edition.esser-skala.at/assets/pdf/{repo}/{work}/{file})]{{.asset-link}}"

    if asset_key == "assets_gh":  # assets on GitHub
        assets = {
            make_part_name(asset, ".pdf"):
            asset_link_github.format(
                repo=metadata["repo"],
                version=metadata["latest_version"],
                file=asset
            )
            for asset in metadata[asset_key]
        }

        midi_file = "midi_collection.zip"
        midi_link = None
        if midi_file in assets:
            midi_link = assets[midi_file]
            del assets[midi_file]

    else:  # assets on server
        assets = {
            make_part_name(asset, ".ly"):
            asset_link_server.format(
                repo=metadata["repo"],
                work=metadata["work_dir"],
                file=asset.replace(".ly", ".pdf")
            )
            for asset in metadata[asset_key]
        }

        midi_link = asset_link_server.format(
            repo=metadata["repo"],
            work=metadata["work_dir"],
            file="midi_collection.zip"
        )

    # sort asset list and move full score to the front
    asset_names = sorted(assets.keys())
    try:
        asset_names.remove(FULL_SCORE_ASSET_NAME)
        asset_names.insert(0, FULL_SCORE_ASSET_NAME)
    except ValueError:
        pass

    metadata["asset_links"] = " ".join(
        [f"[[{k}{assets[k]}" for k in asset_names]
    )
    if midi_link:
        midi_link = "[[{{< fa music >}}" + midi_link
    metadata["midi"] = midi_link
    return metadata


def format_work_entry(work: dict) -> tuple[str, str]:
    """Formats the work entry."""

    # title
    title = (
        '### {title}<br/>[{subtitle}]{{.work-subtitle}}'
        ' {{#work-{id_slug}}}\n'
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
    if "midi" in work:
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
            f"[GitHub](https://github.com/edition-esser-skala/{work['repo']})"
        )
    )

    ## license
    res.append(row.format("license", work["license"]))

    # CSS class
    res.append('\n: {tbl-colwidths="[10,90]" .work-table}\n')

    return TABLEROW_TEMPLATE.format(**work), "\n".join(res)


def format_reference(ref: dict) -> str:
    """Format a reference.

    Args:
        ref (list): reference details (author, title, ...)

    Returns:
        str: formatted reference
    """

    # format the author(s): "A" or "A, B" or "A, B, and C"
    if isinstance(ref["author"], str):
        authors = ref["author"]
    else:  # list of authors
        if len(ref["author"]) == 2:
            authors = f'{ref["author"][0]} and {ref["author"][1]}'
        if len(ref["author"]) > 2:
            authors = ref["author"][:-1]
            authors = ", ".join(authors) + ", and" + ref["author"][-1]
    ref["author"] = authors

    if "url" in ref:
        ref["title"] = f'[{ref["title"]}]({ref["url"]})'

    return REFERENCE_TEMPLATE[ref["type"]].format(**ref)


def parse_composer_details(data: dict) -> str:
    """Parse composer details (dates, links, cv ...) from a YAML file.

    Args:
        file (str): YAML file with composer details

    Returns:
        str: Markdown string to be included in the webpage
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
    links = "-"
    if "encyclopedia" in data:
        links = " ".join([ENCYCLOPEDIAS[k].format(v)
                          for k, v in data["encyclopedia"].items()])

    # authority files (if available)
    authorities = "-"
    if "authority" in data:
        authorities = " ".join([AUTHORITIES[k].format(v)
                                for k, v in data["authority"].items()])

    # sheet music archives (if available)
    archives = "-"
    if "archive" in data:
        archives = " ".join([ARCHIVES[k].format(v)
                             for k, v in data["archive"].items()])

    # cv (if available)
    cv = data.get("cv", "")

    # literature (if available)
    literature = ""
    if "literature" in data:
        literature = "\n".join(
            ["#### Literature"] +
            [format_reference(r) for r in data["literature"]]
        )

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
    """Return the date of a git tag in ISO 8601 format."""
    return (dateutil.parser.parse(tag.commit.commit.last_modified)
                          .strftime("%Y-%m-%d"))


def get_coll_metadata(repo: str,
                      latest_tag: str) -> list:
    """Collects metadata for collection repos."""

    print("  -> Adding collection repository", repo)

    with tempfile.TemporaryDirectory() as repo_dir:
        Repo.clone_from(
            f"https://github.com/edition-esser-skala/{repo}",
            repo_dir,
            multi_options=["--depth 1", f"--branch {latest_tag}"]
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
                metadata = strictyaml.load(f.read()).data

            metadata["repo"] = repo
            metadata["work_dir"] = work_dir
            metadata["assets_server"] = os.listdir(f"{repo_dir}/works/{work_dir}/scores")
            works.append(metadata)

    return works
