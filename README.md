# leonross.me

Personal site. Static [Astro](https://astro.build) build, all content in
Markdown and YAML, deployed to GitHub Pages automatically on every push to
`main` (see [DEPLOY.md](DEPLOY.md) for the one-time setup).

## Add a post (~1 minute)

1. Copy a template: `src/content/posts/_paper-template.md` or
   `src/content/posts/_company-template.md` (files starting with `_` are
   never published).
2. Save it as `src/content/posts/my-post.md` — the filename becomes the URL
   (`/writing/my-post/`).
3. Fill in the frontmatter: `title`, `date` (`YYYY-MM-DD`), `type` (`paper`
   or `company`), `summary`, `link`, `tags`. Extra keys (e.g. from Obsidian)
   are ignored and never break the build.
4. Write the body, commit, push to `main`. Done — it appears on `/writing/`,
   the home page, and the RSS feed.

## Publish from an Obsidian vault (~30 seconds)

```bash
python scripts/publish.py /path/to/vault        # add --dry-run to preview
```

Copies every vault note with `public: true` in its frontmatter into
`src/content/posts/`, mapping `created` → `date` and `type`/`domain` → the
post type (edit `TYPE_MAP` in the script to add domains), keeping `title`,
`summary`, `link` and `tags`, dropping everything else. `[[wikilinks]]`
become real links when the target is also public, plain text otherwise;
`> [!note]` callouts and `![[embeds]]` are stripped. Re-running is safe
(idempotent); it never deletes posts — remove unpublished ones by hand.
Tests: `python scripts/test_publish.py`.

## Update Now (~30 seconds)

Edit `src/content/now.md` (the three sections: Working on, Reading,
Looking for), commit, push. The "last updated" date is read from git
history at build time — there is no date field to maintain.

## Add a project (~30 seconds)

Add an entry to `src/content/projects.yaml`:

```yaml
- title: My project
  oneLiner: One sentence on what it is.
  github: https://github.com/leonross-blip/my-project # optional
  status: active
```

Commit, push. It appears as a card on `/projects/`.

## Other content

- **About page**: edit `src/content/about.md`.
- **CV**: overwrite `public/cv.pdf` with the real PDF (same filename).
- **Email, LinkedIn, GitHub, "Open to" line, analytics**: all in
  `src/site.config.ts` — the only config file.
- **Analytics**: off by default. To enable privacy-friendly analytics, set
  `goatCounterCode` in `src/site.config.ts` to your
  [GoatCounter](https://www.goatcounter.com) site code.

## Run locally

```bash
npm install
npm run dev        # dev server at http://localhost:4321
npm run build      # production build into dist/
npm run preview    # serve the production build locally
```

Requires Node 18.17+ (any current LTS works).

## Five things to check first

1. **Enable GitHub Pages**: Settings → Pages → Source: **GitHub Actions**,
   and set the custom domain to `leonross.me` (details in
   [DEPLOY.md](DEPLOY.md)).
2. **Set the DNS records** at your registrar — the A/AAAA records for the
   apex and the `www` CNAME listed in [DEPLOY.md](DEPLOY.md).
3. **Replace `public/cv.pdf`** — it is currently a one-line placeholder.
4. **Check `src/site.config.ts`** — confirm the email, LinkedIn and GitHub
   URLs and the "Open to" line are right, and add your GoatCounter code if
   you want analytics.
5. **Replace the two example posts** (`gears-perturbation-prediction.md`
   and `recursion-pharmaceuticals.md` in `src/content/posts/`) with your
   own writing, and update `src/content/now.md` and `src/content/about.md`
   so they say what you want them to say.
