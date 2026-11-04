# Deploying leonross.me

The site deploys itself: every push to `main` runs `.github/workflows/deploy.yml`,
which builds the site and publishes it to GitHub Pages. You only need to do the
two one-time setups below.

## 1. GitHub Pages settings (one-time)

In the GitHub repository **leonross-blip/leonross.me**:

1. Go to **Settings → Pages**.
2. Under **Build and deployment → Source**, select **GitHub Actions**
   (not "Deploy from a branch").
3. Under **Custom domain**, enter `leonross.me` and click **Save**.
   GitHub will start a DNS check — it passes once the DNS records below are
   in place (can take up to an hour after you set them).
4. Once the DNS check passes, tick **Enforce HTTPS**. (The checkbox is greyed
   out until GitHub has provisioned the TLS certificate — check back after
   ~15 minutes.)

The repo already contains `public/CNAME` with `leonross.me`, so the custom
domain survives every deploy automatically.

## 2. DNS records at your registrar (one-time)

Add these records wherever you manage DNS for `leonross.me`:

**Apex domain (`leonross.me`) — four A records:**

| Type | Name | Value             |
| ---- | ---- | ----------------- |
| A    | `@`  | `185.199.108.153` |
| A    | `@`  | `185.199.109.153` |
| A    | `@`  | `185.199.110.153` |
| A    | `@`  | `185.199.111.153` |

**Optional but recommended — four AAAA records (IPv6):**

| Type | Name | Value                  |
| ---- | ---- | ---------------------- |
| AAAA | `@`  | `2606:50c0:8000::153`  |
| AAAA | `@`  | `2606:50c0:8001::153`  |
| AAAA | `@`  | `2606:50c0:8002::153`  |
| AAAA | `@`  | `2606:50c0:8003::153`  |

**`www` subdomain — one CNAME record:**

| Type  | Name  | Value                     |
| ----- | ----- | ------------------------- |
| CNAME | `www` | `leonross-blip.github.io` |

Leave TTLs at your registrar's default. Do **not** proxy these records through
a CDN (e.g. orange-cloud in Cloudflare) while GitHub is issuing the certificate.

## Verifying

- `dig leonross.me +short` should return the four A record IPs.
- `dig www.leonross.me +short` should return `leonross-blip.github.io.`
- After a push to `main`, the **Actions** tab shows the "Deploy to GitHub
  Pages" run; when it's green, https://leonross.me serves the new build.

## If a deploy fails

Open the failed run in the **Actions** tab. The build step runs a plain
`npm install && astro build`, so anything that fails there will also fail
locally with `npm run build` — reproduce and fix locally, then push again.
