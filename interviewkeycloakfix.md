# Interview Keycloak Logout – Diagnose & Fix

Dieser Leitfaden fasst die Unterschiede zwischen deinem funktionierenden Setup (dieses Repo) und dem anderen System zusammen und liefert zielgerichtete Checks und Fixes für den Logout.

---

## Kurz-Zusammenfassung (wahrscheinlichste Ursache)
- Höchste Wahrscheinlichkeit: Inkonsequente URLs/Pfade (fehlendes/zusätzliches `/auth`) und fehlerhafte Whitelist des `post_logout_redirect_uri` im Keycloak‑Client.
- Indiz: Im Export steht `"post.logout.redirect.uris": "https://test.ki-interview.com/##https://test.ki-interview.com/*"` – das Format ist verdächtig. Keycloak erwartet korrekte, getrennte Einträge; fehlerhafte URIs führen dazu, dass Keycloak den Redirect blockt oder ignoriert.
- Häufig gekoppelt mit: gemischte Public/Internal URLs und fehlendes `id_token_hint` beim Logout.

Empfohlene Sofortmaßnahme: Einheitliche Basis‑URLs (inkl. `/auth`) verwenden und im Client „Valid Post Logout Redirect URIs“ exakt pflegen (z. B. `https://test.ki-interview.com` oder `https://test.ki-interview.com/*`). Optional `id_token_hint` mitsenden.

---

## Warum es hier funktioniert
- `oauth2-proxy` sitzt vor der App und übernimmt den OIDC‑Flow (Login/Logout, Cookies, Redirects):
  - Öffentliche Endpunkte sauber gesetzt (inkl. End‑Session).
  - Whitelist für absolute Redirects (`OAUTH2_PROXY_WHITELIST_DOMAINS`).
  - Logout führt per `rd=` zu einer öffentlichen Landing‑Page.
- App verwendet nur den Proxy‑Logout (`/oauth2/sign_out?rd=...`) und muss keine IdP‑Details korrekt zusammensetzen.

---

## Typische Ursachen im anderen System
1. URL-/Pfad‑Inkonsistenzen
   - Öffentlich: `https://test.ki-interview.com/auth`
   - Intern: `http://keycloak:8080` (mit `KC_HTTP_RELATIVE_PATH=/auth` → Endpunkte unter `/auth/...`).
   - Fehlerbilder: Endpunkte ohne `/auth`, doppelt `/auth`, falsche Discovery‑URL.

2. Post‑Logout‑Whitelisting
   - `Valid Post Logout Redirect URIs` nicht exakt gepflegt (Formatfehler, falsche Domain/Schema oder Pfad).

3. Logout‑Parameter
   - Fehlendes `id_token_hint`/`client_id` → Keycloak verweigert Redirect oder löscht Session nicht zuverlässig.

4. Reverse‑Proxy Headers
   - `X-Forwarded-Proto`/`Host` nicht korrekt gesetzt → Keycloak generiert falsche Links/Cookies.

5. Gemischte Redirect URIs / Origins
   - HTTP/HTTPS, alte Pfade (`/callback` vs `/auth/callback`) parallel → „mismatch“.

---

## Prüfliste (Step‑by‑Step)
1. Discovery prüfen (Browser/CLI)
   - `https://test.ki-interview.com/auth/realms/interview-designer/.well-known/openid-configuration`
   - Erwartet 200 + konsistente Endpunkte (alle unter `/auth/...`).

2. Client‑Einstellungen (Keycloak Admin UI)
   - „Valid Redirect URIs“: nur genutzte HTTPS‑URIs, z. B. `https://test.ki-interview.com/*`
   - „Valid Post Logout Redirect URIs“: `https://test.ki-interview.com` oder `https://test.ki-interview.com/*`
   - „Web origins“: `https://test.ki-interview.com`
   - Export-Feld korrigieren (kein `##`):
     - Beispiel: `"post.logout.redirect.uris": "https://test.ki-interview.com https://test.ki-interview.com/*"`

