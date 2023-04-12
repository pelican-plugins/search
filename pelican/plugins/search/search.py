"""
Search
======

A Pelican plugin to generate an index for static site searches.

Copyright (c) Justin Mayer
"""

import logging
from pathlib import Path
from shutil import which
import subprocess
from typing import Dict, List

from jinja2.filters import do_striptags as striptags
import rtoml

from pelican import signals

logger = logging.getLogger(__name__)


class SearchSettingsGenerator:
    def __init__(self, context, settings, path, theme, output_path, *null):
        self.output_path = output_path
        self.context = context
        self.content = settings.get("PATH")
        self.tpages = settings.get("TEMPLATE_PAGES")
        self.input_options = settings.get("STORK_INPUT_OPTIONS", {})
        self.output_options = settings.get("STORK_OUTPUT_OPTIONS")
        # Set default values
        self.input_options.setdefault("html_selector", "main")
        self.input_options.setdefault("base_directory", self.output_path)

        # Handle deprecated settings
        if settings.get("SEARCH_HTML_SELECTOR") and not settings.get(
            "STORK_INPUT_OPTIONS"
        ):
            logger.warning(
                "The SEARCH_HTML_SELECTOR setting is deprecated "
                "and will be removed in a future version. "
                "Use the STORK_INPUT_OPTIONS setting instead."
            )
            self.input_options["html_selector"] = settings.get("SEARCH_HTML_SELECTOR")
        if settings.get("SEARCH_MODE") and not settings.get("STORK_INPUT_OPTIONS"):
            logger.warning(
                f"SEARCH_MODE = {settings.get('SEARCH_MODE')} is deprecated "
                "and will be removed in a future version. "
                "Use the STORK_INPUT_OPTIONS setting instead."
            )
            self.input_options["base_directory"] = self.output_path
            if settings.get("SEARCH_MODE") == "source":
                self.input_options["base_directory"] = self.content

    def generate_output(self, writer):
        search_settings_path = Path(self.output_path) / "search.toml"

        self.generate_stork_settings(search_settings_path)

        # Build the search index
        build_log = self.build_search_index(search_settings_path)
        build_log = "".join(["Search plugin reported ", build_log])
        logger.error(build_log) if "error" in build_log else logger.debug(build_log)

    def build_search_index(self, search_settings_path: Path):
        if not which("stork"):
            raise Exception("Stork must be installed and available on $PATH.")
        try:
            output = subprocess.run(
                [
                    "stork",
                    "build",
                    "--input",
                    str(search_settings_path),
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

    def generate_stork_settings(self, search_settings_path: Path):
        self.input_options["files"] = self.get_input_files()

        search_settings = {"input": self.input_options}

        if self.output_options:
            search_settings["output"] = self.output_options

        # Write the search settings file to disk
        with search_settings_path.open("w") as fd:
            rtoml.dump(obj=search_settings, file=fd)

    def _index_output(self) -> bool:
        return self.input_options["base_directory"] == self.output_path

    def get_input_files(
        self,
    ) -> List[Dict]:
        pages = self.context["pages"] + self.context["articles"]

        for article in self.context["articles"]:
            pages += article.translations

        input_files = []
        # Generate list of articles and pages to index
        for page in pages:
            page_to_index = (
                page.save_as if self._index_output() else page.relative_source_path
            )
            # Escape double-quotation marks in the title
            title = striptags(page.title).replace('"', '\\"')
            input_files.append(
                {
                    "path": page_to_index,
                    "url": f"/{page.url}",
                    "title": f"{title}",
                }
            )

        # Generate list of *template* pages to index (if any)
        for tpage in self.tpages:
            tpage_to_index = self.tpages[tpage] if self._index_output() else tpage
            input_files.append(
                {"path": tpage_to_index, "url": self.tpages[tpage], "title": ""}
            )

        return input_files


def get_generators(generators):
    return SearchSettingsGenerator


def register():
    signals.get_generators.connect(get_generators)
