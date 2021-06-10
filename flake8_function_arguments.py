import ast
import importlib.metadata
from functools import wraps
from typing import Generator, Tuple, Type, Any, List

CLASS_ARGS = ['self', 'cls']


def add_generic_visit(func):
    @wraps(func)
    def inner(self, node, *args, **kwargs):
        result = func(self, node, *args, **kwargs)
        self.generic_visit(node)
        return result

    return inner


class Visitor(ast.NodeVisitor):
    def __init__(self, max_single_line_args: int) -> None:
        self.max_single_line_args = max_single_line_args
        self.problems: List[Tuple[int, int, str]] = []

    @add_generic_visit
    def visit_FunctionDef(self, node: ast.FunctionDef) -> None:
        # astpretty --no-show-offsets /dev/stdin <<< 'def f(a, b, c, d, q=1): pass'

        one_line_problems = self.check_that_one_line_function_signature_has_max_number_of_args(
            node,
            self.max_single_line_args,
        )
        self.problems.extend(one_line_problems)

        multi_line_problems = self.check_that_function_signature_has_one_arg_per_line(node)
        self.problems.extend(multi_line_problems)

    @staticmethod
    def check_that_one_line_function_signature_has_max_number_of_args(
            node: ast.FunctionDef,
            max_single_line_args: int,
    ) -> List[Tuple[int, int, str]]:
        problems = []
        function_line = node.lineno
        args = node.args

        all_args = args.args + [args.vararg] + args.kwonlyargs + [args.kwarg]
        all_args = [arg for arg in all_args if arg is not None]

        all_arguments_are_on_one_line = all((function_line == arg.lineno for arg in all_args))
        arguments_lines = [arg.lineno for arg in all_args if arg.arg not in CLASS_ARGS]
        if all_arguments_are_on_one_line and len(arguments_lines) > max_single_line_args:
            problems.append(
                (
                    function_line,
                    0,
                    f'FNA001 Function should not have more than {max_single_line_args} single line arguments.',
                ),
            )
        return problems

    @staticmethod
    def check_that_function_signature_has_one_arg_per_line(node: ast.FunctionDef) -> List[Tuple[int, int, str]]:
        problems = []
        function_line = node.lineno
        args = node.args

        all_args = args.args + [args.vararg] + args.kwonlyargs + [args.kwarg]
        all_args = [arg for arg in all_args if arg is not None]
        args_lines = [arg.lineno for arg in all_args if arg.arg not in CLASS_ARGS]
        uniq_args_lines = {arg.lineno for arg in all_args if arg.arg not in CLASS_ARGS}
        if any((function_line != arg.lineno for arg in all_args)) and len(args_lines) != len(uniq_args_lines):
            problems.append(
                (
                    function_line,
                    0,
                    f'FNA002 Function should have only one argument per line in multiline definition.',
                ),
            )

        return problems


class Plugin:
    MAX_SINGLE_LINE_ARGS = 3
    name = __name__
    version = importlib.metadata.version(__name__)
    max_single_line_args = MAX_SINGLE_LINE_ARGS

    def __init__(self, tree: ast.AST) -> None:
        self._tree = tree

    @classmethod
    def add_options(cls, parser) -> None:
        parser.add_option(
            '--max-single-line-args',
            type=int,
            default=cls.MAX_SINGLE_LINE_ARGS,
            parse_from_config=True,
        )

    @classmethod
    def parse_options(cls, options) -> None:
        cls.max_single_line_args = int(options.max_single_line_args)

    def run(self) -> Generator[Tuple[int, int, str, Type[Any]], None, None]:
        visitor = Visitor(max_single_line_args=self.max_single_line_args)
        visitor.visit(self._tree)
        for line, column, text in visitor.problems:
            yield line, column, text, type(self)
