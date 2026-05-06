import fitz

file_path = "uploads/tender.pdf"

try:
    doc = fitz.open(file_path)

    for page_num in range(len(doc)):
        page = doc[page_num]
        text = page.get_text().lower()

        # 🔥 SEARCH KEYWORDS
        if "qualification" in text or "eligibility" in text or "experience" in text:
            print(f"\n🔥 FOUND ON PAGE {page_num+1} 🔥\n")
            print(page.get_text()[:1500])

except Exception as e:
    print("ERROR:", e)