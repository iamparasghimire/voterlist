# How to Push to GitHub

Since you have the code ready, follow these steps to upload it to GitHub so others can use it.

## 1. Create a Repository on GitHub
1. Go to [github.com](https://github.com) and sign in.
2. Click the **+** icon in the top right and select **New repository**.
3. Name it (e.g., `nepal-voter-list-scraper`).
4. Choose **Public**.
5. Do **not** check "Initialize with README" (since we already have one).
6. Click **Create repository**.

## 2. Push Code from Terminal
Open your terminal in VS Code (where you are now) and run the following commands one by one:

### Initialize Git (if not already done)
```bash
git init
```

### Add Files
```bash
git add .
```

### Commit Changes
```bash
git commit -m "Initial commit: Added scraping script for Bhaktapur and Lalitpur"
```

### Rename Branch (Optional, standard practice)
```bash
git branch -M main
```

### Add Remote Origin
*Replace `YOUR_USERNAME` with your actual GitHub username.*
```bash
git remote add origin https://github.com/YOUR_USERNAME/nepal-voter-list-scraper.git
```

### Push to GitHub
```bash
git push -u origin main
```

Note: If it asks for a password, you might need to use a [Personal Access Token](https://docs.github.com/en/authentication/keeping-your-account-and-data-secure/managing-your-personal-access-tokens) instead of your login password.

## 3. Share
Once pushed, anyone can visit `https://github.com/YOUR_USERNAME/nepal-voter-list-scraper` to see your code and read the `README.md` instructions.
