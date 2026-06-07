from __future__ import annotations
from re import compile, Pattern, Match
from typing import Callable

class Template:
  def __init__(self, pattern: str):
    self.__pattern: str = pattern
    self.__placeholders: list[Placeholder] = self.parse()
    self.__callbacks: dict[str,Callable[[Placeholder,dict[sct,object],dict[sct,object]],str]] = dict()

  def __str__(self):
    return f"Template(pattern=\"{self.__pattern}\", placeholders={[p.name for p in self.__placeholders]})"

  @property
  def pattern(self) -> str:
    return self.__pattern

  @property
  def placeholders(self) -> list[Placeholder]:
    return self.__placeholders

  @property
  def callbacks(self) -> dict[str,Callable[[Placeholder,dict[sct,object],dict[sct,object]],str]]:
    return self.__callbacks

  def parse(self) -> list[Placeholder]:
    results: list[Placeholder] = []

    text:str = self.pattern
    i: int = 0
    n: int = len(text)

    while i < n - 1:
      # Look for the required prefix "$("
      if text[i] == "$" and text[i + 1] == "(":
        tokens: list[str] = []
        start: int = i
        depth: int = 1

        i += 2
        token: int = i

        while i < n and depth > 0:
          if text[i] == "(":
            depth += 1
          elif text[i] == ")":
            depth -= 1
          elif text[i] == ":":
            tokens.append(text[token:i])
            token = i + 1
          i += 1

        if depth == 0:
          # i is one past the matching ')'
          tokens.append(text[token:i - 1])

          # split up list of 'name(value)' in tokens[1:] to dict[name,value]
          results.append(Placeholder((start, i), tokens[0], [Modifier(m) for m in tokens[1:]]))
        else:
          # Unbalanced — ignore and stop this attempt
          pass
      else:
        i += 1

    return results

  def render(self, scene: dict[str,object], file: dict[str,object], nofm: span[int,int]) -> str:
    result: str = self.pattern
    sortedPlaceholders: list[Placeholder] = self.placeholders.copy()
    sortedPlaceholders.sort(key=lambda p: p.span[0], reverse=True)
    for placeholder in sortedPlaceholders:
      value: str = None
      if placeholder.name in self.callbacks:
        callback: Callable[[Placeholder,dict[sct,object],dict[sct,object]],str] = self.callbacks[placeholder.name]
        value = callback(placeholder, scene, file)
      elif placeholder.name in scene:
        value = str(scene[placeholder.name])
      elif placeholder.name in file:
        value = str(file[placeholder.name])
      else:
        value = f"{placeholder.name} not in scene nor file"
      result = value.join([result[:placeholder.span[0]], result[placeholder.span[1]:]])

    if nofm[1]!=1:
        result += f" ({nofm[0]}of{nofm[1]})"
    
    return result

class Placeholder:
  def __init__(self, span: tuple[int, int], name: str, modifiers: list[Modifier]):
    self.__span = span
    self.__name = name
    self.__modifiers = modifiers
    pass

  def __str__(self):
    return f"Placeholder(name={self.__name}, modifiers={self.__modifiers}, span={self.__span})"

  @property
  def span(self) -> tuple[int, int]:
    return self.__span

  @property
  def name(self) -> str:
    return self.__name

  @property
  def modifiers(self) -> list[Modifier]:
    return self.__modifiers

class Modifier:
  __modifier: Pattern = compile('^([^()]+)(?:\\(([^)]*)\\))?$')

  @staticmethod
  def parse(raw: str) -> tuple[str,str]:
    match: Match = Modifier.__modifier.match(raw)
    if match is not None:
      if match.group(2) is not None:
        return (True, match.group(1), match.group(2))
      else:
        return (True, None, match.group(1))
    else:
      return (False, None, raw)

  def __init__(self, raw: str):
    self.__raw = raw
    (self.__strict, self.__name, self.__value) = Modifier.parse(raw)

  def __str__(self):
    strict: str = f"strict" if self.__strict else ""
    name: str = f"name={self.__name}" if self.__name is not None else ""
    value: str = f"value={self.__value}" if self.__value is not None else ""
    raw: str = f"raw={self.__raw}" if name=="" and value=="" else ""
    return f"Modifier({", ".join([s for s in [strict,raw,name,value] if s != ""])})"

  def __repr__(self):
    return self.__str__()

  @property
  def raw(self) -> str:
    return self.__raw

  @property
  def strict(self) -> bool:
    return self.__strict

  @property
  def name(self) -> str:
    return self.__name

  @property
  def value(self) -> str:
    return self.__value