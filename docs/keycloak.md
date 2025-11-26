# Keycloak-Konfiguration und Logout-Fluss (StudyHelper)

Dieses Dokument fasst die Keycloak-Integration in diesem Projekt zusammen und beschreibt typische Stolpersteine – insbesondere, warum der Logout‑Button eventuell nicht wie erwartet wirkt.

## Architekturüberblick

- Keycloak 24 (Docker) stellt den IdP für OIDC bereit.
- oauth2-proxy (OIDC Provider) schützt die App, terminiert OIDC und setzt die Session‑Cookies.
- NiceGUI‑App läuft hinter oauth2-proxy als Upstream; optionale statische UI unter `web/`.
- Gemeinsames Docker‑Netz: `studyhelper-net`.

## Relevante Dateien

- Compose/Services: `docker-compose.yml`
- Realm‑Export (vorkonfiguriert): `keycloak/realm-export.json`
- Statische UI inkl. Logout‑Page: `web/index.html`, `web/logged-out.html`
- NiceGUI App (Logout‑Link + eigene Logout‑Seite): `nicegui_app.py`
- E2E‑Tests (Login/Logout): `e2e/tests/nicegui-auth.spec.ts`
- Veraltete Beispiel‑ENV und Setup‑Notizen: `.env.example`, `keycloak_setup.md`

## Keycloak (Service)

- Image/Version: `quay.io/keycloak/keycloak:24.0.5`
- Start: `start-dev --import-realm` (Realm wird aus JSON importiert)
- Ports: `8080:8080`
- Hostname/Proxy: `KC_HOSTNAME=localhost`, `KC_HOSTNAME_PORT=8080`, `KC_PROXY=edge`, `KC_HOSTNAME_STRICT=false`
- Admin‑Zugang (Dev): `KEYCLOAK_ADMIN=admin`, `KEYCLOAK_ADMIN_PASSWORD=admin`
- Realm‑Import: `./keycloak/realm-export.json -> /opt/keycloak/data/import/realm-export.json`

## Realm „studyhelper“ (Clients & Nutzer)

Auszug aus `keycloak/realm-export.json`:

- Client `oauth2-proxy` (confidential)
  - Redirect URIs: `http://localhost:8081/oauth2/callback`
  - Web Origins: `http://localhost:8081`
  - Attributes:
    - `pkce.code.challenge.method=S256`
    - `post.logout.redirect.uris=http://localhost:8081/*`
    - `frontchannel.logout=true`
- Client `nicegui-app` (confidential)
  - Redirect URIs: `http://localhost:8081/auth/callback`
  - Web Origins: `http://localhost:8081`
  - Attributes wie oben (PKCE, Post‑Logout, Frontchannel)
- Client `studyhelper-spa` (public)
  - Für reine SPA‑Flows; aktuell nicht aktiv benutzt (hinter Proxy nicht erforderlich)
- Testnutzer
  - `alice / alice` (aktiviert, Email verifiziert)

Hinweis: Für RP‑initiated Logout muss die `post.logout.redirect.uris` des verwendeten Clients exakt zur Ziel‑URL passen (siehe Abschnitt „Logout‑Fluss“).

## oauth2-proxy (Service)

Wichtigste Environment‑Variablen aus `docker-compose.yml`:

- Provider/Issuer: `OAUTH2_PROXY_PROVIDER=oidc`, `OAUTH2_PROXY_OIDC_ISSUER_URL=http://localhost:8080/realms/studyhelper`
- Discovery: `OAUTH2_PROXY_SKIP_OIDC_DISCOVERY=true` (Endpunkte werden manuell gesetzt)
- OIDC Endpunkte (Browser vs. intern):
  - Login (Browser): `OAUTH2_PROXY_LOGIN_URL=http://localhost:8080/.../auth`
  - Token/JWKS/UserInfo (intern, Container‑zu‑Container):
    - `OAUTH2_PROXY_REDEEM_URL=http://keycloak:8080/.../token`
    - `OAUTH2_PROXY_OIDC_JWKS_URL=http://keycloak:8080/.../certs`
    - `OAUTH2_PROXY_USERINFO_URL=http://keycloak:8080/.../userinfo`
- Logout (IdP):
  - `OAUTH2_PROXY_OIDC_END_SESSION_ENDPOINT=http://localhost:8080/.../logout`
  - Achtung: Je nach oauth2-proxy‑Version lautet die Option ggf. `OAUTH2_PROXY_OIDC_LOGOUT_URL`. Siehe „Stolpersteine“.
