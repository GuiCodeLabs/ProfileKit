# GitHub Profile Card

Original SVG cards for GitHub activity, programming languages and contribution streaks. This public MIT-licensed repository powers the [GuiCodeLabs profile](https://github.com/GuiCodeLabs) and can be copied for other users. [Documentação em português](README.md).

<p align="center"><img src="profile/stats-en.svg" width="520" alt="GitHub activity card" /></p>

## Use it for your profile

1. Copy this repository to your account and edit `profile-card.json`: `username`, `display_name`, `timezone`, and repositories excluded from **language stats only**.
2. Enable Actions and allow the workflow to write to the default branch. It uses the automatic repository-scoped `GITHUB_TOKEN`; no personal access token is needed.
3. Embed the cards from your copy of the repository. Put each image in a separate paragraph so it fills the available width on mobile.

```html
<p align="center"><img src="https://raw.githubusercontent.com/YOUR_USER/github-profile-card/main/profile/stats-en.svg" width="520" alt="GitHub activity" /></p>
<p align="center"><img src="https://raw.githubusercontent.com/YOUR_USER/github-profile-card/main/profile/languages-en.svg" width="520" alt="Repository languages" /></p>
<p align="center"><img src="https://raw.githubusercontent.com/YOUR_USER/github-profile-card/main/profile/rhythm-en.svg" width="520" alt="Contribution streaks" /></p>
```

Use the filenames without `-en` for Portuguese and with `-es` for Spanish. A GitHub README image cannot detect each viewer's locale reliably; choose the language in your Markdown. The **programming languages** themselves are detected automatically from the configured user's public repositories.

## Understand the counts

- **Calendar contributions** add GitHub's yearly contribution calendars. They include recognized public activity and, if the user opts in, anonymous private contribution counts. They are not all commits.
- **Public commits** add `totalCommitContributions` for the same years with the repository's automatic token. Private commits are not exposed or distinguished by type.
- **Stars** are received by public owned repositories. **Languages** are based on GitHub's byte counts in owned public repositories, excluding forks, archives and configured repository names. Percentages do not measure proficiency.
- **Streaks** use consecutive days of contribution-calendar activity. **Views** are requests reaching the Komarev badge service, not unique people.

The annual boundaries use the timezone in `profile-card.json`. The original SVG design and renderer code are in `scripts/generate_card.py`.

## Refresh rate and live views

GitHub Actions regenerates the static SVGs every 15 minutes, subject to GitHub's scheduling delays. It commits only when data changes. A daily run fetches the visitor badge for the static fallback; that request itself increments the service's counter.

For a more current view number **inside the same card**, deploy `api/card.js` to Vercel, set `PROFILE_REPOSITORY` to `YOUR_USER/github-profile-card` and `PROFILE_USER` to your username, then use:

```html
<img src="https://YOUR-DEPLOY.vercel.app/api/card?type=stats&amp;locale=en" width="520" alt="GitHub activity" />
```

The function reads the public generated SVG and refreshes the visit count on origin requests with a 60-second cache. GitHub's image proxy can cache longer, so a new count on **every** page reload is not guaranteed. Remove any separate pixel/badge for the same visitor service to avoid double counting. This repository's own README embeds the static card so its page views do not also count as profile views.

## Develop

Requires Python 3.11+ and Node.js 20+. No package dependencies for static generation.

```bash
python3 -m unittest discover -s tests -v
npm test
GITHUB_TOKEN=READ_ONLY_TOKEN python3 scripts/generate_card.py
```

Never commit a token. In Actions, `GITHUB_TOKEN` is supplied automatically. The optional `--refresh-visits` flag fetches and increments the visitor counter.

Contributions are welcome. [MIT License](LICENSE).
