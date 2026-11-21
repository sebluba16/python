#!/usr/bin/env python3
"""Lit un fichier 3MF et affiche l'image (miniature) de l'objet qu'il contient.

Un fichier .3mf est une archive ZIP. L'image d'aperçu est référencée dans
`_rels/.rels` (relation de type "thumbnail"), le plus souvent sous
`Metadata/thumbnail.png`. À défaut, on cherche une image dans l'archive.

Usage :
    python show_3mf.py objet.3mf            # affiche l'image
    python show_3mf.py objet.3mf -o out.png # enregistre l'image au lieu de l'afficher
"""
import argparse
import io
import sys
import zipfile
import xml.etree.ElementTree as ET

from PIL import Image

IMAGE_EXT = (".png", ".jpg", ".jpeg")


def find_thumbnails(z: zipfile.ZipFile) -> list[str]:
    """Retourne les chemins d'images candidates, les plus probables d'abord."""
    names = z.namelist()
    found = []

    # 1) Relations déclarées dans _rels/.rels (norme 3MF)
    if "_rels/.rels" in names:
        root = ET.fromstring(z.read("_rels/.rels"))
        for rel in root.iter():
            if rel.tag.endswith("Relationship") and rel.get("Type", "").endswith("thumbnail"):
                target = rel.get("Target", "").lstrip("/")
                if target in names:
                    found.append(target)

    # 2) Repli : toute image de l'archive (Bambu/Prusa/Cura rangent dans Metadata/)
    others = [n for n in names if n.lower().endswith(IMAGE_EXT) and n not in found]
    others.sort(key=lambda n: ("thumbnail" not in n.lower(), "metadata" not in n.lower(), n))
    return found + others


def main() -> int:
    p = argparse.ArgumentParser(description="Affiche l'image contenue dans un fichier 3MF.")
    p.add_argument("fichier", help="chemin du fichier .3mf")
    p.add_argument("-o", "--output", help="enregistre l'image dans ce fichier au lieu de l'afficher")
    p.add_argument("-l", "--list", action="store_true", help="liste toutes les images trouvées")
    args = p.parse_args()

    try:
        z = zipfile.ZipFile(args.fichier)
    except (FileNotFoundError, zipfile.BadZipFile) as e:
        print(f"Erreur : impossible d'ouvrir {args.fichier} ({e})", file=sys.stderr)
        return 1

    with z:
        candidates = find_thumbnails(z)
        if args.list:
            print("\n".join(candidates) or "(aucune image)")
        if not candidates:
            print("Aucune image trouvée dans ce fichier 3MF.", file=sys.stderr)
            return 2
        img = Image.open(io.BytesIO(z.read(candidates[0])))
        img.load()

    print(f"Image : {candidates[0]} ({img.width}x{img.height})")
    if args.output:
        img.save(args.output)
        print(f"Enregistrée dans {args.output}")
    else:
        img.show()
    return 0


if __name__ == "__main__":
    sys.exit(main())
