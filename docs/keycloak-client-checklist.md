# Keycloak Client Checklist (Realm: roc)

- Realm: `roc` (Admin Console: `http://localhost:8080/admin`)
- Client used by oauth2-proxy: `oauth2-proxy` (confidential)
  - Access Type: Confidential (Client Authentication ON)
  - Redirect URIs: `http://localhost:8081/oauth2/callback`
  - Web Origins: `http://localhost:8081`
  - Valid Post Logout Redirect URIs:
    - `http://localhost:8081/logged-out.html`
    - Optional zusätzlich: `http://localhost:8081/*` (für lokale Tests)
  - Attributes:
    - `pkce.code.challenge.method = S256`
    - Optional: `frontchannel.logout = true`
- Test-User: anlegen oder Import nutzen (z. B. `alice/alice`).

Hinweise
- Exakte Übereinstimmung der `post_logout_redirect_uri` ist erforderlich (Protokoll, Host, Port, Pfad). Schon kleine Abweichungen verhindern die Weiterleitung.
- Wenn Discovery in oauth2-proxy deaktiviert ist, muss die Logout-URL entweder konfiguriert werden oder per `rd`-Redirect aufgerufen werden (hier genutzt).
