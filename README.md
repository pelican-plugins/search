# Search: A Plugin for Pelican

[![Build Status](https://img.shields.io/github/actions/workflow/status/pelican-plugins/search/main.yml?branch=main)](https://github.com/pelican-plugins/search/actions)
[![PyPI Version](https://img.shields.io/pypi/v/pelican-search)](https://pypi.org/project/pelican-search/)

This plugin generates an index for searching content on a Pelican-powered site.


## Why would you want this?

Static sites are, well, static… and thus usually don’t have an application server component that could be used to power site search functionality. Rather than give up control (and privacy) to third-party search engine corporations, this plugin adds elegant and self-hosted site search capability to your site. Last but not least, searches are **really** fast. 🚀

Want to see just _how_ fast? Try it out for yourself. Following are some sites that use this plugin:

* [Justin Mayer](https://justinmayer.com)
* [Open Source Alternatives](https://opensourcealternatives.org)


## Installation

This plugin uses [Stork](https://stork-search.net/) to generate a search index. Follow the [Stork installation instructions](https://stork-search.net/docs/install) to install this required command-line tool and ensure it is available within `/usr/local/bin/` or another `$PATH`-accessible location of your choosing. For example, Stork can be installed on macOS (Intel) via:

    export STORKVERSION="v1.5.0"
    wget -O /usr/local/bin/stork https://files.stork-search.net/releases/$STORKVERSION/stork-macos-10-15
    chmod +x /usr/local/bin/stork

For macOS on ARM, install via Homebrew:

    brew install stork-search/stork-tap/stork

Confirm that Stork is properly installed via:

    stork --help

Once Stork has been successfully installed and tested, this plugin can be installed via:

    python -m pip install pelican-search

If you are using Pelican 4.5+ with namespace plugins and don’t have a `PLUGINS` setting defined in your configuration, then the Search plugin should be auto-discovered with no further action required. If, on the other hand, you _do_ have a `PLUGINS` setting defined (because you also use legacy plugins or because you want to be able to selectively disable installed plugins), then you must manually add `search` to the `PLUGINS` list, as described in the [Pelican plugins documentation][].


## Settings

This plugin’s behavior can be customized via Pelican settings. Those settings, and their default values, follow below.

### `SEARCH_MODE = "output"`

In addition to plain-text files, Stork can recognize and index HTML and Markdown-formatted content. The default behavior of this plugin is to index generated HTML files, since Stork is good at extracting content from tags, scripts, and styles. But that mode may require a slight theme modification that isn’t necessary when indexing Markdown source (see `SEARCH_HTML_SELECTOR` setting below). That said, indexing Markdown means that markup information may not be removed from the indexed content and will thus be visible in the search preview results. With that caveat aside, if you want to index Markdown source content files instead of the generated HTML output, you can use: `SEARCH_MODE = "source"`

### `SEARCH_HTML_SELECTOR = "main"`

By default, Stork looks for `<main>[…]</main>` tags to determine where your main content is located. If such tags do not already exist in your theme’s template files, you can either (1) add `<main>` tags or (2) change the HTML selector that Stork should look for.

To use the default `main` selector, in each of your theme’s relevant template files, wrap the content you want to index with `<main>` tags. For example:

`article.html`:

```jinja
<main>
{{ article.content }}
</main>
```

`page.html`:

```jinja
<main>
{{ page.content }}
</main>

```

For more information, refer to [Stork’s documentation on HTML tag selection](https://stork-search.net/docs/html).


## Static Assets

There are two options for serving the necessary JavaScript, WebAssembly, and CSS static assets:

1. Use a content delivery network (CDN) to serve Stork’s static assets
2. Self-host the Stork static assets

The first option is easier to set up. The second option is provided for folks who prefer to self-host everything. After you have decided which option you prefer, follow the relevant section’s instructions below.

### Static Assets — Option 1: Use CDN

#### CSS

Add the Stork CSS before the closing `</head>` tag in your theme’s base template file, such as `base.html`:

```html
<link rel="stylesheet" href="https://files.stork-search.net/basic.css" />
```

If your theme supports dark mode, you may want to also add Stork’s dark CSS file:

```html
<link rel="stylesheet" media="screen and (prefers-color-scheme: dark)" href="https://files.stork-search.net/dark.css">
```

#### JavaScript

Add the following script tags to your theme’s base template, just before your closing `</body>` tag, which will load the most recent Stork module along with the matching WASM binary:

```html
<script src="https://files.stork-search.net/releases/v1.5.0/stork.js"></script>
<script>
    stork.register("sitesearch", "{{ SITEURL }}/search-index.st")
</script>
```

### Static Assets — Option 2: Self-Host

Download the Stork JavaScript, WebAssembly, and CSS files and put them in your theme’s respective static asset directories:

```shell
export STORKVERSION="v1.5.0"
cd $YOUR-THEME-DIR
mkdir -p static/{js,css}
wget -O static/js/stork.js https://files.stork-search.net/releases/$STORKVERSION/stork.js
wget -O static/js/stork.js.map https://files.stork-search.net/releases/$STORKVERSION/stork.js.map
wget -O static/js/stork.wasm https://files.stork-search.net/releases/$STORKVERSION/stork.wasm
wget -O static/css/stork.css https://files.stork-search.net/basic.css
wget -O static/css/stork-dark.css https://files.stork-search.net/dark.css
```

#### CSS

Add the Stork CSS before the closing `</head>` tag in your theme’s base template file, such as `base.html`:

```jinja
<link rel="stylesheet" href="{{ SITEURL }}/{{ THEME_STATIC_DIR }}/css/stork.css">
```

If your theme supports dark mode, you may want to also add Stork’s dark CSS file:

```jinja
<link rel="stylesheet" media="screen and (prefers-color-scheme: dark)" href="{{ SITEURL }}/{{ THEME_STATIC_DIR }}/css/stork-dark.css">
```

#### JavaScript & WebAssembly

Add the following script tags to your theme’s base template file, such as `base.html`, just before the closing `</body>` tag:

```jinja
<script src="{{ SITEURL }}/{{ THEME_STATIC_DIR }}/js/stork.js"></script>
<script>
    stork.initialize("{{ SITEURL }}/{{ THEME_STATIC_DIR }}/js/stork.wasm")
    stork.downloadIndex("sitesearch", "{{ SITEURL }}/search-index.st")
    stork.attach("sitesearch")
</script>
```

### Search Input Form

Decide in which place(s) on your site you want to put your search field, such as your `index.html` template file. Then add the search field to the template:

```html
Search: <input data-stork="sitesearch" />
<div data-stork="sitesearch-output"></div>
```

For more information regarding this topic, see the [Stork search interface documentation](https://stork-search.net/docs/interface).


## Deployment

Ensure your production web server serves the WebAssembly file with the `application/wasm` MIME type. For folks using older versions of Nginx, that might look like the following:

```nginx
…
http {
    …
    include             mime.types;
    # Types not included in older Nginx versions:
    types {
        application/wasm                                 wasm;
    }
    …
}
```

For other self-hosting considerations, see the [Stork self-hosting documentation](https://stork-search.net/docs/self-hosting).


## Contributing

Contributions are welcome and much appreciated. Every little bit helps. You can contribute by improving the documentation, adding missing features, and fixing bugs. You can also help out by reviewing and commenting on [existing issues][].

To start contributing to this plugin, review the [Contributing to Pelican][] documentation, beginning with the **Contributing Code** section.

[Pelican plugins documentation]: https://docs.getpelican.com/en/latest/plugins.html
[existing issues]: https://github.com/pelican-plugins/search/issues
[Contributing to Pelican]: https://docs.getpelican.com/en/latest/contribute.html
