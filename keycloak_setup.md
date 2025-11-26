# Keycloak Setup für NiceGUI Demo

## 1. Keycloak mit Docker starten

```bash
docker run -p 8080:8080 -e KEYCLOAK_ADMIN=admin -e KEYCLOAK_ADMIN_PASSWORD=admin quay.io/keycloak/keycloak:latest start-dev
```

## 2. Keycloak Admin Console öffnen

- URL: http://localhost:8080/admin
- Username: admin  
- Password: admin

## 3. Client konfigurieren

### 3.1 Neuen Client erstellen
1. Gehe zu "Clients" → "Create client"
2. Client ID: `nicegui-client`
3. Client type: `OpenID Connect`
4. Client authentication: `ON` (für Client Secret)

### 3.2 Client Settings
- Valid redirect URIs: `http://localhost:8080/callback`
- Valid post logout redirect URIs: `http://localhost:8080`
- Web origins: `http://localhost:8080`

### 3.3 Client Secret
1. Gehe zum "Credentials" Tab
2. Kopiere das "Client secret"
3. Trage es in die .env Datei ein

## 4. Test User erstellen

### 4.1 User hinzufügen
1. Gehe zu "Users" → "Add user"
2. Username: `testuser`
3. Email: `test@example.com`
4. First name: `Test`
5. Last name: `User`
6. Email verified: `ON`

### 4.2 Passwort setzen
1. Gehe zum "Credentials" Tab des Users
2. Setze ein Passwort (z.B. `password123`)
3. Temporary: `OFF`

## 5. App starten

```bash
# Virtual Environment aktivieren
source .venv/bin/activate  # Linux/Mac
# oder
.venv\Scripts\activate     # Windows

# Dependencies installieren
pip install -r requirements.txt

# Umgebungsvariablen setzen
cp .env.example .env
# Bearbeite .env und trage das Client Secret ein

# App starten
python nicegui_app.py
```

## 6. Testen

1. Öffne http://localhost:8080
2. Klicke auf "Mit Keycloak anmelden"
3. Melde dich mit `testuser` / `password123` an
4. Du solltest zum Dashboard weitergeleitet werden
5. Teste den "Logout" Button

## Troubleshooting

### Port-Konflikt
Falls Port 8080 bereits belegt ist:
- Ändere den Keycloak Port: `docker run -p 8081:8080 ...`
- Passe die URLs in .env entsprechend an
- Oder ändere den NiceGUI Port: `ui.run(port=3000)`

### CORS Fehler
- Stelle sicher, dass "Web origins" korrekt gesetzt ist
- Prüfe die Redirect URIs

### Client Secret Fehler
- Stelle sicher, dass "Client authentication" auf `ON` steht
- Kopiere das Secret aus dem "Credentials" Tab