"""Prepare score pages from metadata in GitHub score repos."""

from operator import itemgetter
import os
import pickle
import re
from typing import Optional

import frontmatter  # type: ignore
from github import Github
from github.Organization import Organization
from github.GithubException import UnknownObjectException
import strictyaml  # type: ignore

from utils import (Composer,
                   format_composer_details,
                   format_composer_name,
                   format_work_entry,
                   get_coll_metadata,
                   get_tag_date)

try:
    from pat import TOKEN
except ModuleNotFoundError:
    TOKEN = os.environ["GH_API_TOKEN"]


PAGE_TEMPLATE = """\
{hero}

{composer_details}

{intro}

|ID|Title|Genre|
|--|-----|-----|
{table_rows}

: {{.overview-table}}

{work_details}
"""


def get_markdown_file(gh_org: Organization,
                      repo_file: str,
                      out_file: str,
                      title: str) -> None:
    """Downloads a markdown file that should be used as page.

    Args:
        gh_org: GitHub organization
        repo_file: file name in repository
        out_file: output file name
        title: page title
    """
    header = (
        "---\n"
        f"title: {title}\n"
        "---\n"
    )

    print(f"Obtaining {repo_file}")
    doc = (gh_org  # type: ignore
           .get_repo("ees-tools")
           .get_contents(repo_file)
           .decoded_content
           .decode("utf-8")
           .split("\n", 1)[1])  # remove first line (title)

    doc = header + re.sub("# Contents.+?##", "#", doc, flags=re.DOTALL)

    with open(out_file, "w", encoding="utf-8") as f:
        f.write(doc)


def collect_metadata(gh_org: Organization,
                     ignored_repos: Optional[list[str]]=None,
                     collection_repos: Optional[list[str]]=None) -> dict:
    """Collects work metadata from YAML files in GitHub repos.

    Args:
        gh_org: GitHub organization
        ignored_repos: list of ignored repositories
        collection_repos: list of collection repositories

    Returns:
        work metadata
    """

    repos = gh_org.get_repos(sort="updated")
    if ignored_repos is None:
        ignored_repos = []
    if collection_repos is None:
        collection_repos = []

    works: dict[Composer, list] = {}

    for counter, repo in enumerate(repos):
        counter_str = f"({counter + 1}/{repos.totalCount})"

        if repo.name in ignored_repos:
            print(f"{counter_str} Ignoring {repo.name} (blacklisted)")
            continue

        if repo.private:
            print(f"{counter_str} Ignoring {repo.name} (private)")
            continue

        tags = repo.get_tags()
        if tags.totalCount == 0:
            print(f"{counter_str} Ignoring {repo.name} (no tags)")
            continue

        print(f"{counter_str} Analyzing {repo.name}")
        try:
            metadata = strictyaml.load(
                repo  # type: ignore
                .get_contents("metadata.yaml", ref=tags[0].name)
                .decoded_content
                .decode("utf-8")
            ).data
        except UnknownObjectException:
            print(f"UnknownObjectException for {repo.name}")
            continue

        metadata["repo"] = repo.name
        metadata["latest_version"] = tags[0].name
        metadata["latest_date"] = get_tag_date(tags[0])  # type: ignore

        releases = repo.get_releases()
        if releases.totalCount > 0:
            metadata["assets_gh"] = [i.name for i in releases[0].get_assets()]

        try:
            print_data = strictyaml.load(
                repo  # type: ignore
                .get_contents("print/printer.yaml")
                .decoded_content
                .decode("utf-8")
            ).data
            metadata["asin"] = print_data["asin"]
        except UnknownObjectException:
            pass

        if repo.name in collection_repos:
            metadata["collection"] = get_coll_metadata(metadata)

        c = Composer(**metadata["composer"])
        try:
            works[c] += [metadata]
        except KeyError:
            works[c] = [metadata]

    return works


def generate_score_pages(works: dict) -> None:
    """Generates one markdown file for each composer.

    Args:
        works: works metadata
    """

    composer_pages = os.listdir("_scores_templates")
    if "_template.qmd" in composer_pages:
        composer_pages.remove("_template.qmd")

    for composer_qmd in composer_pages:
        print("Formatting", composer_qmd)
        page = frontmatter.load("_scores_templates/" + composer_qmd)
        composer = Composer(**page["composer_data"]["name"])
        if composer not in works:
            print("  Warning: No work found.")
            continue

        # hero image
        try:
            hero = f'![]({page["composer_data"]["hero"]}){{fig-align="center"}}'
        except KeyError:
            hero = ""

        # composer details
        composer_details = format_composer_details(page["composer_data"])

        # flatten work metadata to a list of dicts,
        # each of which describes a work
        works_all = []
        for work in works[composer]:
            if "collection" in work:
                works_all += work["collection"]
            else:
                works_all.append(work)

        # get table rows and work details
        work_data = [format_work_entry(w, composer)
                     for w in sorted(works_all, key=itemgetter("title"))]

        table_rows = "\n".join([r for r, _ in work_data])
        work_details = "\n".join([d for _, d in work_data])

        # save composer page
        page["title"] = format_composer_name(page["composer_data"]["name"])
        page.content = PAGE_TEMPLATE.format(
            hero=hero,
            composer_details=composer_details,
            intro=page["composer_data"].get("intro", ""),
            table_rows=table_rows,
            work_details=work_details
        )
        del page["composer_data"]
        out = frontmatter.dumps(page)

        with open("scores/" + composer_qmd, "w", encoding="utf-8") as f:
            f.write(out)


def main() -> None:
    """Main workflow."""
    ignored_repos = [
        ".github",
        "ees-template",
        "cantorey-performance-materials",
        "ees-tools",
        "imslp-lists",
        "misc-analyses",
        "sacral-lyrics",
        "tuma-catalogue-of-works",
        "webpage",
        "werner-catalogue-of-works"
    ]
    collection_repos = [
        "eybler-sacred-music",
        "haydn-m-proprium-missae",
        "tuma-collected-works",
        "werner-collected-works"
    ]

    gh = Github(TOKEN)
    gh_org = gh.get_organization("edition-esser-skala")

    print(gh.get_rate_limit().resources.core)
    get_markdown_file(gh_org,
                      "documents/editorial_guidelines.md",
                      "editorial-guidelines.qmd",
                      "Editorial guidelines")
    get_markdown_file(gh_org,
                      "README.md",
                      "technical-documentation.qmd",
                      "Technical documentation",)

    try:
        with open("data_generated/works_metadata.pkl", "rb") as f:
            all_works = pickle.load(f)
    except FileNotFoundError:
        all_works = collect_metadata(gh_org, ignored_repos, collection_repos)
        with open("data_generated/works_metadata.pkl", "wb") as f:
            pickle.dump(all_works, f)

    generate_score_pages(all_works)

    print(gh.get_rate_limit().resources.core)


if __name__ == "__main__":
    main()
