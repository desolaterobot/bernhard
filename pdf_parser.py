import PyPDF2
from langchain.text_splitter import RecursiveCharacterTextSplitter

# returns a list of strings, each item is page content
def extract_pdf(filename) -> list:
    pages = []
    with open(filename, "rb") as file:
        reader = PyPDF2.PdfReader(file)
        for i, page in enumerate(reader.pages):
            pages.append(page.extract_text())
    return pages

if __name__ == '__main__':
    for page in extract_pdf('documents/dynamicfunc.pdf'):
        print("="*80)
        print(page)
        print("="*80)