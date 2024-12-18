import queue
import socket
import threading
from dataclasses import dataclass
from typing import Generator, Set, List, Optional


@dataclass
class TwitchPrivateMessage:
    """
    A dataclass representing a Twitch private message.
    """
    badges: Set[str]
    color: str
    name: str
    is_first_message: bool
    message_id: str
    is_moderator: bool
    is_broadcaster: bool
    is_returning_chatter: bool
    room_id: int
    is_subscriber: bool
    is_turbo: bool
    user_id: int
    channel: str
    content: str

    @classmethod
    def parse(cls, message: str) -> "TwitchPrivateMessage":
        """
        Parse a Twitch private message.
        :param message: The message to parse.
        """
        parts: List[str] = message.split(" :", 3)
        tags = {key: value for key, value in [tag.split("=") for tag in parts[0].split(";")]}
        badges = set(tags["badges"].split(","))
        color = tags["color"]
        name = tags["display-name"]
        is_first_message = tags["first-msg"] == "1"
        message_id = tags["id"]
        is_moderator = tags["mod"] == "1"
        is_broadcaster = any(string.startswith("broadcaster/") for string in badges)
        is_returning_chatter = tags["returning-chatter"] == "1"
        room_id = int(tags["room-id"])
        is_subscriber = tags["subscriber"] == "1"
        is_turbo = tags["turbo"] == "1"
        user_id = int(tags["user-id"])
        channel = parts[1].split(" ")[-1].lstrip("#")
        content = parts[2]

        return cls(
            badges=badges,
            color=color,
            name=name,
            is_first_message=is_first_message,
            message_id=message_id,
            is_moderator=is_moderator,
            is_broadcaster=is_broadcaster,
            is_returning_chatter=is_returning_chatter,
            room_id=room_id,
            is_subscriber=is_subscriber,
            is_turbo=is_turbo,
            user_id=user_id,
            channel=channel,
            content=content,
        )


class Twitch:
    """
    Twitch IRC client.
    """
    __DEFAULT_USER = "justinfan12345"
    __DEFAULT_TOKEN = "oauth:1234567890"
    __HOST = "irc.chat.twitch.tv"
    __PORT = 6667

    def __init__(self, user: str = __DEFAULT_USER, token: str = __DEFAULT_TOKEN):
        """
        Initialize the Twitch IRC client.
        :param user: The username to use.
        :param token: The OAuth token to use.
        """
        token = token.lstrip("oauth:")
        self.__user = user
        self.__token = token
        self.__sock = socket.socket()
        self.__queue = queue.Queue()
        self.__is_running = False
        self.__is_reconnecting = False
        self.__thread: Optional[threading.Thread] = None

    def join(self, channel: str) -> None:
        """
        Join a channel.
        :param channel: The channel to join.
        """
        channel = channel.lstrip("#")
        self.__sock.send(f"JOIN #{channel}\n".encode("utf-8"))

    def leave(self, channel: str) -> None:
        """
        Leave a channel.
        :param channel: The channel to leave.
        """
        channel = channel.lstrip("#")
        self.__sock.send(f"PART #{channel}\n".encode("utf-8"))

    def __pong(self) -> None:
        """
        Send a PONG message to the server.
        """
        self.__sock.send("PONG :tmi.twitch.tv\n".encode("utf-8"))

    def connect(self) -> None:
        """
        Connect to the Twitch IRC server.
        """
        self.__sock.connect((self.__HOST, self.__PORT))
        self.__sock.send(f"PASS oauth:{self.__token}\n".encode("utf-8"))
        self.__sock.send(f"NICK {self.__user}\n".encode("utf-8"))
        self.__sock.send("CAP REQ :twitch.tv/tags\n".encode("utf-8"))
        self.__sock.send("CAP REQ :twitch.tv/commands\n".encode("utf-8"))

        self.__is_running = True
        self.__thread = threading.Thread(
            target=self.__message_handler,
            daemon=True,
        )
        self.__thread.start()

    def disconnect(self) -> None:
        """
        Disconnect from the Twitch IRC server.
        """
        self.__is_running = False
        if self.__thread:
            self.__thread.join()
        self.__sock.close()

        if not self.__is_reconnecting:
            while not self.__queue.empty():
                self.__queue.get()

    def send_message(self, channel: str, message: str) -> None:
        """
        Send a message to a channel.
        :param channel: The channel to send the message to.
        :param message: The message to send.
        """
        channel = channel.lstrip("#")
        self.__sock.send(f"PRIVMSG #{channel} :{message}\n".encode("utf-8"))

    def send_reply(self, message_id: str, channel: str, reply: str) -> None:
        """
        Send a reply to a message.
        :param message_id: The ID of the message to reply to.
        :param channel: The channel to send the reply to.
        :param reply: The reply to send.
        """
        channel = channel.lstrip("#")
        self.__sock.send(f"@reply-parent-msg-id={message_id} PRIVMSG #{channel} :{reply}\n".encode("utf-8"))

    def __recv(self) -> Generator[str, None, None]:
        """
        Receive a message from the server.
        :return: A generator of messages.
        """
        buffer = ""
        while self.__is_running and not self.__is_reconnecting:
            data = self.__sock.recv(2048).decode("utf-8")
            buffer += data
            while "\n" in buffer:
                line, buffer = buffer.split("\n", 1)
                yield line.strip()

    def read(self) -> Generator[TwitchPrivateMessage, None, None]:
        """
        Read messages from the queue.
        :return: A generator of messages.
        """
        while self.__is_running:
            yield self.__queue.get()

    def __message_handler(self) -> None:
        """
        Handle messages from the server.
        """
        for recv in self.__recv():
            if recv.startswith("PING"):
                print("ping")
                self.__pong()
            elif "PRIVMSG" in recv:
                self.__queue.put_nowait(TwitchPrivateMessage.parse(recv))
            elif "RECONNECT" in recv:
                print("reconnecting...")
                self.__is_reconnecting = True
                self.disconnect()
                self.connect()
                self.__is_reconnecting = False

    def __del__(self) -> None:
        """
        Close the connection to the Twitch IRC server.
        """
        self.disconnect()
