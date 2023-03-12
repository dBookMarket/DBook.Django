# import pdfkit
# from weasyprint import HTML
import asyncio
# import multiprocessing
import time
# import threading

import ebooklib
from ebooklib import epub


def func():
    print('hi....')
    time.sleep(10)
    print('bye....')


async def main():
    print('Hello ...')
    await asyncio.sleep(1)
    print('... World!')


if __name__ == '__main__':
    # pdfkit.from_file('./test.htm', './output.pdf')
    # HTML(filename='./test.htm').write_pdf('./output.pdf')
    # with open('./test.pdf', 'rb') as f:
    #     print(f.read()[:500])
    # asyncio.run(main())
    #
    # p = threading.Thread(target=func)
    # p.daemon=True
    # p.start()
    # print(p.is_alive())

    # book = epub.read_epub('./test.epub')
    # print(book.get_metadata('DC', 'title')[0][0])

    # n = 0
    # content = b''
    # for doc in book.get_items_of_type(ebooklib.ITEM_DOCUMENT):
    #     content += doc.content
    #
    # HTML(string=content.decode()).write_pdf('./epub.pdf')

    # content = ''
    # with open('./test.txt', 'r') as f:
    #     chunk = f.readline(512)
    #     while chunk:
    #         content += chunk
    #         chunk = f.readline(512)
    #
    # HTML(string=content).write_pdf('./text.pdf')

    book = epub.EpubBook()

    book.set_title('Simple book')
    book.add_author('ABC')

    book.set_cover('cover.png', open('test.png', 'rb').read())

    c1 = epub.EpubHtml(title='Cover', file_name='cover-image.xhtml')
    c1.set_content('<p><img src="cover.png" alt="cover image"/></p>')

    c2 = epub.EpubHtml(title='Title', file_name='title-page.xhtml')
    c2.set_content('<h1>Simple book</h1>')

    c3 = epub.EpubHtml(title='Content', file_name='content.xhtml', lang='hr')
    c3.set_content('<html><body><p>Introduction paragraph.sdfffffffff</p>'
                   '<p>fsdffffffffffffffffffffffsdfsdf</p>'
                   '<p>fsdfffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffsdfsdfdfsdf</p>'
                   '<p>fsdddddddddddddddddddddddddddddddddddfsdfs</p>'
                   '<p>fsdffffffffffffffffffffffffff</p></body></html>')

    book.add_item(c1)
    book.add_item(c2)
    book.add_item(c3)

    # book.toc = (epub.Link('content.xhtml', 'Content', 'content'),)
    # book.add_item(epub.EpubNcx())
    # book.add_item(epub.EpubNav())

    book.spine = ['cover', c1, c2, c3]
    epub.write_epub('book.epub', book)
