# Full Keycloak Logout (NiceGUI behind oauth2-proxy)

## How to run

```bash
docker compose up --build
```

Services:
- Keycloak at `http://localhost:8080` (realm `roc`)
- App via oauth2-proxy at `http://localhost:8081`

## How to test

1. Open `http://localhost:8081/` → you should get redirected to Keycloak login.
2. Log in with your test user (e.g., `alice / alice`).
3. On the app, click “Logout”.
4. You will be redirected through oauth2-proxy to Keycloak’s end_session endpoint and then back to `http://localhost:8081/logged-out.html`.
5. Refresh `http://localhost:8081/` → you should be redirected to Keycloak login again (SSO session ended).

## What makes it work

- The Logout button links to `/oauth2/sign_out?rd=<idp_logout_url>`.
- `rd` points to Keycloak’s `end_session` URL with a valid `post_logout_redirect_uri` back to the app.
- `/logged-out.html` is publicly reachable via `OAUTH2_PROXY_SKIP_AUTH_ROUTES`.
- `OAUTH2_PROXY_WHITELIST_DOMAINS` includes `localhost:8080` (Keycloak) and `localhost:8081` (app) for absolute redirects.
- Keycloak client (`oauth2-proxy`) allows the exact `http://localhost:8081/logged-out.html` as a Valid Post Logout Redirect URI.

See also:
- `docker-compose.yml` (oauth2-proxy env)
- `nicegui_app.py` (Logout link and logged-out page)
- `docs/keycloak-client-checklist.md`
