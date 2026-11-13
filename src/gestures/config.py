import tomllib
from dataclasses import dataclass
from pathlib import Path
from enum import StrEnum

from gestures.command import (
  BuiltinCommand,
  Command,
  CustomCommand,
  BUILTIN_COMMANDS
)

class Gesture(StrEnum):
  CLOSED_FIST = "closed_fist"

@dataclass(frozen=True)
class Config:
  bindings: dict[Gesture, Command]
  custom_commands: dict[str, CustomCommand]

def load_raw_data(data: dict[str, object]) -> list[dict[str, object]]:
  unknown = set(data) - {"bindings", "custom_commands"}
  if unknown:
    raise ValueError(f"Config: Unknown sections in config.toml: {sorted(unknown)}")

  raw_bindings = data.get("bindings", {})
  raw_commands = data.get("custom_commands", {})

  if not isinstance(raw_bindings, dict):
    raise ValueError('Config: "bindings" must be a table') 
  if not isinstance(raw_commands, dict):
    raise ValueError('Config: "custom_commands" must be a table') 

  return [raw_bindings, raw_commands]

def populate_commands(raw_commands: dict[str, object]) -> dict[str, CustomCommand]:
  custom_commands: dict[str, CustomCommand] = {}
  for name, definition in raw_commands.items():
    if not name or ":" in name:
      raise ValueError(f"Config: Invalid custom command name: {name!r}")

    if not isinstance(definition, dict) or set(definition) != {"argv"}:
      raise ValueError(f"Config: Custom command {name!r} must contain only 'argv'")

    argv = definition["argv"]
    if (
        not argv
        or not isinstance(argv, list)
        or not all(isinstance(arg, str) for arg in argv)
        ):
      raise ValueError(f"Config: Command {name!r}: 'argv' must be a nonempty list of strings")

    custom_commands[name] = CustomCommand(name=name, argv=tuple(argv))
  
  return custom_commands

def populate_bindings(
  raw_bindings: dict[str, object],
  custom_commands: dict[str, CustomCommand],
) -> dict[Gesture, Command]:
  bindings: dict[Gesture, Command] = {}

  for gesture_name, target_command in raw_bindings.items():
    try:
      gesture = Gesture(gesture_name)
    except ValueError:
      raise ValueError(f"Config: Unknown gesture provided in cordie.toml: {gesture_name!r}!") from None

    if not isinstance(target_command, str):
      raise ValueError(f"Config: Binding for {gesture_name!r} must be a string!")

    if target_command.startswith("custom:"):
      command_name = target_command.removeprefix("custom:")
      command = custom_commands.get(command_name)
      if command is None:
        raise ValueError(f"Config: Unknown custom command is provided in the bindings: custom:{command_name!r}!")

      bindings[gesture] = custom_commands[command_name]
    else:
      try:
        identifier = BuiltinCommand(target_command)
      except ValueError:
        raise ValueError(f"Config: Unknown built-in command provided in cordie.toml: {target_command!r}") from None
      
      bindings[gesture] = BUILTIN_COMMANDS[identifier]

  return bindings

def load_config(path: Path) -> None:
  with path.open("rb") as file:
    data = tomllib.load(file)

  raw_bindings, raw_commands = load_raw_data(data)

  custom_commands = populate_commands(raw_commands)
  bindings = populate_bindings(raw_bindings, custom_commands)
