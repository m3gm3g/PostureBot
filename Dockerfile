FROM python:3.13-slim

LABEL org.opencontainers.image.source="https://github.com/m3gm3g/PostureBot" \
      org.opencontainers.image.description="A tiny 8-bit terminal bot that reminds you to check your posture." \
      org.opencontainers.image.licenses="MIT"

ENV TERM=xterm-256color PYTHONUNBUFFERED=1
RUN useradd --create-home bot
USER bot
WORKDIR /home/bot
COPY --chown=bot posture_bot.py .
ENTRYPOINT ["python", "posture_bot.py"]
