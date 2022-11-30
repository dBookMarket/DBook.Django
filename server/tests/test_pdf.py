# import pdfkit
from weasyprint import HTML
import asyncio
import multiprocessing
import time
import threading


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
    asyncio.run(main())

    p = threading.Thread(target=func)
    p.daemon=True
    p.start()
    print(p.is_alive())
