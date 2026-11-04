# EyD Clearing House (single-node v0.1.0) as a container.
# The production beta runs the same code under systemd behind Caddy
# (see deploy/README.md); this image is the portable way to run it.
#
#   docker build -t eyd-clearinghouse .
#   docker run -p 8787:8787 -e CH_STATE_FILE=/data/state.json \
#       -v eyd-data:/data eyd-clearinghouse
#   curl localhost:8787/        # service, version, ch_id, pubkey
FROM python:3.12-slim

WORKDIR /app
COPY . .

RUN pip install --no-cache-dir -e ".[clearinghouse]"

ENV HOST=0.0.0.0 PORT=8787
EXPOSE 8787

CMD ["python", "clearinghouse/main.py"]
