# GitHub Actions Setup: Remote `make nice-key`

Anbei eine kurze Anleitung, wie du ein anderes Repository auf deinem Server so an GitHub Actions ankoppelst, dass bei jedem Push automatisch `make nice-key` ausgeführt wird.

## 1. Voraussetzungen

- Repository liegt auf GitHub (z. B. `user/remote-app`).
- Auf dem Zielserver existiert ein Linux‑User (z. B. `deploy`) mit Zugriff auf das Projektverzeichnis (`/srv/remote-app`), in dem `make nice-key` funktioniert.
- SSH-Zugriff vom GitHub Actions Runner zum Server ist möglich (Port 22 erreichbar).

## 2. Deploy-Key erzeugen

Auf deinem lokalen Rechner:

```bash
ssh-keygen -t ed25519 -f ~/.ssh/remote-app-gha -C "github-actions@remote-app"
```

- `~/.ssh/remote-app-gha` → privater Schlüssel (nicht weitergeben).
- `~/.ssh/remote-app-gha.pub` → öffentlichen Schlüssel in `~deploy/.ssh/authorized_keys` auf dem Server eintragen.

Auf GitHub (Repo → Settings → Secrets and variables → Actions → *New repository secret*):

- `DEPLOY_HOST`: `server.example.com`
- `DEPLOY_USER`: `deploy`
- `DEPLOY_PATH`: `/srv/remote-app`
- `DEPLOY_KEY`: Inhalt von `remote-app-gha` (privater Schlüssel, **inkl.** `-----BEGIN`/`END`).

## 3. Workflow-Datei anlegen

Erstelle im Repo `remote-app` die Datei `.github/workflows/deploy.yml`:

```yaml
name: Deploy remote-app

on:
  push:
    branches:
      - main

jobs:
  deploy:
    runs-on: ubuntu-latest

    steps:
      - uses: actions/checkout@v4

      - name: Install SSH key
        run: |
          mkdir -p ~/.ssh
          echo "$DEPLOY_KEY" > ~/.ssh/id_ed25519
          chmod 600 ~/.ssh/id_ed25519
          ssh-keyscan -H "$DEPLOY_HOST" >> ~/.ssh/known_hosts
        env:
          DEPLOY_KEY: ${{ secrets.DEPLOY_KEY }}
          DEPLOY_HOST: ${{ secrets.DEPLOY_HOST }}

      - name: Deploy via SSH
        env:
          DEPLOY_HOST: ${{ secrets.DEPLOY_HOST }}
          DEPLOY_USER: ${{ secrets.DEPLOY_USER }}
          DEPLOY_PATH: ${{ secrets.DEPLOY_PATH }}
        run: |
          ssh "$DEPLOY_USER@$DEPLOY_HOST" <<'EOF'
            set -euo pipefail
            cd "$DEPLOY_PATH"
            git fetch origin main
            git reset --hard origin/main
            make nice-key
          EOF
```

> **Hinweis:** Falls der Build sehr lange läuft, kannst du `timeout-minutes` auf Job- oder Step-Ebene erhöhen (Standard 360 min).

## 4. Sicherheit

- Account `deploy` sollte nur die minimal nötigen Rechte haben (kein `sudo`).
- Restriktiere den SSH-Key ggf. mit `command="..."` und `from="GitHub-Actions-IP"` in `authorized_keys`.
- Drehe den Key, wenn er kompromittiert sein könnte (`regen ssh-keygen`, Secret neu setzen).

## 5. Tests

1. Auf dem Server manuell `make nice-key` ausführen, um sicherzugehen, dass alle Abhängigkeiten stimmen.
2. Dummy-Commit auf `main` pushen → Actions → Job sollte grün durchlaufen; in den Logs siehst du `make nice-key`.
3. Prüfe die Anwendung auf dem Server.

Damit hast du ein simples Push‑Deploy eingerichtet: Jeder Push auf `main` sorgt dafür, dass GitHub Actions deinen Server aktualisiert und `make nice-key` ausführt. Bei Bedarf kannst du weitere Branches, manuelle Trigger (`workflow_dispatch`) oder Staging/Production-Targets ergänzen.
