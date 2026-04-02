# GitHub Pages Setup

Follow these steps to publish the **what-the-shell** web app on GitHub Pages.

## Prerequisites

- You must be an owner or admin of the repository.

## Steps

### 1. Merge this branch into `main`

GitHub Pages is configured to deploy automatically on every push to `main`.
Merge (or fast-forward) this branch into `main` so the workflow file is present.

```bash
git checkout main
git merge --ff-only origin/copilot/create-simple-frontend-web-app
git push origin main
```

### 2. Enable GitHub Pages in repository settings

1. Go to your repository on GitHub.
2. Click **Settings** → **Pages** (left sidebar).
3. Under **Build and deployment**, set **Source** to **GitHub Actions**.
4. Click **Save**.

### 3. Trigger the first deployment

The workflow runs automatically on every push to `main`.  
After the merge in step 1, navigate to **Actions** → **Deploy to GitHub Pages**
to watch the run. When it finishes you'll see a green tick and the live URL.

Alternatively, trigger a manual run:

1. Go to **Actions** → **Deploy to GitHub Pages**.
2. Click **Run workflow** → **Run workflow**.

### 4. Visit your site

Once the workflow succeeds, your site is live at:

```
https://<your-github-username>.github.io/what-the-shell/
```

Replace `<your-github-username>` with your actual GitHub username (e.g., `DanBurton`).

---

## Re-deploying

Any future push to `main` will automatically trigger a new deployment.
No manual steps are required after initial setup.
