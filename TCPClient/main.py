import asyncio
import queue

# Configuration 
SERVER_PORT = 5000
message_to_send = "test data with space and $@>"

send_queue = queue.Queue()
receive_queue = queue.Queue()


def get_server_ip():
    ip = "198.162.X.Y" #ip address of TCP Server
    while not ip:
        ip = input("Enter ESP32 IP address: ").strip()
    return ip


class TcpClient:
    def __init__(self, ip, port):
        self.ip = ip
        self.port = port
        self.reader = None
        self.writer = None
        self.receive_buffer = ""

    async def connect(self):
        self.reader, self.writer = await asyncio.open_connection(self.ip, self.port)
        print(f"Connected to {self.ip}:{self.port}")

        asyncio.create_task(self.send_loop())
        asyncio.create_task(self.receive_loop())

    async def send_loop(self):
        while True:
            while not send_queue.empty():
                msg = send_queue.get() + "\n"
                self.writer.write(msg.encode("ascii"))
                await self.writer.drain()
                print(f"Sent: {msg.strip()}")

            await asyncio.sleep(0.001)

    async def receive_loop(self):
        try:
            while True:
                data = await self.reader.read(1024)
                if not data:
                    print("Connection closed by server")
                    break

                chunk = data.decode("ascii")
                self.receive_buffer += chunk

                while "\n" in self.receive_buffer:
                    msg, self.receive_buffer = self.receive_buffer.split("\n", 1)
                    msg = msg.strip()
                    if msg:
                        receive_queue.put(msg)
        except Exception as e:
            print("Receive error:", e)


async def main():
    server_ip = get_server_ip()

    client = TcpClient(server_ip, SERVER_PORT)
    await client.connect()

    # Enqueue initial message
    send_queue.put(message_to_send)

    # Passive update loop
    while True:
        while not receive_queue.empty():
            print("ESP32:", receive_queue.get())

        await asyncio.sleep(0.01)


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\nProgram stopped by user")

