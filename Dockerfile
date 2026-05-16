# Build argument to control whether to include calibre-server (AIO mode)
ARG BUILD_TYPE=standard
# BUILD_TYPE can be: standard or aio

# Stage 1: Builder - To build dependencies
FROM python:3.12-slim-bookworm AS builder

ARG BUILD_TYPE

# Set the working directory
WORKDIR /app

# Install build tools and dependencies for ebook-converter
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
    build-essential \
    git \
    pkg-config \
    libxml2-dev \
    libxslt-dev \
    poppler-utils \
    zlib1g-dev \
    fonts-liberation \
    zip \
    fonts-wqy-microhei

# Create a non-root user for security
RUN useradd --create-home appuser
WORKDIR /home/appuser

# Create a virtual environment for building ebook-converter
RUN python -m venv /home/appuser/build_venv

# Install lxml and html5-parser from source first, then ebook-converter
RUN /home/appuser/build_venv/bin/pip install --no-binary lxml lxml html5-parser && \
    /home/appuser/build_venv/bin/pip install git+https://github.com/gryf/ebook-converter.git

# Create and activate a virtual environment for the app
RUN python -m venv /home/appuser/venv
ENV PATH="/home/appuser/venv/bin:$PATH"

# Copy only the requirements file to leverage Docker cache
COPY --chown=appuser:appuser requirements.txt .

# Upgrade pip and setuptools, then install dependencies
RUN /home/appuser/venv/bin/pip install --upgrade pip setuptools && \
    /home/appuser/venv/bin/pip install --no-cache-dir -r requirements.txt && \
    /home/appuser/venv/bin/pip install gunicorn

# Clone foliate-js repository
RUN git clone https://github.com/johnfactotum/foliate-js.git /home/appuser/foliate-js

# Stage 2: Final image - For running the application
FROM python:3.12-slim-bookworm

ARG BUILD_TYPE

# Install gosu for user switching, tini for signal handling, and runtime deps for ebook-converter
# For AIO mode, also install calibre
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
    gosu \
    tini \
    poppler-utils \
    fonts-liberation \
    zip \
    locales \
    libxslt1.1 \
    libxml2 \
    ffmpeg \
    fonts-wqy-microhei \
    $(if [ "$BUILD_TYPE" = "aio" ]; then echo "calibre curl"; fi) && \
    rm -rf /var/lib/apt/lists/*

# Configure locales
RUN sed -i -e 's/# en_US.UTF-8 UTF-8/en_US.UTF-8 UTF-8/' /etc/locale.gen && \
    sed -i -e 's/# zh_CN.UTF-8 UTF-8/zh_CN.UTF-8 UTF-8/' /etc/locale.gen && \
    sed -i -e 's/# zh_TW.UTF-8 UTF-8/zh_TW.UTF-8 UTF-8/' /etc/locale.gen && \
    dpkg-reconfigure --frontend=noninteractive locales

# Set environment variables for the application.
ENV LANG zh_CN.UTF-8
ENV LC_ALL zh_CN.UTF-8
ENV PORT=5000
ENV GUNICORN_WORKERS=2
# The following are placeholders and should be set securely at runtime
ENV SECRET_KEY=""
ENV CALIBRE_URL=""
ENV CALIBRE_USERNAME=""
ENV CALIBRE_PASSWORD=""
ENV CALIBRE_DEFAULT_LIBRARY_ID="Calibre_Library"
ENV CALIBRE_ADD_DUPLICATES="false"
ENV REQUIRE_INVITE_CODE="true"
ENV SMTP_SERVER=""
ENV SMTP_PORT=587
ENV SMTP_USERNAME=""
ENV SMTP_PASSWORD=""
ENV SMTP_ENCRYPTION="ssl"
ENV DEFAULT_TTS_SENTENCE_PAUSE=650
ENV DEFAULT_TTS_PARAGRAPH_PAUSE=900


# Create app user and standard directories as root
# For AIO mode, also create /Calibre Library directory for calibre-server
RUN useradd --uid 1001 --create-home appuser && \
    mkdir -p /config /webdav /audiobooks /tmp && \
    if [ "$BUILD_TYPE" = "aio" ]; then \
        mkdir -p "/Calibre Library" && \
        chown -R appuser:appuser "/Calibre Library"; \
    fi && \
    chown -R appuser:appuser /config /webdav /audiobooks /tmp

# Set working directory
WORKDIR /home/appuser

# Copy the virtual environments from builder stage
COPY --from=builder --chown=appuser:appuser /home/appuser/venv ./venv
COPY --from=builder --chown=appuser:appuser /home/appuser/build_venv ./build_venv
COPY --chown=appuser:appuser . .
COPY --from=builder --chown=appuser:appuser /home/appuser/foliate-js /home/appuser/static/js/foliate


# Extract, initialize all language files, populate English, auto-translate others, and compile.
RUN . venv/bin/activate && \
    #mkdir -p translations/en/LC_MESSAGES translations/zh_Hans/LC_MESSAGES translations/zh_Hant/LC_MESSAGES translations/es/LC_MESSAGES translations/fr/LC_MESSAGES translations/de/LC_MESSAGES && \
    #pybabel extract -F babel.cfg -o messages.pot . && \
    #pybabel init -i messages.pot -d translations -l en && \
    #pybabel init -i messages.pot -d translations -l zh_Hans && \
    #pybabel init -i messages.pot -d translations -l zh_Hant && \
    #pybabel init -i messages.pot -d translations -l es && \
    #pybabel init -i messages.pot -d translations -l fr && \
    #pybabel init -i messages.pot -d translations -l de && \
    python populate_en_po.py && \
    #python auto_translate.py zh_Hans zh_Hant es fr de && \
    pybabel compile -d translations

# Package the KOReader plugin into a zip file, preserving the top-level directory
RUN zip -r /home/appuser/static/anx-calibre-manager-koreader-plugin.zip anx-calibre-manager-koreader-plugin.koplugin

# Copy the entrypoint script
COPY --chown=appuser:appuser entrypoint.sh /usr/local/bin/entrypoint.sh
RUN chmod +x /usr/local/bin/entrypoint.sh

# Activate both virtual environments - build_venv first for ebook-converter
ENV PATH="/home/appuser/build_venv/bin:/home/appuser/venv/bin:$PATH"

# Expose the port the app runs on
EXPOSE $PORT

# Define volumes for persistent data
# For AIO mode, also add /Calibre Library volume
VOLUME ["/config", "/webdav", "/audiobooks"]

# Set the entrypoint to use tini for proper signal handling
ENTRYPOINT ["/usr/bin/tini", "--", "/usr/local/bin/entrypoint.sh"]

# Define the default command
# The --pid flag tells Gunicorn to write its master process ID to a file.
# This allows us to send signals (like SIGHUP for reloading) to it.
# Access logs are disabled. Error logs go to stderr (visible in `docker logs`).
# Application logs are saved to /config/logs/app.log and also output to stdout.
CMD gunicorn --bind [::]:$PORT --workers ${GUNICORN_WORKERS} --timeout 3600 --pid /tmp/gunicorn.pid --access-logfile /dev/null --error-logfile - --capture-output --enable-stdio-inheritance "app:create_app()"