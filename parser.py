# Copyright 2023 Google LLC
#
# Use of this source code is governed by a BSD-style
# license that can be found in the LICENSE file or at
# https://developers.google.com/open-source/licenses/bsd

"""Parser to extract affected function blocks from the code snippets.

This module abstracts the collection of language parsers for a safer and
simpler use of it.
FunctionChunk and LineChunk are data classes for maintaining data for function
signature and line signature generation. |base| of the continaner classes is a
raw function/line chunk object generated by the language parsers. Data
generated by language parsers can be accessed through |base|, whereas data
generated outside of the language parsers can be updated and accessed through
the other member variables of the data classes.
"""

from typing import Optional, Sequence, Tuple

from absl import logging
from vanir import signature
from vanir.language_parsers import language_parsers


def is_supported_type(filename: str) -> bool:
  """Returns whether any parser supports named file."""
  return language_parsers.get_parser_class(filename) is not None


class Parser:
  """Parses a given file and exports code chunks for making signatures."""

  def __init__(
      self,
      file_path: str,
      target_file: str,
      affected_line_ranges: Optional[Sequence[Tuple[int, int]]] = None,
  ):
    """Parses the given file and extract function and line chunks.

    Args:
      file_path: the absolute path to the file to analyze.
      target_file: relative path of the target file in the target system. E.g.,
        arch/x86/pci/irq.c in Linux Kernel. Note that this value is used as a
        label for the chunks generated from the parser and their corresponding
        signatures. |file_path| is not suitable as a label value since it is an
        absolute path in the runtime system and can be a temporary file.
      affected_line_ranges: list of the ranges of lines affected by a patch.
        Only function chunks that are affected by at least one line within this
        range will be processed. This does not affect how line chunks are
        processed, i.e. this will still return all line chunks in the file.

    Raises:
      StatusNotOk: if failed to open the file at |file_path|.
    """
    if not affected_line_ranges:
      affected_line_ranges = []

    results = language_parsers.parse_file(
        file_path,
        functions_line_ranges=affected_line_ranges,
    )
    if results.parse_errors:
      logging.warning(
          'Syntax errors encountered while parsing file "%s" ("%s"): %s',
          file_path, target_file, results.parse_errors)

    self._function_chunks = [
        signature.create_function_chunk(chunk_base, target_file)
        for chunk_base in results.function_chunks
    ]
    self._line_chunk = signature.create_line_chunk(
        results.line_chunk, affected_line_ranges, target_file
    )

  def get_function_chunks(self) -> Sequence[signature.FunctionChunk]:
    """Gets function chunk list for each function affected by the patch.

    If no affected lines are passed, assumes entire file is affected.
    Returns:
      Function Chunk list.
    """
    return self._function_chunks

  def get_line_chunk(self) -> signature.LineChunk:
    """Gets the line chunk holding tokens of each line.

    Returns:
      Line Chunk object.
    """
    return self._line_chunk
