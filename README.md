# everything
This program brings News-feeds, Podcasts, YouTube subscriptions and much more into one place.

### Disclaimer
This program is meant for use in private LANs only.   
Do NOT make this accessible to untrusted users.    
This program is not secure.

### Installation
```sh
python3 -m virtualenv venv
source ./venv/bin/activate
pip install -r requirements.txt
deactivate
```

Create a file `src/secrets.py` that contains the following variables:
- `YOUTUBE_API_KEY`

Maybe adjust the values in `src/conf.py` to your needs.

If you want to run this as a service enter the correct parameter for ExecStart
in `everything.service` and execute:  
```
cp everything.service /etc/systemd/system
sudo systemctl enable everything
sudo systemctl start everything
```

### Execution
Run it with
```sh
./src/everything.py
```

This will spawn a webserver on the specified address in `src/conf.py` (default 127.0.0.1:7070).

### TODO
- Twitter module
- News -> Feed
