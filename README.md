## Python Twitch IRC Library

This is a simple Python library for connecting to the Twitch IRC chat and sending/receiving messages.

### Twitch

This is the main class for the Twitch IRC client and has the following methods:

- `__init__(self, user: str = "justinfan12345", token: str = "oauth:1234567890")`: Initializes the client with the given
  username and OAuth token.
- `join(self, channel: str) -> None`: Joins the given channel.
- `part(self, channel: str) -> None`: Leaves the given channel.
- `connect(self) -> None`: Connects to the Twitch IRC server.
- `close(self) -> None`: Closes the connection to the Twitch IRC server.
- `send_message(self, channel: str, message: str) -> None`: Sends a message to the given channel.
- `send_reply(self, message_id: str, channel: str, reply: str) -> None`: Sends a reply to the given message.
- `read(self) -> Generator[TwitchPrivateMessage, None, None]`: Reads messages from the Twitch IRC server.

### TwitchPrivateMessage

This class represents a Twitch private message and has the following attributes:

- `badges` (set): A set of strings representing the badges the user has.
- `color` (str): The color of the user's username in the chat.
- `display_name` (str): The user's display name.
- `first_message` (bool): Whether this is the user's first message in the chat.
- `message_id` (str): The ID of the message.
- `mod` (bool): Whether the user is a moderator.
- `broadcaster` (bool): Whether the user is the broadcaster.
- `returning_chatter` (bool): Whether the user has been in the chat before.
- `room_id` (int): The ID of the room.
- `subscriber` (bool): Whether the user is a subscriber.
- `turbo` (bool): Whether the user has Twitch Turbo.
- `user_id` (int): The ID of the user.
- `name` (str): The user's name.
- `channel` (str): The channel the message was sent to.
- `message` (str): The contents of the message.

### Usage

To use this library, create a `Twitch` instance and call its methods to connect to the Twitch IRC chat and send/receive
messages.

```python
from twitch import Twitch

client = Twitch(user="your_username", token="your_oauth_token")
client.connect()
client.join("your_channel")
client.send_message("your_channel", "Hello, world!")
for message in client.read():
    print(message)
client.close()
```

### Contributing

All contributions are welcome! Please open an issue or pull request if you have any suggestions or find any bugs.

### License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.