# GitHub Profile Card

[Português](README.md) · [MIT License](LICENSE)

Three original SVG cards for **GitHub contributions, languages and streaks**. This project powers [Guilherme Beserra's profile](https://github.com/GuiCodeLabs) and can be copied for your own profile.

<p align="center">
  <img src="profile/stats-en.svg" width="410" alt="GitHub statistics" />
  <img src="profile/languages-en.svg" width="410" alt="Repository languages" />
</p>
<p align="center">
  <picture>
    <source media="(max-width: 600px)" srcset="profile/rhythm-mobile-en.svg" />
    <img src="profile/rhythm-en.svg" width="840" alt="Contribution rhythm" />
  </picture>
</p>

The cards show all calendar contributions (including anonymous private counts when enabled), yearly contributions, visible commits, stars, PRs, issues, profile views, code languages and streaks. **Anonymous private contributions are not claimed to be private commits.** Repository content and names remain hidden.

## Add them to your profile

1. Create a public copy of this repository. Edit `profile-card.json` with your username, display name and repositories to omit **from the language card only**.
2. Enable Actions and allow it to write to your main branch. The built-in `GITHUB_TOKEN` is sufficient; no personal access token is required.
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

Use filenames without a suffix for Portuguese or with `-es` for Spanish. The language of a README image cannot be automatically selected for each viewer; the **programming languages** are detected from your public owned repositories.

## How it works

GitHub Actions regenerates the cards every **15 minutes**, subject to scheduling delays, and commits only changed metrics. The optional [live SVG endpoint](docs/CUSTOMIZATION.md#visitas-dentro-do-cartão) fetches a new view count whenever it receives an origin request. GitHub's image proxy can still cache images, so **one increment per page reload is not guaranteed**. A daily job refreshes the static fallback.

See [metric definitions](docs/METRICS.md), [customization and troubleshooting](docs/CUSTOMIZATION.md), and [contribution guide](CONTRIBUTING.md). Runs on Python 3.11+ and Node.js 20+; the generator has no package dependencies.

```bash
python3 -m unittest discover -s tests -v
npm test
```
