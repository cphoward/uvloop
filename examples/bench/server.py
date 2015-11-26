import argparse
import asyncio
import gc
import uvloop

from socket import *


PRINT = 1


async def echo_server(loop, address):
    sock = socket(AF_INET, SOCK_STREAM)
    sock.setsockopt(SOL_SOCKET, SO_REUSEADDR, 1)
    sock.bind(address)
    sock.listen(5)
    sock.setblocking(False)
    if PRINT:
        print('Server listening at', address)
    with sock:
        while True:
             client, addr = await loop.sock_accept(sock)
             if PRINT:
                print('Connection from', addr)
             loop.create_task(echo_client(loop, client))


async def echo_client(loop, client):
    with client:
         while True:
             data = await loop.sock_recv(client, 10000)
             if not data:
                  break
             await loop.sock_sendall(client, data)
    print('Connection closed')


async def echo_client_streams(reader, writer):
    sock = writer.get_extra_info('socket')
    if PRINT:
        print('Connection from', sock.getpeername())
    while True:
         data = await reader.read(10000)
         if not data:
             break
         writer.write(data)
         await writer.drain()
    if PRINT:
        print('Connection closed')


async def print_debug(loop):
    while True:
        print(chr(27) + "[2J")  # clear screen
        loop.print_debug_info()
        await asyncio.sleep(0.5, loop=loop)


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--uvloop', default=False, action='store_true')
    parser.add_argument('--streams', default=False, action='store_true')
    args = parser.parse_args()

    if args.uvloop:
        loop = uvloop.Loop()
        print('using UVLoop')
    else:
        loop = asyncio.new_event_loop()
        print('using asyncio loop')

    asyncio.set_event_loop(loop)
    loop.set_debug(False)

    if hasattr(loop, 'print_debug_info'):
        loop.create_task(print_debug(loop))
        PRINT = 0

    if args.streams:
        print('using asyncio/streams')
        coro = asyncio.start_server(echo_client_streams,
                                    '127.0.0.1', 25000, loop=loop)
        loop.create_task(coro)
    else:
        print('using sock_recv/sock_sendall')
        loop.create_task(echo_server(loop, ('', 25000)))
    try:
        loop.run_forever()
    finally:
        if hasattr(loop, 'print_debug_info'):
            gc.collect()
            print(chr(27) + "[2J")
            loop.print_debug_info()

        loop.close()
