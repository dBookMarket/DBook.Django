# import pdfkit
from weasyprint import HTML

if __name__ == '__main__':
    # pdfkit.from_file('./test.htm', './output.pdf')
    # HTML(filename='./test.htm').write_pdf('./output.pdf')
    with open('./test.pdf', 'rb') as f:
        print(f.read()[:500])
