import zipfile
import xml.etree.ElementTree as ET


def extract_docx_table(path):
    with zipfile.ZipFile(path) as z:
        xml = z.read("word/document.xml")

    root = ET.fromstring(xml)

    # namespace-safe поиск
    ns = {'w': 'http://schemas.openxmlformats.org/wordprocessingml/2006/main'}

    rows = []

    for tr in root.findall('.//w:tr', ns):
        row = []

        for tc in tr.findall('.//w:tc', ns):
            texts = []

            for t in tc.findall('.//w:t', ns):
                if t.text:
                    texts.append(t.text)

            cell_text = "".join(texts).strip()
            row.append(cell_text)

        if any(row):
            rows.append(row)

    return rows