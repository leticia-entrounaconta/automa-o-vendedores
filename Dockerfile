FROM python:3.13-slim

ENV PYTHONUNBUFFERED=1 \
    DEBIAN_FRONTEND=noninteractive \
    DISPLAY=:99 \
    LANG=pt_BR.UTF-8 \
    LC_ALL=pt_BR.UTF-8 \
    TZ=America/Sao_Paulo \
    CHROME_BINARY=/usr/bin/google-chrome

SHELL ["bash", "-o", "pipefail", "-c"]

RUN apt-get update && \
    apt-get install -y --no-install-recommends \
        apt-transport-https \
        ca-certificates \
        curl \
        dumb-init \
        fluxbox \
        fonts-liberation \
        gnupg \
        locales \
        novnc \
        unzip \
        websockify \
        wget \
        x11vnc \
        xvfb \
        xdg-utils \
        tzdata \
        libasound2 \
        libatk-bridge2.0-0 \
        libatk1.0-0 \
        libcairo2 \
        libcups2 \
        libdbus-1-3 \
        libdrm2 \
        libexpat1 \
        libfontconfig1 \
        libgbm1 \
        libglib2.0-0 \
        libgtk-3-0 \
        libnspr4 \
        libnss3 \
        libpango-1.0-0 \
        libpangocairo-1.0-0 \
        libstdc++6 \
        libx11-6 \
        libx11-xcb1 \
        libxcb1 \
        libxcomposite1 \
        libxcursor1 \
        libxdamage1 \
        libxext6 \
        libxfixes3 \
        libxi6 \
        libxrandr2 \
        libxrender1 \
        libxss1 \
        libxtst6 && \
    echo "pt_BR.UTF-8 UTF-8" >> /etc/locale.gen && \
    locale-gen pt_BR.UTF-8 && \
    rm -rf /var/lib/apt/lists/*

RUN curl -fsSL https://dl.google.com/linux/linux_signing_key.pub | gpg --dearmor -o /usr/share/keyrings/google-linux.gpg && \
    echo "deb [arch=amd64 signed-by=/usr/share/keyrings/google-linux.gpg] http://dl.google.com/linux/chrome/deb/ stable main" > /etc/apt/sources.list.d/google-chrome.list && \
    apt-get update && \
    apt-get install -y --no-install-recommends google-chrome-stable && \
    rm -rf /var/lib/apt/lists/*

RUN useradd --create-home --shell /bin/bash app && \
    mkdir -p /app && \
    chown app:app /app

WORKDIR /app

COPY requirements.txt ./

RUN python -m pip install --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

COPY --chown=app:app app ./app
COPY --chown=app:app docker ./docker
COPY --chown=app:app README.md ./

RUN mkdir -p /app/logs && \
    chown -R app:app /app && \
    chmod +x docker/entrypoint.sh

USER app

EXPOSE 7900

ENTRYPOINT ["/usr/bin/dumb-init", "--", "/app/docker/entrypoint.sh"]
