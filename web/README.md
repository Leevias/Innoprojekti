# Lampun PI-säädön web-käyttöliittymä

Django-sovellus, joka ajetaan Linux-palvelimella samalla koneella kuin Mosquitto.
Se näyttää PLC:n lähettämän lämpötilan (`plc/pid/temp`) ja lähettää asetusarvon,
Kp:n ja Ki:n PLC:lle (`plc/pid/setpoint`, `plc/pid/kp`, `plc/pid/ki`).

Asetukset lähetetään retained-viesteinä: Mosquitto muistaa viimeisimmän arvon,
joten PLC saa sen heti uudelleenkäynnistyksen jälkeen ja käyttöliittymä näyttää
nykyiset arvot.

## Asennus palvelimelle

Polut olettavat, että repo on kloonattu kansioon `/home/leevias/Innoprojekti`.

```bash
sudo apt install python3-venv nginx
cd ~
git clone https://github.com/Leevias/Innoprojekti.git
cd Innoprojekti/web
python3 -m venv venv
venv/bin/pip install -r requirements.txt
```

### Pikatesti (kehityspalvelin, portti 8000)

```bash
sudo ufw allow 8000/tcp
venv/bin/python manage.py runserver 0.0.0.0:8000
```

Avaa selaimessa `http://<palvelimen-ip>:8000`. Lopeta Ctrl+C:llä ja sulje portti:
`sudo ufw delete allow 8000/tcp`.

### Pysyvä asennus (portti 80)

1. Vaihda `deploy/pid_ui.service`-tiedostoon oma `DJANGO_SECRET_KEY`. Satunnaisen
   avaimen saa komennolla `python3 -c "import secrets; print(secrets.token_urlsafe(50))"`.
2. Asenna gunicorn-palvelu:
   ```bash
   sudo cp deploy/pid_ui.service /etc/systemd/system/
   sudo systemctl daemon-reload
   sudo systemctl enable --now pid_ui
   ```
3. Asenna nginx-asetukset:
   ```bash
   sudo cp deploy/nginx_pid_ui.conf /etc/nginx/sites-available/pid_ui
   sudo ln -s /etc/nginx/sites-available/pid_ui /etc/nginx/sites-enabled/
   sudo rm /etc/nginx/sites-enabled/default
   sudo nginx -t && sudo systemctl reload nginx
   sudo ufw allow 80/tcp
   ```

Käyttöliittymä löytyy nyt osoitteesta `http://<palvelimen-ip>`.

## Päivitys

```bash
cd ~/Innoprojekti && git pull
sudo systemctl restart pid_ui
```

## Vianetsintä

- `sudo systemctl status pid_ui` ja `sudo journalctl -u pid_ui -n 50`: Djangon/gunicornin lokit.
- `mosquitto_sub -h localhost -t "plc/pid/#" -v`: tuleeko PLC:n data palvelimelle.
- Sallitut arvoalueet ja MQTT-aiheet ovat tiedostossa `pid_ui/settings.py`.
