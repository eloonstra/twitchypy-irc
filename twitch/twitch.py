import socket
from dataclasses import dataclass
from typing import Generator, Set


@dataclass
class TwitchPrivateMessage:
    """
    A dataclass representing a Twitch private message.
    """
    badges: Set[str]
    color: str
    display_name: str
    first_message: bool
    message_id: str
    mod: bool
    broadcaster: bool
    returning_chatter: bool
    room_id: int
    subscriber: bool
    turbo: bool
    user_id: int
    name: str
    channel: str
    message: str

    @classmethod
    def parse(cls, message: str) -> "TwitchPrivateMessage":
        """
        Parse a Twitch private message.
        :param message: The message to parse.
        """
        badges = {badge.rstrip("/1") for badge in message.split("badges=")[1].split(";")[0].split(",")}
        color = message.split("color=")[1].split(";")[0]
        display_name = message.split("display-name=")[1].split(";")[0]
        first_message = message.split("emotes=")[1].split(";")[0] == "-1"
        message_id = message.split("id=")[1].split(";")[0]
        mod = message.split("mod=")[1].split(";")[0] == "1"
        broadcaster = "broadcaster" in badges
        returning_chatter = message.split("room-id=")[1].split(";")[0] == "1"
        room_id = int(message.split("room-id=")[1].split(";")[0])
        subscriber = message.split("subscriber=")[1].split(";")[0] == "1"
        turbo = message.split("turbo=")[1].split(";")[0] == "1"
        user_id = int(message.split("user-id=")[1].split(";")[0])
        name = message.split("PRIVMSG")[0].split("!")[0].split(":")[1]
        channel = message.split("PRIVMSG")[1].split(":")[0].strip().lstrip("#")
        message = ":".join(message.split("PRIVMSG")[1].split(":")[1:]).strip()
        return cls(
            badges,
            color,
            display_name,
            first_message,
            message_id,
            mod,
            broadcaster,
            returning_chatter,
            room_id,
            subscriber,
            turbo,
            user_id,
            name,
            channel,
            message,
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
        self.user = user
        self.token = token
        self.sock = socket.socket()

    def join(self, channel: str) -> None:
        """
        Join a channel.
        :param channel: The channel to join.
        """
        channel = channel.lstrip("#")
        self.sock.send(f"JOIN #{channel}\n".encode("utf-8"))

    def part(self, channel: str) -> None:
        """
        Leave a channel.
        :param channel: The channel to leave.
        """
        channel = channel.lstrip("#")
        self.sock.send(f"PART #{channel}\n".encode("utf-8"))

    def __pong(self) -> None:
        """
        Send a PONG message to the server.
        """
        self.sock.send("PONG :tmi.twitch.tv\n".encode("utf-8"))

    def connect(self) -> None:
        """
        Connect to the Twitch IRC server.
        """
        self.sock.connect((self.__HOST, self.__PORT))
        self.sock.send(f"PASS oauth:{self.token}\n".encode("utf-8"))
        self.sock.send(f"NICK {self.user}\n".encode("utf-8"))
        self.sock.send("CAP REQ :twitch.tv/tags\n".encode("utf-8"))
        self.sock.send("CAP REQ :twitch.tv/commands\n".encode("utf-8"))

    def close(self) -> None:
        """
        Close the connection to the Twitch IRC server.
        """
        self.sock.close()

    def send_message(self, channel: str, message: str) -> None:
        """
        Send a message to a channel.
        :param channel: The channel to send the message to.
        :param message: The message to send.
        """
        channel = channel.lstrip("#")
        self.sock.send(f"PRIVMSG #{channel} :{message}\n".encode("utf-8"))

    def send_reply(self, message_id: str, channel: str, reply: str) -> None:
        """
        Send a reply to a message.
        :param message_id: The ID of the message to reply to.
        :param channel: The channel to send the reply to.
        :param reply: The reply to send.
        """
        channel = channel.lstrip("#")
        self.sock.send(f"@reply-parent-msg-id={message_id} PRIVMSG #{channel} :{reply}\n".encode("utf-8"))

    def __recv(self) -> Generator[str, None, None]:
        """
        Receive a message from the server.
        :return: A generator of messages.
        """
        total = ""
        while True:
            recv = self.sock.recv(1024).decode("utf-8")
            total += recv
            if "\n" not in total:
                continue

            for line in total.split("\n"):
                yield line
                total = line

    def read(self) -> Generator[TwitchPrivateMessage, None, None]:
        """
        Read messages from the server.
        :return: A generator of TwitchPrivateMessage objects.
        """
        for recv in self.__recv():
            if recv.startswith("PING"):
                self.__pong()
            elif "PRIVMSG" in recv:
                yield TwitchPrivateMessage.parse(recv)
            elif "RECONNECT" in recv:
                self.close()
                self.connect()

    def __del__(self) -> None:
        """
        Close the connection to the Twitch IRC server.
        """
        self.close()
