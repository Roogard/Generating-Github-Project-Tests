Root Cause: The `run_script_with_context` function writes the rendered template content to a `NamedTemporaryFile` opened in mode `'w'` without specifying an encoding. On systems where the default locale encoding is not UTF-8 (e.g., Windows with a non-UTF-8 default), the temporary file write may fail or corrupt Unicode characters, causing the script to receive a garbled string instead of "héllo" and thus exit with code 1.

Suggestion 1: Add `encoding='utf-8'` to the `NamedTemporaryFile` call
Change the `tempfile.NamedTemporaryFile(delete=False, mode='w', suffix=extension)` call to include `encoding='utf-8'`, so that the rendered template content (which may contain Unicode characters) is written correctly to the temporary file regardless of the system's default locale encoding.

Suggestion 2: Encode the rendered content explicitly when writing
Instead of relying on the file's default encoding, write the rendered content as bytes by opening the temp file in binary mode (`mode='wb'`) and encoding the rendered string explicitly with `Template(contents).render(**context).encode('utf-8')`. This ensures Unicode content is always written correctly.