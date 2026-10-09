# GitHub Profile Card

[Português](README.md) · [MIT License](LICENSE)

Three original SVG cards for **GitHub contributions, languages and streaks**. The visual uses familiar icons and aligned values for quick scanning, taking inspiration from cards such as [GitHub Readme Stats](https://github.com/anuraghazra/github-readme-stats); this project's SVGs, icons and code are original. This project powers [Guilherme Beserra's profile](https://github.com/GuiCodeLabs) and can be copied for your own profile.

<p align="center">
  <img src="profile/stats-en.svg" width="410" alt="Current-year GitHub contribution statistics" />
  <img src="profile/languages-en.svg" width="410" alt="Languages from configured accessible repositories" />
</p>
<p align="center">
  <picture>
    <source media="(max-width: 600px)" srcset="profile/rhythm-mobile-en.svg" />
    <img src="profile/rhythm-en.svg" width="840" alt="Contribution rhythm" />
  </picture>
</p>

The top card shows one current-year contribution total from GitHub's calendar, including anonymized private activity when enabled. The lower card keeps the all-time total and streaks. Commits remain a separate visible count. **Anonymous private contributions are not claimed to be private commits.** Repository content and names remain hidden.

The language card analyzes owned public repositories by default. To include selected private repositories, optionally add a fine-grained, read-only token with Metadata: read access as the `PRIVATE_REPOSITORIES_TOKEN` Actions secret. Only aggregate language names and byte counts are written to the generated cards; repository names and source code are not.

## Add them to your profile

1. Create a public copy of this repository. Edit `profile-card.json` with your username, display name and repositories to omit **from the language card only**.
2. Enable Actions and allow it to write to your main branch. The built-in `GITHUB_TOKEN` is sufficient for public data and anonymous private contribution totals. To include private repository languages, configure the optional `PRIVATE_REPOSITORIES_TOKEN` secret with a fine-grained, read-only token; see [the permission guide](docs/CUSTOMIZATION.md).
3. Embed the images from your copy of the repository:

```html
<p align="center">
  <img src="https://raw.githubusercontent.com/YOUR_USER/github-profile-card/main/profile/stats-en.svg" width="410" alt="GitHub activity" />
  <img src="https://raw.githubusercontent.com/YOUR_USER/github-profile-card/main/profile/languages-en.svg" width="410" alt="Repository languages" />
</p>
<p align="center">
  <picture>
    <source media="(max-width: 600px)" srcset="https://raw.githubusercontent.com/YOUR_USER/github-profile-card/main/profile/rhythm-mobile-en.svg" />
    <img src="https://raw.githubusercontent.com/YOUR_USER/github-profile-card/main/profile/rhythm-en.svg" width="840" alt="Contribution rhythm" />
  </picture>
</p>
```

Use filenames without a suffix for Portuguese or with `-es` for Spanish. The language of a README image cannot be automatically selected for each viewer. **Programming languages** are detected from owned public repositories by default and from selected private repositories when the optional token is configured.

## How it works

GitHub Actions tests pushes and pull requests. A separate scheduled job regenerates cards every **15 minutes**, subject to scheduling delays, and commits only changed metrics. The optional [live SVG endpoint](docs/CUSTOMIZATION.md#visitas-dentro-do-cartão) fetches a view count whenever it receives an origin request. Its `Cache-Control: no-cache` header asks GitHub's Camo image proxy to revalidate, while `no-store` bypasses Vercel caching. GitHub controls its proxy, so **one increment per page reload is not guaranteed**. A daily job refreshes the static fallback. CI cannot detect a reader's image reload.

See [metric definitions](docs/METRICS.md), [customization and troubleshooting](docs/CUSTOMIZATION.md), and [contribution guide](CONTRIBUTING.md). Runs on Python 3.11+ and Node.js 20+; the generator has no package dependencies.

```bash
python3 -m unittest discover -s tests -v
npm test
```
