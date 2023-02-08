"""
Search
======

A Pelican plugin to generate an index for static site searches.

Copyright (c) Justin Mayer
"""

from codecs import open
from inspect import cleandoc
from json import dumps
import logging
import os.path
from shutil import which
import subprocess

from jinja2.filters import do_striptags as striptags

from pelican import signals

logger = logging.getLogger(__name__)


class SearchSettingsGenerator:
    def __init__(self, context, settings, path, theme, output_path, *null):
        self.output_path = output_path
        self.context = context
        self.content = settings.get("PATH")
        self.tpages = settings.get("TEMPLATE_PAGES")
        self.search_mode = settings.get("SEARCH_MODE", "output")
        self.html_selector = settings.get("SEARCH_HTML_SELECTOR", "main")

    def build_search_index(self, search_settings_path):
        if not which("stork"):
            raise Exception("Stork must be installed and available on $PATH.")
        try:
            output = subprocess.run(
                [
                    "stork",
                    "build",
                    "--input",
                    search_settings_path,
                    "--output",
                    f"{self.output_path}/search-index.st",
                ],
                capture_output=True,
                encoding="utf-8",
                check=True,
            )
        except subprocess.CalledProcessError as e:
            raise Exception("".join(["Search plugin reported ", e.stdout, e.stderr]))

        return output.stdout

    def generate_output(self, writer):
        search_settings_path = os.path.join(self.output_path, "search.toml")

        pages = self.context["pages"] + self.context["articles"]

        for article in self.context["articles"]:
            pages += article.translations

        input_files = ""

        # Generate list of articles and pages to index
        for page in pages:
            if self.search_mode == "output":
                page_to_index = page.save_as
            if self.search_mode == "source":
                page_to_index = page.relative_source_path
            input_file = f"""
                [[input.files]]
                path = "{page_to_index}"
                url = "/{page.url}"
                title = {dumps(striptags(page.title))}
            """
            input_files = "".join([input_files, input_file])

        # Generate list of *template* pages to index (if any)
        for tpage in self.tpages:
            if self.search_mode == "output":
                tpage_to_index = self.tpages[tpage]
            if self.search_mode == "source":
                tpage_to_index = tpage
            input_file = f"""
                [[input.files]]
                path = "{tpage_to_index}"
                url = "{self.tpages[tpage]}"
                title = ""
            """
            input_files = "".join([input_files, input_file])

        # Assemble the search settings file
        if self.search_mode == "output":
            base_dir = self.output_path
        if self.search_mode == "source":
            base_dir = self.content
        search_settings = cleandoc(
            f"""
                [input]
                base_directory = "{base_dir}"
                html_selector = "{self.html_selector}"
                {input_files}
            """
        )

        # Write the search settings file to disk
        with open(search_settings_path, "w", encoding="utf-8") as fd:
            fd.write(search_settings)

        # Build the search index
        build_log = self.build_search_index(search_settings_path)
        build_log = "".join(["Search plugin reported ", build_log])
        logger.error(build_log) if "error" in build_log else logger.debug(build_log)


def get_generators(generators):
    return SearchSettingsGenerator


def register():
    signals.get_generators.connect(get_generators)
