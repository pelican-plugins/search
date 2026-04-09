CHANGELOG
=========

1.1.1 - 2026-04-09
------------------

- Write `search.toml` with UTF-8 encoding
- Support Python 3.13 & 3.14
- Drop Python 3.8 & 3.9 support

Contributed by [Justin Mayer](https://github.com/justinmayer) via [PR #41](https://github.com/pelican-plugins/search/pull/41/)


1.1.0 - 2023-04-12
------------------

* Add the ability to directly configure the underlying Stork search engine via new `STORK_INPUT_OPTIONS` and `STORK_OUTPUT_OPTIONS` settings.
* Address [#31](https://github.com/pelican-plugins/search/issues/31) by reverting [#23](https://github.com/pelican-plugins/search/issues/23) in favor of [#15](https://github.com/pelican-plugins/search/issues/15).

1.0.2 - 2023-02-09
------------------

Improve handling of quotation marks and other special characters in post titles.

1.0.1 - 2022-08-05
------------------

Fix incorrect search result URLs when searching from non-home pages

1.0.0 - 2021-11-16
------------------

Initial project release