- Redirects/Whitelist: `OAUTH2_PROXY_REDIRECT_URL=http://localhost:8081/oauth2/callback`, `OAUTH2_PROXY_WHITELIST_DOMAINS=localhost:8081,.localhost:8081,localhost`
- Cookies: `OAUTH2_PROXY_COOKIE_SECRET`, `OAUTH2_PROXY_COOKIE_SECURE=false`
- Scope/PKCE: `OAUTH2_PROXY_SCOPE="openid email profile"`, `OAUTH2_PROXY_CODE_CHALLENGE_METHOD=S256`
- Upstream: `OAUTH2_PROXY_UPSTREAMS=http://nicegui:8081`
- Skip‑Auth‑Routes: `OAUTH2_PROXY_SKIP_AUTH_ROUTES='^/logged-out\.html$|^/favicon\.ico$'`

## App‑Integration und Logout‑Fluss

Variante A – statische UI `web/`:

- Logout‑Link: `href="/oauth2/sign_out?rd=/logged-out.html"`
- Zielseite `web/logged-out.html`:
  - Ruft Keycloak‑Logout an: `/protocol/openid-connect/logout?client_id=oauth2-proxy&post_logout_redirect_uri=http://localhost:8081/`
  - Danach Redirect zurück auf `/` (erneuter Login erforderlich)

Variante B – NiceGUI `nicegui_app.py`:

- Aktueller Logout‑Link: `'/oauth2/sign_out?rd=/'` (nur zurück zur Startseite)
- Eigene Seite `/logged-out.html` ist vorhanden und führt wie die statische Variante einen Keycloak‑Logout via JS aus.
  - Wird aber vom aktuellen Logout‑Link nicht benutzt.

E2E‑Test erwartet nach Logout eine erneute Login‑Aufforderung und prüft zusätzlich PKCE‑Unterstützung.

## Warum der Logout‑Button evtl. „nicht funktioniert“

- Falsches Ziel nach `sign_out`: In der NiceGUI‑App zeigt der Logout‑Link auf `rd=/` statt auf die Logout‑Seite. Dadurch wird zwar die Proxy‑Session gelöscht, aber die Keycloak‑SSO‑Session bleibt bestehen und der Nutzer ist beim nächsten Aufruf direkt wieder eingeloggt.
- IdP‑Logout‑Endpoint nicht korrekt konfiguriert: Bei deaktivierter Discovery (`SKIP_OIDC_DISCOVERY=true`) muss oauth2-proxy den Logout‑Endpoint kennen. Je nach Version heißt die Variable `OAUTH2_PROXY_OIDC_LOGOUT_URL` (nicht `...END_SESSION_ENDPOINT`). Falls die gesetzte Variable nicht erkannt wird, ruft oauth2-proxy kein IdP‑Logout auf.
- Post‑Logout‑Redirect nicht erlaubt: Die `post_logout_redirect_uri` muss exakt in `post.logout.redirect.uris` des verwendeten Clients (hier typischerweise `oauth2-proxy`) stehen. Ein Mismatch führt dazu, dass Keycloak nicht wie erwartet zurückleitet oder den Logout verweigert.
- Logout‑Seite nicht von Auth ausgenommen: Wenn `/logged-out.html` nicht in `OAUTH2_PROXY_SKIP_AUTH_ROUTES` enthalten wäre, könnte die Seite nicht ohne Session geladen werden und der JS‑Logout nie ausgeführt werden.
- Relative `rd`‑Redirects: Für einige OIDC‑Logout‑Flows wird eine absolute Redirect‑URL benötigt. Ein relatives `rd=/` verhindert ggf., dass `post_logout_redirect_uri` korrekt gesetzt werden kann.

## Empfohlene Fixes

- NiceGUI‑Logout‑Link anpassen: `'/oauth2/sign_out?rd=/logged-out.html'` verwenden, damit die IdP‑Abmeldung sicher ausgelöst wird.
- oauth2-proxy Logout‑Konfig prüfen: Falls Discovery aus bleibt, sicherstellen, dass die korrekte Variable für die verwendete Version gesetzt ist (ggf. `OAUTH2_PROXY_OIDC_LOGOUT_URL`). Alternativ Discovery aktivieren und `end_session_endpoint` automatisch übernehmen lassen.
- Post‑Logout‑Redirects verifizieren: In `keycloak/realm-export.json` sind `post.logout.redirect.uris` bereits auf `http://localhost:8081/*` gesetzt. Sicherstellen, dass die tatsächliche Ziel‑URL darunter fällt.
- Skip‑Auth‑Route beibehalten: `/logged-out.html` muss weiterhin ohne Auth erreichbar sein, damit der JS‑Logout unabhängig von der App‑Session ausgeführt wird.

## Hinweise zu veralteten Dateien

- `.env.example` und `keycloak_setup.md` stammen von einer früheren, nicht‑proxy‑basierten Variante (direkter App‑Login). Für den aktuellen Aufbau gelten primär die Docker‑Compose‑Settings und der Realm‑Export.

