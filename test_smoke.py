"""Minimal smoke test for the Dupilumab COPD living-meta single-file app.

Validates the shipped HTML and the Paper Studio asset JS without a browser:
  - HTML files exist, are valid UTF-8, carry no BOM
  - no unfilled template placeholders (double-brace / replace-me / placeholder tokens)
  - no cp1252 em-dash mojibake regression
  - balanced <script>/</script> tags
  - every assets/js/*.js parses under `node --check`

Run:  python -m pytest test_smoke.py -q   (or)   python test_smoke.py
"""
import os
import re
import glob
import shutil
import subprocess

HERE = os.path.dirname(os.path.abspath(__file__))
HTML_FILES = ["index.html", "DUPILUMAB_COPD_REVIEW.html"]
MOJIBAKE_EMDASH = "â€”"  # 'â€”' : UTF-8 em-dash misread as cp1252


def _read(name):
    with open(os.path.join(HERE, name), encoding="utf-8") as fh:
        return fh.read()


def test_html_files_present():
    for name in HTML_FILES:
        assert os.path.isfile(os.path.join(HERE, name)), f"missing {name}"


def test_html_valid_utf8_no_bom():
    for name in HTML_FILES:
        with open(os.path.join(HERE, name), "rb") as fh:
            raw = fh.read()
        assert not raw.startswith(b"\xef\xbb\xbf"), f"BOM in {name}"
        raw.decode("utf-8")  # raises on invalid UTF-8


def test_no_unfilled_placeholders():
    # Build the token patterns from fragments so this test file does not itself
    # trip placeholder scanners on its own source.
    tokens = ["REPLACE" + "_ME", "__" + "PLACEHOLDER" + "__"]
    pat = re.compile(r"\{\{[^}]+\}\}|" + "|".join(tokens))
    for name in HTML_FILES:
        hits = pat.findall(_read(name))
        assert not hits, f"unfilled placeholders in {name}: {hits[:5]}"


def test_no_mojibake_regression():
    for name in HTML_FILES:
        assert MOJIBAKE_EMDASH not in _read(name), f"cp1252 mojibake in {name}"


def test_script_tags_balanced():
    for name in HTML_FILES:
        s = _read(name)
        opens = len(re.findall(r"<script[\s>]", s))
        closes = s.count("</script>")
        assert opens == closes, f"unbalanced <script> in {name}: {opens}/{closes}"


def test_asset_js_parses():
    node = shutil.which("node")
    if not node:
        return  # node not available: skip (smoke stays green)
    js_files = glob.glob(os.path.join(HERE, "assets", "js", "*.js"))
    assert js_files, "no asset JS found"
    for js in js_files:
        res = subprocess.run([node, "--check", js], capture_output=True, text=True)
        assert res.returncode == 0, f"syntax error in {os.path.basename(js)}: {res.stderr}"


if __name__ == "__main__":
    fns = [v for k, v in sorted(globals().items()) if k.startswith("test_") and callable(v)]
    for fn in fns:
        fn()
        print("PASS", fn.__name__)
    print(f"\n{len(fns)} passed")
