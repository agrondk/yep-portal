from pathlib import Path

from app.modules.core.permissions import CORE_PERMISSIONS


def main() -> None:
    rows = ["# Permission matrix", "", "Generated from module permission declarations.", ""]
    rows.extend(["| Role | M00 permissions |", "| --- | --- |"])
    for role, permissions in CORE_PERMISSIONS.items():
        value = ", ".join(f"`{item}`" for item in sorted(permissions)) or "—"
        rows.append(f"| `{role.value}` | {value} |")
    path = Path(__file__).parents[3] / "docs" / "permission-matrix.md"
    path.write_text("\n".join(rows) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
