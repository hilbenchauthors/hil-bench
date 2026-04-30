FROM python:3.11-slim
RUN mkdir -p /tmp/apt-dl/partial && apt-get update && apt-get install -y --no-install-recommends -o Dir::Cache::archives=/tmp/apt-dl sqlite3 curl tmux && rm -rf /tmp/apt-dl /var/lib/apt/lists/*
RUN pip install --no-cache-dir pandas
COPY mcp.py /usr/local/bin/mcp
RUN chmod +x /usr/local/bin/mcp
COPY setup_tools.py /tmp/setup_tools.py
RUN python3 /tmp/setup_tools.py && rm /tmp/setup_tools.py
WORKDIR /app
