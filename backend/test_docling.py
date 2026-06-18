from pathlib import Path

from docling.document_converter import DocumentConverter

pdf = Path(
    "data/mediassist_data/general/leave_policy.pdf"
)

converter = DocumentConverter()

result = converter.convert(str(pdf))

document = result.document

for i, item in enumerate(document.iterate_items()):

    print("\n" + "=" * 80)
    print(type(item))
    print(item)

    if i > 15:
        break