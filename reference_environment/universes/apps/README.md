# Bharat universe apps

ARE app classes for the eight new apps of the Bharat universes: PaySetu,
RailMitra, SafarHub, KartBazaar, StyleGali, ThaliDash, SehatCare and DawaGhar.
The design, rules and verifier settings are specified in
[`../blr_pranjal_01/app_schemas.md`](../blr_pranjal_01/app_schemas.md).

Importing `reference_environment.universes.apps` registers every write tool
with ARE's verifier. PaySetu exposes `BharatProtocol.PAYMENT`, and ARE's
`Environment.register_apps` connects it to every paying app.

## Run the tests

The apps need ARE, so the tests run with the Python environment of the pinned
ARE checkout. From the `rlenv` workspace root:

```bash
omnilingual-gaia2-hindi/.venv/bin/python -m unittest discover \
  -s reference_environment/universes/apps/tests -t .
ruff check reference_environment/universes/apps
ruff format --check reference_environment/universes/apps
```
