# everything
This program brings News-feeds, Podcasts, YouTube subscriptions and much more into one place.

### Disclaimer
This program is meant for use in private LANs only.   
Do NOT make this accessible to untrusted users.    
This program is not secure.

### Installation
```sh
pip install -r requirements.txt
```

Create a file `src/secrets.py` that contains the following variables:
- `YOUTUBE_API_KEY`

Maybe adjust the values in `src/conf.py` to your needs.

### Execution
Run it with
```sh
./src/everything.py
```

This will spawn a webserver on the specified address in `src/conf.py` (default 127.0.0.1:7070).

### TODO
- Web interface for changing conf.json
- Twitter module
- Proper installation with virtualenv and systemd unit
- News -> Feed
