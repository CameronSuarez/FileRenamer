  **How to Use**
1) Select a folder
Click Browse or drag a folder into the folder box (if drag-and-drop is enabled).

Files inside are listed in the table (natural order).

2) Choose a mode
A) Build from parts
Controls:

Prefix / Suffix: Text added before/after the (optionally modified) original stem.

Find / Replace: Change the original stem. Toggle Regex for regular expressions.

Start # / Padding: Numbering if you include {n} in your prefix or suffix.

Case: None / lower / UPPER / Title.

Remove spaces: Strip spaces from the final name (stem + prefix/suffix).

Keep extension: Reattach the original extension.

Example:

Prefix: IMG_{n}_, Start 1, Padding 3 → IMG_001_, IMG_002_, …

Find: draft, Replace: final → report_draft → report_final

B) Pattern mode
Provide a single Pattern that can reference placeholders:

Placeholder	Meaning	Example
{n}	Sequence number (start+padding)	001
{stem}	Original file stem	photo
{ext}	Original extension (incl. dot)	.jpg
{parent}	Parent folder name	Trips
{yyyy}	Year (4-digit)	2025
{mm}	Month 01-12	08
{dd}	Day 01-31	12
{hh}	Hour 00-23	16
{mi}	Minute 00-59	04
{ss}	Second 00-59	33

Options:

Start # / Padding: numbering for {n}.

Case: final case transform.

Remove spaces: on the final name.

Auto-append ext if {ext} missing: keeps original extension if your pattern doesn’t include {ext}

  **Logging**
Logs are written to the same folder you’re renaming, named:
rename_log_YYYYMMDD_HHMMSS.csv

Each line: Old Path,New Path (filenames only; same directory)
