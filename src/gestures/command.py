from enum import StrEnum
from typing import Protocol
from abc import ABC, abstractmethod
from dataclasses import dataclass

class BuiltinCommand(StrEnum):
  QUIT = "quit"

class CommandContext(Protocol):
  def request_quit(self) -> None: ...

  def submit_process(self, argv: tuple[str, ...]) -> None: ...

class Command(ABC):
  @abstractmethod
  def execute(self, context:CommandContext) -> None:
    ...
  
@dataclass(frozen=True)
class CustomCommand(Command):
  name: str
  argv: tuple[str, ...]

  def execute(self, context: CommandContext) -> None:
    context.submit_process(self.argv)

class QuitCommand(Command):
  def execute(self, context: CommandContext) -> None:
    context.request_quit()

BUILTIN_COMMANDS: dict[BuiltinCommand, Command] = {
  BuiltinCommand.QUIT: QuitCommand(),
}

