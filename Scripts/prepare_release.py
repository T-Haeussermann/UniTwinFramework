import os
import shutil
from pathlib import Path

# Liste von zu ignorierenden Dateien/Ordnern
IGNORED = [
        ".git",
        "__pycache__",
        ".DS_Store",
        ".vscode",
        ".idea",
        "secrets.env",
        "Kubernetes",
        "Scripts/get_uuid_files.py",
        "venv"
    ]

# Ordner, in denen auch neue Dateien erlaubt sind (relativ zum src_dir)
ALLOWED_NEW_PATHS = [
        Path("DTPS"),
        Path("UniTwin/Chat"),
        Path("Chat-Model-Provider"),
        Path("UniTwin\Modules"),
        Path("Kubernetes\\04-ts-db_influxdb"),
        Path("Kubernetes\\04-ts-db_influxdb\\04-grafana-ingress.yaml"),
        Path("Kubernetes\\06-chat-model-provider\\02-chat-model-provider-k8-pvc.yaml"),
        Path("Scripts"),
        Path("DockerfileUniTwinStandalone")
    ]

def is_ignored(path: Path, base: Path) -> bool:
    rel_parts = path.relative_to(base).parts
    return any(part in IGNORED for part in rel_parts)

def is_under_allowed_new_path(path: Path, base: Path) -> bool:
    """Prüft, ob die Datei unter einem der erlaubten Ordner liegt."""
    try:
        rel = path.relative_to(base)
        return any(rel.parts[:len(allowed.parts)] == allowed.parts for allowed in ALLOWED_NEW_PATHS)
    except ValueError:
        return False

def prepare_release(src_dir, dst_dir):
    src_path = Path(src_dir)
    dst_path = Path(dst_dir)

    if not src_path.exists():
        print(f"❌ Quellverzeichnis existiert nicht: {src_path}")
        return
    if not dst_path.exists():
        print(f"❌ Zielverzeichnis existiert nicht: {dst_path}")
        return

    for root, dirs, files in os.walk(src_path):
        root_path = Path(root)

        # Verzeichnisse filtern (in-place!)
        dirs[:] = [d for d in dirs if not is_ignored(root_path / d, src_path)]

        for file in files:
            src_file = root_path / file
            if is_ignored(src_file, src_path):
                print(f"🚫 Ignoriert: {src_file.relative_to(src_path)}")
                continue

            rel_path = src_file.relative_to(src_path)
            dst_file = dst_path / rel_path

            # Nur kopieren, wenn Datei im Ziel existiert
            # oder sie in einem erlaubten "neue-Dateien-Ordner" liegt
            if not dst_file.exists() and not is_under_allowed_new_path(src_file, src_path):
                print(f"⏩ Übersprungen (nicht vorhanden im Ziel): {rel_path}")
                continue

            dst_file.parent.mkdir(parents=True, exist_ok=True)

            if not dst_file.exists() or src_file.stat().st_mtime > dst_file.stat().st_mtime:
                shutil.copy2(src_file, dst_file)
                print(f"✅ Kopiert: {rel_path}")
            else:
                print(f"⏩ Übersprungen (bereits aktuell): {rel_path}")


# Beispielpfade – bitte anpassen!
privates_repo = "C:\\Users\\Tim Häußermann\\Documents\\HSMannheim\\10-Projekte\\UniTwin\\Python"
oeffentliches_repo = "C:\\Users\\Tim Häußermann\\Documents\\HSMannheim\\10-Projekte\\UniTwin\\UniTwinFramework"

prepare_release(privates_repo, oeffentliches_repo)
