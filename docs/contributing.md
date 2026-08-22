# Contributing

Keep evaluation logic in `backend/app/evaluation`, transport concerns in the
application boundary, and presentation code in `frontend`. Add focused tests
under the directory matching the responsibility being changed. Preserve
contract-compatible Pydantic models and include evidence links in new
findings.

Before opening a change, run the backend test suite, backend compilation, and
frontend lint/build when frontend code is affected. Do not commit secrets,
local databases, generated caches, or dependency directories.
