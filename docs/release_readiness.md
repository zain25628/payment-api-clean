# Release Readiness Checklist

## Automated Checks

- Run tests:

  Command: `pytest -q`

### Pytest Output

```
............................................................................. [ 76%]
........................                                                      [100%]
================================= warnings summary ================================= 
tests/test_full_payment_flow.py: 3 warnings
tests/test_payment_service.py: 4 warnings
tests/test_payments_router.py: 3 warnings
  C:\Users\zaink\OneDrive\Desktop\api\app\services\payment_service.py:31: Deprecation
Warning: datetime.datetime.utcnow() is deprecated and scheduled for removal in a future version. Use timezone-aware objects to represent datetimes in UTC: datetime.datetime.now(datetime.UTC).                                                                    cutoff = datetime.utcnow() - timedelta(minutes=max_age)

tests/test_full_payment_flow.py::test_full_flow_happy_path
tests/test_payment_service.py::test_confirm_payment_happy_path_and_idempotent        
tests/test_payments_router.py::test_payments_confirm_endpoint_happy_path_and_idempote
nt                                                                                     C:\Users\zaink\OneDrive\Desktop\api\app\services\payment_service.py:127: Deprecatio
nWarning: datetime.datetime.utcnow() is deprecated and scheduled for removal in a future version. Use timezone-aware objects to represent datetimes in UTC: datetime.datetime.now(datetime.UTC).                                                                   payment.used_at = datetime.utcnow()

tests/test_full_payment_flow.py::test_check_not_found_for_old_payment
  C:\Users\zaink\OneDrive\Desktop\api\tests\test_full_payment_flow.py:222: Deprecatio
nWarning: datetime.datetime.utcnow() is deprecated and scheduled for removal in a future version. Use timezone-aware objects to represent datetimes in UTC: datetime.datetime.now(datetime.UTC).                                                                   old_time = datetime.utcnow() - timedelta(hours=2)

-- Docs: https://docs.pytest.org/en/stable/how-to/capture-warnings.html
101 passed, 19 warnings in 1.71s
```

## Docker & Runtime

- Validate Docker Compose config:

  Command: `docker-compose config`

### docker-compose config Output

```
docker-compose : The term 'docker-compose' is not recognized as the name of a 
cmdlet, function, script file, or operable program. Check the spelling of the name,  
or if a path was included, verify that the path is correct and try again.
At line:1 char:1
+ docker-compose config
+ ~~~~~~~~~~~~~~
    + CategoryInfo          : ObjectNotFound: (docker-compose:String) [], CommandNo  
   tFoundException
    + FullyQualifiedErrorId : CommandNotFoundException

```

## Summary

- Pytest: All tests passed (`101 passed, 19 warnings`).
- docker-compose: `docker-compose` is not available in the environment where the checks were run (command not found). Please ensure Docker and docker-compose (or the Docker Compose v2 plugin) are installed and available on PATH to validate the compose configuration.

## Production Notes

- Backend application code is functionally ready for production use: all automated tests are passing (`101 passed`).
- There are `DeprecationWarning` messages related to `datetime.utcnow()`. These should be addressed in a future refactor by moving to timezone-aware datetimes (e.g. `datetime.now(datetime.UTC)`), but they are not blocking for an initial MVP release.
- Docker/Docker Compose are not available in the current local environment (`docker-compose` command not found). On the target production environment:
  - Install Docker Engine and Docker Compose (v2 plugin or `docker compose` CLI).
  - Validate the stack with `docker compose config` and a test deployment.
- Before going live, make sure:
  - All required environment variables are configured (database URL, secrets, external services).
  - Database migrations are applied using Alembic.
  - Logging and basic monitoring are enabled.
