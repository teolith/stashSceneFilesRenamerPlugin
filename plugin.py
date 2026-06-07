import os,sys,stat,json
from stashapi.stashapp import StashInterface

class Plugin:
    @staticmethod
    def read_stdin() -> str:
        fileno: int = sys.stdin.fileno()
        mode: int = os.fstat(fileno).st_mode
        piped: bool = not os.isatty(fileno) and stat.S_ISFIFO(mode)

        lines: list = []
        if not piped:
            lines = sys.stdin.readlines()

        return "".join(lines)

    @staticmethod
    def new_stash_connection(json_input: dict) -> StashInterface:
        server_connection = json_input["server_connection"]
        host = server_connection["Host"]
        if host == "0.0.0.0":
            host = "localhost"
        stash_connection = {
            "Scheme": server_connection["Scheme"],
            "Host": host,
            "Port": server_connection["Port"],
        }
        if server_connection.get("SessionCookie"):
            stash_connection["SessionCookie"] = server_connection["SessionCookie"]
        if server_connection.get("ApiKey"):
            stash_connection["ApiKey"] = server_connection["ApiKey"]
        return StashInterface(stash_connection)

    def __init__(self, name: str, stdin: str = None):
        self._name = name
        data: str = stdin
        if data is None:
            data = Plugin.read_stdin()
        self._json_input = json.loads(data)
        self._stash_interface: StashInterface = Plugin.new_stash_connection(self._json_input)

    @property
    def name(self) -> str:
        return self._name

    @property
    def json_input(self) -> dict:
        return self._json_input

    @property
    def stash_interface(self) -> StashInterface:
        return self._stash_interface
