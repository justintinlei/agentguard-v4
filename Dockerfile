# AgentGuard v4 - container image for the Streamlit remediation demo.
#
# Built and run in Day 9 Lab 7; wired into CI in Day 9 Lab 8. This file
# only describes the image; it contains no secret and no path to one.

# Match the local virtualenv (Python 3.14.6) so the container reproduces
# it exactly - that reproducibility is the whole point. "-slim" is a
# minimal Debian + Python with no build toolchain or docs: smaller image,
# smaller attack surface.
FROM python:3.14-slim

# Every application file lives under /app inside the container.
WORKDIR /app

# Copy ONLY the pinned dependency list first, install it, THEN copy the
# code. Docker caches each instruction as a layer, so editing app code
# reuses the (slow) pip-install layer instead of re-running it.
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

# Now the application. .dockerignore keeps .git, .venv, .env*, *.db,
# evidence/, notes/, ... out of this copy - no host junk, no credential.
COPY . .

# Run as a non-root user. If the containerised app is ever exploited, the
# attacker is an unprivileged account inside the container, not root.
# /app/data (where the Day 10 SQLite audit log will live) is made
# writable for that user.
RUN useradd --create-home --uid 10001 appuser \
 && mkdir -p /app/data \
 && chown -R appuser:appuser /app
USER appuser

# Streamlit's default port. This is documentation; compose.yaml does the
# actual host publishing.
EXPOSE 8501

# --server.address=0.0.0.0           accept connections from the host,
#                                    not just container-localhost
# --server.port=8501                 explicit, matches EXPOSE / compose
# --server.headless=true             no "open a browser" / e-mail prompt
# --browser.gatherUsageStats=false   no telemetry phone-home
CMD ["streamlit", "run", "app_v4.py", \
     "--server.address=0.0.0.0", \
     "--server.port=8501", \
     "--server.headless=true", \
     "--browser.gatherUsageStats=false"]
