# yt-mark-watched

Use webdriver to mark the watched position of youtube videos.

# Getting Started

Edit and copy `env-sample` to `.env`.

Run docker image or `app.py` directly:

```bash
docker-compose build
docker-compose up -d
```

# Endpoints

GET:/
```
Get status of webdriver and API.
```

POST:/api/cookies/update
```
Set youtube cookies. Content body must be a JSON stringified array.

[
    {name: 'COOKIE_NAME', value: 'COOKIE_VALUE'},
    ...
]
```

POST:/api/videos/mark-watched
```

Add new video to queue to be marked as watched at position specified in URL.

Example: set watched position to 60s

{url:'https://www.youtube.com/watch?v=y2NhcFrtrrY&t=60s'}
```