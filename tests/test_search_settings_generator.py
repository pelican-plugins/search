import logging
from pathlib import Path

import pytest
from pytest_mock import MockerFixture

from pelican.plugins.search.search import SearchSettingsGenerator


class TestSearchSettingsGenerator:
    def test_search_html_selector_deprecation(self, caplog):
        test_settings = {"SEARCH_HTML_SELECTOR": "foo"}
        generator = SearchSettingsGenerator(
            context={},
            settings=test_settings,
            path=None,
            theme=None,
            output_path="output",
        )
        assert generator.input_options.get("html_selector") == "foo"
        assert "SEARCH_HTML_SELECTOR is deprecated" in caplog.text

    @pytest.mark.parametrize(
        "deprecated_option", ["SEARCH_HTML_SELECTOR", "SEARCH_MODE"]
    )
    def test_ignore_deprecated_options_if_new_var_available(
        self, caplog, deprecated_option
    ):
        test_settings = {
            deprecated_option: "foo",
            "STORK_INPUT_OPTIONS": {"foo": "bar"},
        }
        SearchSettingsGenerator(
            context={},
            settings=test_settings,
            path=None,
            theme=None,
            output_path="output",
        )
        assert f"{deprecated_option} is deprecated" not in caplog.text

    @pytest.mark.parametrize(
        "search_mode, base_directory", [("source", "content"), ("output", "output")]
    )
    def test_search_mode_deprecation(self, caplog, search_mode, base_directory):
        test_settings = {"SEARCH_MODE": search_mode, "PATH": "content"}
        generator = SearchSettingsGenerator(
            context={},
            settings=test_settings,
            path=None,
            theme=None,
            output_path="output",
        )
        assert generator.input_options.get("base_directory") == base_directory
        assert f"SEARCH_MODE = {search_mode} is deprecated" in caplog.text

    class TestGenerateOutput:
        def test_output_path(self, mocker: MockerFixture):
            generator = SearchSettingsGenerator(
                context={},
                settings={},
                path=None,
                theme=None,
                output_path="output",
            )
            generate_settings_mock = mocker.patch(
                "pelican.plugins.search.SearchSettingsGenerator.generate_stork_settings"
            )
            build_index_mock = mocker.patch(
                "pelican.plugins.search.SearchSettingsGenerator.build_search_index",
                return_value="",
            )
            generator.generate_output(writer=None)
            expected_search_path = Path("output") / "search.toml"
            generate_settings_mock.assert_called_once_with(expected_search_path)
            build_index_mock.assert_called_once_with(expected_search_path)

        def test_positive_logs(self, caplog, mocker: MockerFixture):
            generator = SearchSettingsGenerator(
                context={},
                settings={},
                path=None,
                theme=None,
                output_path="output",
            )
            mocker.patch(
                "pelican.plugins.search.SearchSettingsGenerator.generate_stork_settings"
            )
            mocker.patch(
                "pelican.plugins.search.SearchSettingsGenerator.build_search_index",
                return_value="foo bar",
            )
            with caplog.at_level(logging.DEBUG):
                generator.generate_output(writer=None)
                assert "Search plugin reported foo bar" in caplog.text
                for record in caplog.records:
                    assert record.levelname != "ERROR"

        def test_error_logs(self, caplog, mocker: MockerFixture):
            generator = SearchSettingsGenerator(
                context={},
                settings={},
                path=None,
                theme=None,
                output_path="output",
            )
            mocker.patch(
                "pelican.plugins.search.SearchSettingsGenerator.generate_stork_settings"
            )
            mocker.patch(
                "pelican.plugins.search.SearchSettingsGenerator.build_search_index",
                return_value="error bar",
            )
            with caplog.at_level(logging.DEBUG):
                generator.generate_output(writer=None)
                assert "Search plugin reported error bar" in caplog.text
                for record in caplog.records:
                    assert record.levelname == "ERROR"

    class TestBuildSearchIndex:
        @pytest.mark.skip("Skipped because mocking is not working")
        def test_raise_exception_if_stork_not_there(self, mocker: MockerFixture):
            # FIXME: This does not work. And I don;t have any other idea now.
            mocker.patch(
                "pelican.plugins.search.which",
                return_value=None,
            )

            with pytest.raises(
                Exception, match="Stork must be installed and available on \\$PATH."
            ):
                generator = SearchSettingsGenerator(
                    context={},
                    settings={},
                    path=None,
                    theme=None,
                    output_path="output",
                )
                generator.build_search_index(Path("output"))

    class TestGenerateStorkSettings:
        def test_output_options_set(self, mocker: MockerFixture):
            rtoml_patch = mocker.patch("pelican.plugins.search.rtoml.dump")
            mocker.patch(
                "pelican.plugins.search.SearchSettingsGenerator.get_input_files",
                return_value=[],
            )
            mocker.patch(
                "pathlib.Path.open",
            )
            generator = SearchSettingsGenerator(
                context={},
                settings={"STORK_OUTPUT_OPTIONS": {"debug": True}},
                path=None,
                theme=None,
                output_path="output",
            )
            generator.generate_stork_settings(Path("foo"))
            assert rtoml_patch.call_args.kwargs.get("obj").get("output") == {
                "debug": True
            }

        def test_output_options_not_set(self, mocker: MockerFixture):
            rtoml_patch = mocker.patch("pelican.plugins.search.rtoml.dump")
            mocker.patch(
                "pelican.plugins.search.SearchSettingsGenerator.get_input_files",
                return_value=[],
            )
            mocker.patch(
                "pathlib.Path.open",
            )
            generator = SearchSettingsGenerator(
                context={},
                settings={},
                path=None,
                theme=None,
                output_path="output",
            )
            generator.generate_stork_settings(Path("foo"))
            assert rtoml_patch.call_args.kwargs.get("obj").get("output") is None

        def test_files_added_to_input_options(self, mocker: MockerFixture):
            test_input_files = [
                {
                    "path": "content/foo.md",
                    "url": "https://blog.example.com/foo",
                    "title": "Foo",
                }
            ]
            mocker.patch(
                "pathlib.Path.open",
            )
            rtoml_patch = mocker.patch("pelican.plugins.search.rtoml.dump")
            mocker.patch(
                "pelican.plugins.search.SearchSettingsGenerator.get_input_files",
                return_value=test_input_files,
            )
            generator = SearchSettingsGenerator(
                context={},
                settings={},
                path=None,
                theme=None,
                output_path="output",
            )
            assert generator.input_options.get("files") is None
            generator.generate_stork_settings(Path("foo"))
            assert (
                rtoml_patch.call_args.kwargs.get("obj").get("input").get("files")
                == test_input_files
            )

    class TestGetInputFiles:
        class PageArticleMock:
            def __init__(self, title, translations=[]):
                self._title = title
                self._translations = translations

            @property
            def save_as(self):
                return "save_as"

            @property
            def relative_source_path(self):
                return "relative"

            @property
            def url(self):
                return "url"

            @property
            def title(self):
                return self._title

            @property
            def translations(self):
                return self._translations

        def test_path_is_save_as_on_index_output(self):
            generator = SearchSettingsGenerator(
                context={"pages": [self.PageArticleMock("title")], "articles": []},
                settings={"TEMPLATE_PAGES": []},
                path=None,
                theme=None,
                output_path="output",
            )
            assert generator.get_input_files() == [
                {
                    "path": "save_as",
                    "url": "/url",
                    "title": '"title"',
                }
            ]

        def test_path_is_realtive_on_index_source(self):
            generator = SearchSettingsGenerator(
                context={"pages": [self.PageArticleMock("title")], "articles": []},
                settings={
                    "TEMPLATE_PAGES": [],
                    "STORK_INPUT_OPTIONS": {"base_directory": "content"},
                },
                path=None,
                theme=None,
                output_path="output",
            )
            assert generator.get_input_files() == [
                {
                    "path": "relative",
                    "url": "/url",
                    "title": '"title"',
                }
            ]

        def test_articles_and_pages_are_collected(self):
            generator = SearchSettingsGenerator(
                context={
                    "pages": [self.PageArticleMock("page")],
                    "articles": [self.PageArticleMock("article")],
                },
                settings={
                    "TEMPLATE_PAGES": [],
                },
                path=None,
                theme=None,
                output_path="output",
            )
            assert generator.get_input_files() == [
                {
                    "path": "save_as",
                    "url": "/url",
                    "title": '"page"',
                },
                {
                    "path": "save_as",
                    "url": "/url",
                    "title": '"article"',
                },
            ]

        def test_translations_for_articles_are_collected(self):
            generator = SearchSettingsGenerator(
                context={
                    "pages": [],
                    "articles": [
                        self.PageArticleMock(
                            "article", translations=[self.PageArticleMock("article-fr")]
                        )
                    ],
                },
                settings={
                    "TEMPLATE_PAGES": [],
                },
                path=None,
                theme=None,
                output_path="output",
            )
            assert generator.get_input_files() == [
                {
                    "path": "save_as",
                    "url": "/url",
                    "title": '"article"',
                },
                {
                    "path": "save_as",
                    "url": "/url",
                    "title": '"article-fr"',
                },
            ]

        @pytest.mark.parametrize("is_output,expected", [(True, "dest"), (False, "src")])
        def test_template_pages_collected(
            self, mocker: MockerFixture, is_output: bool, expected: str
        ):
            mocker.patch(
                "pelican.plugins.search.SearchSettingsGenerator._index_output",
                return_value=is_output,
            )
            generator = SearchSettingsGenerator(
                context={
                    "pages": [],
                    "articles": [],
                },
                settings={
                    "TEMPLATE_PAGES": {
                        "src/books.html": "dest/books.html",
                        "src/resume.html": "dest/resume.html",
                    }
                },
                path=None,
                theme=None,
                output_path="output",
            )
            assert generator.get_input_files() == [
                {
                    "path": f"{expected}/books.html",
                    "url": "dest/books.html",
                    "title": "",
                },
                {
                    "path": f"{expected}/resume.html",
                    "url": "dest/resume.html",
                    "title": "",
                },
            ]
