# PvpBot Wiki

Documentation for PvpBot: installation, commands, selectors, every setting and the main features. The site is static
and GitHub Pages serves it as is.

## Layout

| Path | Contents |
|---|---|
| `content/*.html` | The wiki pages. These are what you edit. |
| `content/data/settings-schema.json` | PvpBot's settings: name, group, type, limits and default. |
| `content/data/settings-text.json` | The description shown for each setting. |
| `assets/` | Styles, the script (theme, menu, search) and the generated search index. |
| `build.py` | The generator. |
| `*.html` at the root | The generated pages GitHub Pages publishes. Don't edit them by hand. |

## Editing the wiki

1. Edit or add a page in `content/`. Every page starts with a header:

   ```
   ---
   title: Commands
   section: Reference
   order: 10
   icon: ⌨️
   lead: The sentence under the title.
   ---
   ```

   `section` is one of `Getting started`, `Reference`, `Features` and `Help`. `order` sets the position in the sidebar.
   Write `{{settings:combat}}` (or another group) to insert that group's settings table.
2. Rebuild the site (only Python 3 is needed, no libraries):

   ```
   python3 build.py
   ```

3. Commit both `content/` and the generated pages. If you rename or remove a page, delete its old generated `.html`
   at the root too.

When PvpBot gains a setting, add it to `settings-schema.json` and write its description in `settings-text.json`. If the
description is missing, the schema's short help text is used.

## Publishing

On GitHub: **Settings → Pages → Build and deployment → Source: Deploy from a branch**, branch `main`, folder
`/ (root)`. The `.nojekyll` file makes Pages serve the files as they are. The site is then at
https://nantag.github.io/Plugin-PvP-Bot-doc/.
