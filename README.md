# Inflation Monitor
Interactive U.S. inflation website: CPI/PCE headline/core, monthly and annual rates, and illustrative contribution analysis.

## Publish with GitHub Pages
Go to **Settings → Pages**, choose **Deploy from a branch**, select **main** and **/(root)**, then Save. The site should appear at https://jakejones2700-cmd.github.io/inflation-monitor/ once deployed.

## Update automation
The workflow at `.github/workflows/refresh.yml` runs on weekdays around 16:25 UTC. It retrieves BLS seasonally adjusted CPI headline/core index levels automatically. The BEA integration requires a free BEA API key stored as repository secret `BEA_API_KEY` (Settings → Secrets and variables → Actions). The workflow can be manually dispatched through the Actions tab.

**Limitations:** CPI category contributions for September 2026 are seed estimates, not official published attributions and are intentionally not copied into newer months. PCE data uploaded by the user are from BEA Table 2.8.7, which lacks expenditure weights; PCE contribution breakdowns cannot be computed from that table alone. PCE YoY rates from this table are compounded using rounded monthly changes, so may differ from BEA's official twelve-month figures. The updater's BEA table mapping is best-effort and must be checked against the first workflow log after an API key is configured. Core PCE mappings can vary by table revision. No assertion of historical correctness for computed PCE YoY until verified.

The site uses Chart.js from CDN, so Internet access is required for charts. Use the Export CSV button for inspection.
