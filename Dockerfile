FROM python:3.11-slim

# Libs système utiles pour beaucoup de libs Python/data/ML
RUN apt-get update && \
    apt-get install -y libnss3 libxss1 libasound2 libx11-xcb1 \
    libxcomposite1 libxcursor1 libxdamage1 libxi6 libxtst6 \
    libappindicator1 libxrandr2 libatk1.0-0 libatk-bridge2.0-0 \
    libgtk-3-0 libgbm1 libpango1.0-0 libxkbcommon0 libxshmfence1 \
    libx11-6 libxcb1 libxext6 libxfixes3 libxrender1 && \
    rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

ENV PORT=8080

# Ajoute toutes les ENV dont tu as vraiment besoin
ENV API_KEY=${API_KEY}
ENV API_SECRET=${API_SECRET}

EXPOSE 8080

CMD ["python", "src/backend/app.py"]
