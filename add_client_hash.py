import hashlib
import sys
import os

HASHES_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "allowed client hashes.txt")


def compute_hash(filepath):
    with open(filepath, "r", encoding="utf-8", errors="ignore") as f:
        content = f.read()
    normalized = content.replace("\r\n", "\n").replace("\r", "\n")
    lines = [line.rstrip() for line in normalized.split("\n")]
    normalized_content = "\n".join(lines).strip()
    return hashlib.sha256(normalized_content.encode("utf-8")).hexdigest()


def existing_hashes():
    hashes = set()
    if os.path.exists(HASHES_FILE):
        with open(HASHES_FILE, "r", encoding="utf-8") as f:
            for line in f:
                entry = line.strip()
                if entry and not entry.startswith("#"):
                    hashes.add(entry.split()[0])
    return hashes


def main():
    if len(sys.argv) < 3:
        print("Usage: python3 add_client_hash.py <client_file> <description>")
        print('Example: python3 add_client_hash.py "client code 2.py" "Release v1.0"')
        sys.exit(1)

    filepath = sys.argv[1]
    description = sys.argv[2]

    if not os.path.exists(filepath):
        print(f"Error: File not found: {filepath}")
        sys.exit(1)

    file_hash = compute_hash(filepath)
    print(f"Hash: {file_hash}")

    if file_hash in existing_hashes():
        print("This hash is already in allowed client hashes.txt")
        return

    with open(HASHES_FILE, "a", encoding="utf-8") as f:
        f.write(f"{file_hash} {description}\n")

    print(f"Added to allowed client hashes.txt: {description}")


if __name__ == "__main__":
    main()
