# backend/app/auth.py

def validate_token(headers):
    """
    Validates the X-Authorization header according to the ECE461 Phase 2 spec.

    This project does NOT require real JWT verification.
    It only requires:
      - Header must exist
      - Token must be non-empty
      - Token should start with "bearer "
      - Token should look like a JWT (3 parts separated by dots)

    Returns:
        True if token passes validation rules, otherwise False.
    """

    if not headers:
        return False

    token = headers.get("X-Authorization")
    if not token:
        return False

    token = token.strip()
    if len(token) == 0:
        return False

    # Must start with "bearer "
    if not token.lower().startswith("bearer "):
        return False

    jwt_part = token.split(" ", 1)[1]

    # Must look like a JWT: a.b.c
    if len(jwt_part.split(".")) != 3:
        return False

    return True


def require_auth(event):
    """
    Helper for Lambda handlers.
    Returns (is_valid, error_response) so handlers can do:

        valid, error = require_auth(event)
        if not valid:
            return error

    """

    headers = event.get("headers", {})
    if validate_token(headers):
        return True, None

    return False, {
        "statusCode": 403,
        "body": "Authentication failed due to invalid or missing AuthenticationToken.",
        "headers": {"Content-Type": "text/plain"}
    }