3. Nginx (Reverse Proxy) sicherstellen
   - Wichtige Header:
     - `proxy_set_header Host $host;`
     - `proxy_set_header X-Forwarded-Proto $scheme;`
     - `proxy_set_header X-Forwarded-Host $host;`
     - optional `proxy_set_header X-Forwarded-Port $server_port;`

4. App‑Konfiguration vereinheitlichen
   - Public (Browser): `KEYCLOAK_PUBLIC_URL=https://test.ki-interview.com/auth`
   - Intern (Container): `KEYCLOAK_INTERNAL_URL=http://keycloak:8080` (Endpoints unter `/auth/...` aufrufen)
   - Keine doppelte/fehlende `/auth`.

5. Logout‑URL testen
   - Minimal (ohne id_token_hint):
     - `https://test.ki-interview.com/auth/realms/interview-designer/protocol/openid-connect/logout?client_id=interview-designer-client&post_logout_redirect_uri=https%3A%2F%2Ftest.ki-interview.com`
   - Besser (mit id_token_hint):
     - `...&id_token_hint=<ID_TOKEN>`
   - Erwartung: 302 auf die Post‑Logout‑URL (kein 400). Keycloak‑Logs dabei beobachten.

6. Cookies/Sessions der App
   - Neben IdP‑Logout serverseitige App‑Session/Cookies löschen (SameSite/Secure passend zu HTTPS).

---

## Beispiel‑Konfigurationen

### Logout‑URL (Frontend)
```
https://test.ki-interview.com/auth/realms/interview-designer/protocol/openid-connect/logout
  ?client_id=interview-designer-client
  &post_logout_redirect_uri=https%3A%2F%2Ftest.ki-interview.com
  [&id_token_hint=<ID_TOKEN>]
```

### Nginx – wichtige Header
```
proxy_set_header Host $host;
proxy_set_header X-Real-IP $remote_addr;
proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
proxy_set_header X-Forwarded-Proto $scheme;
proxy_set_header X-Forwarded-Host $host;
# optional
proxy_set_header X-Forwarded-Port $server_port;
```

### Keycloak Client – minimale Felder
- Valid Redirect URIs: `https://test.ki-interview.com/*`
- Valid Post Logout Redirect URIs: `https://test.ki-interview.com` (oder `/*`)
- Web origins: `https://test.ki-interview.com`

---

## Unterschiede zum funktionierenden Setup (dieses Repo)
- Hier übernimmt `oauth2-proxy` den OIDC‑Flow, inkl. End‑Session‑Handling und Redirect‑Whitelist.
- Logout‑Link in der App geht an den Proxy: `/oauth2/sign_out?rd=<landing>` (siehe `nicegui_app.py`).
- Ergebnis: weniger Fehlerquellen in der App‑Logik.

---

## Empfohlene Fix‑Reihenfolge
1. Client‑URIs korrigieren (insb. `post_logout_redirect_uri`).
2. Alle URLs mit `/auth` konsistent setzen (Public + Intern + Discovery).
3. Reverse‑Proxy Header absichern.
4. Logout mit `client_id` + `post_logout_redirect_uri` testen; optional `id_token_hint` ergänzen.
5. Bei anhaltenden Problemen: `oauth2-proxy` vorschalten und über diesen ausloggen (reduziert Komplexität erheblich).

---

## Benötigte Zusatzinfos (falls weiterhin Fehler)
- Exakte Logout‑URL, die die App aufruft (ohne echte Tokens).
- Discovery‑URL in der App und deren Antwort.
- Aktuelle Client‑Einstellungen (Screenshots/Text) für Redirects/Post‑Logout‑Redirects/Web‑Origins.
- Vollständiger Nginx‑Serverblock für `/` und `/auth` inkl. Headers.
- Keycloak‑Logs während eines Logout‑Versuchs.

---

Stand: aktuell, basierend auf den bereitgestellten Konfigurationen und den funktionierenden Patterns aus diesem Repo.

