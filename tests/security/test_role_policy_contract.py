"""Static contract tests for backend role enforcement.

These tests intentionally avoid importing the application so the security CI can
run without production secrets, databases, or optional runtime dependencies.
"""
from __future__ import annotations

import ast
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
ADMIN = ROOT / "src" / "app" / "api" / "admin.py"
AUTH = ROOT / "src" / "app" / "core" / "auth.py"


def _tree(path: Path) -> ast.Module:
    return ast.parse(path.read_text(encoding="utf-8"), filename=str(path))


def _endpoint_functions(tree: ast.Module) -> list[ast.AsyncFunctionDef]:
    result = []
    for node in tree.body:
        if not isinstance(node, ast.AsyncFunctionDef):
            continue
        if any(
            isinstance(dec, ast.Call)
            and isinstance(dec.func, ast.Attribute)
            and isinstance(dec.func.value, ast.Name)
            and dec.func.value.id == "router"
            for dec in node.decorator_list
        ):
            result.append(node)
    return result


def _depends_names(node: ast.AsyncFunctionDef) -> set[str]:
    names: set[str] = set()
    for arg in node.args.args:
        default = None
        default_index = len(node.args.args) - len(node.args.defaults)
        if node.args.args.index(arg) >= default_index:
            default = node.args.defaults[node.args.args.index(arg) - default_index]
        if (
            isinstance(default, ast.Call)
            and isinstance(default.func, ast.Name)
            and default.func.id == "Depends"
            and default.args
            and isinstance(default.args[0], ast.Name)
        ):
            names.add(default.args[0].id)
    return names


def test_admin_endpoints_have_role_dependencies() -> None:
    tree = _tree(ADMIN)
    endpoints = _endpoint_functions(tree)
    assert endpoints, "admin.py must expose router endpoints"

    for endpoint in endpoints:
        deps = _depends_names(endpoint)
        # Every admin API endpoint must enforce either admin or moderator access.
        assert deps & {"require_admin", "require_moderator"}, (
            f"{endpoint.name} has no role dependency"
        )


def test_role_guards_are_strict_for_non_admin_users() -> None:
    source = AUTH.read_text(encoding="utf-8")
    admin_source = ADMIN.read_text(encoding="utf-8")

    assert "status_code=status.HTTP_401_UNAUTHORIZED" in source
    assert "if not current_user.is_admin:" in admin_source
    assert "if not current_user.is_admin and not current_user.is_moderator:" in admin_source
    assert "status_code=status.HTTP_403_FORBIDDEN" in admin_source


def test_admin_route_cannot_become_public_by_removing_dependency() -> None:
    tree = _tree(ADMIN)
    endpoints = _endpoint_functions(tree)
    assert all(_depends_names(endpoint) & {"require_admin", "require_moderator"} for endpoint in endpoints)
