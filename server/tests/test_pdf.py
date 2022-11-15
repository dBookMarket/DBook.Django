# import pdfkit
from weasyprint import HTML

if __name__ == '__main__':
    # pdfkit.from_file('./test.htm', './output.pdf')
    HTML(filename='./test.htm').write_pdf('./output.pdf')
