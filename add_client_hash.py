# add_client_hash.py
# ------------------------------------------------------------------
# PURPOSE:
#   Works out the "fingerprint" (a SHA-256 hash) of a client file and
#   adds it to "allowed client hashes.txt". The server reads that file
#   and only lets a client connect if its fingerprint is in the list.
#
#   This stops someone connecting with a modified/cheating version of
#   the client, because changing even one character changes the hash.
#
# HOW TO RUN IT (from the PyChat folder):
#   python add_client_hash.py "client code.py" "a short description"
#
#   The quotes matter because the filename has a space in it.
#
# MULTIPLE HASHES:
#   You can have as many hashes as you like in the txt file (one per
#   line). This script just adds one more line each time you run it,
#   and it will not add the same hash twice.
# ------------------------------------------------------------------

import hashlib   # gives us the SHA-256 hashing function
import sys       # lets us read the arguments typed after the filename
import os        # lets us work with file paths

# The full path to the list of approved hashes. We build it from the
# folder this script lives in, so it works no matter where you run it.
HASHES_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "allowed client hashes.txt")


def compute_hash(filepath):
    """Read a file and turn its contents into a single SHA-256 hash string.

    We "normalise" the text first so that tiny invisible differences
    (like Windows vs Mac line endings, or spaces at the end of a line)
    do NOT change the hash. That way the same code gives the same hash
    on any computer."""

    # Open the file and read everything into one big string.
    with open(filepath, "r", encoding="utf-8", errors="ignore") as f:
        content = f.read()

    # Make all line endings the same style (\n), so Windows/Mac/Linux match.
    normalized = content.replace("\r\n", "\n").replace("\r", "\n")

    # Remove any spaces/tabs at the end of each line.
    lines = [line.rstrip() for line in normalized.split("\n")]

    # Join the lines back together and trim blank lines at the start/end.
    normalized_content = "\n".join(lines).strip()

    # Turn the cleaned-up text into its SHA-256 fingerprint (a hex string).
    return hashlib.sha256(normalized_content.encode("utf-8")).hexdigest()


def existing_hashes():
    """Return a set of all hashes already listed in the txt file, so we
    can check whether the new one is already there."""

    hashes = set()

    # Only try to read the file if it actually exists yet.
    if os.path.exists(HASHES_FILE):
        with open(HASHES_FILE, "r", encoding="utf-8") as f:
            # Go through the file one line at a time.
            for line in f:
                entry = line.strip()
                # Skip blank lines and comment lines (starting with #).
                if entry and not entry.startswith("#"):
                    # Each line is "HASH description", so the hash is the
                    # first word. split()[0] grabs just that first word.
                    hashes.add(entry.split()[0])

    return hashes


def main():
    """The main routine: checks the arguments, computes the hash, and
    adds it to the file if it is new."""

    # sys.argv is the list of words typed on the command line.
    # [0] is the script name, [1] is the file, [2] is the description.
    # If the user did not give us both, show how to use it and stop.
    if len(sys.argv) < 3:
        print("Usage: python3 add_client_hash.py <client_file> <description>")
        print('Example: python3 add_client_hash.py "client code.py" "Release v2.0"')
        sys.exit(1)

    filepath = sys.argv[1]     # the client file to fingerprint
    description = sys.argv[2]  # a friendly label to remember what it is

    # Make sure the file they asked for actually exists.
    if not os.path.exists(filepath):
        print(f"Error: File not found: {filepath}")
        sys.exit(1)

    # Work out the fingerprint and show it on screen.
    file_hash = compute_hash(filepath)
    print(f"Hash: {file_hash}")

    # If this exact hash is already approved, there is nothing to do.
    if file_hash in existing_hashes():
        print("This hash is already in allowed client hashes.txt")
        return

    # Make sure we start on a fresh line: if the file exists and does not
    # already end with a newline, the hash would otherwise be glued onto
    # the last line (e.g. a comment), and the server would skip it.
    needs_newline = False
    if os.path.exists(HASHES_FILE) and os.path.getsize(HASHES_FILE) > 0:
        with open(HASHES_FILE, "rb") as f:
            f.seek(-1, os.SEEK_END)   # jump to the very last byte
            needs_newline = f.read(1) != b"\n"   # is it a newline or not?

    # Open the file in "append" mode ("a") so we ADD to the end instead of
    # overwriting. This is what lets you keep lots of hashes in the file.
    with open(HASHES_FILE, "a", encoding="utf-8") as f:
        if needs_newline:
            f.write("\n")   # finish off the previous line first
        # Write the new line in "HASH description" format.
        f.write(f"{file_hash} {description}\n")

    print(f"Added to allowed client hashes.txt: {description}")


# This line means: only run main() if this file is run directly,
# not if it is imported by another file.
if __name__ == "__main__":
    main()
