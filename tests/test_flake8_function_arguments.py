from typing import Set
import ast

import pytest

from flake8_function_arguments import Plugin


def get_results(string: str) -> Set[str]:
    tree = ast.parse(string)
    plugin = Plugin(tree)
    return {
        f'{line}:{column} {message}' for line, column, message, _ in plugin.run()
    }


def assert_errors(results: Set[str], error_string: str) -> None:
    for result in results:
        assert error_string in result


def test_that_empty_file_has_no_errors():
    assert get_results('') == set()


def test_that_function_must_have_at_most_3_single_line_args():
    assert get_results('def f(a, b, c): pass') == set()

    result = get_results('def f(a, b, c, d): pass')
    assert result != set()
    assert_errors(result, 'FNA001')


def test_that_function_wo_args_has_no_errors():
    assert get_results('def f(): pass') == set()


def test_multiline_1():
    fn = '''\
def f(a, b, 
    c, d,
):
    pass
    '''
    result = get_results(fn)
    assert result != set()
    assert_errors(result, 'FNA002')


def test_multiline_2():
    fn = '''\
def f(
    a, b, 
    c, d,
):
    pass
    '''
    result = get_results(fn)
    assert result != set()
    assert_errors(result, 'FNA002')


def test_multiline_3():
    fn = '''\
def f(
    a, 
    b, 
    c, 
    d,
):
    pass
    '''
    result = get_results(fn)
    assert result == set()


def test_that_different_types_of_args_can_pass_test_1():
    fn = '''\
def func(
        arg1,
        arg2,
        *args,
        kwarg1='',
        kwarg2='',
        **kwargs,
):
    pass
    '''
    result = get_results(fn)
    assert result == set()


@pytest.mark.parametrize('test_func', [
    'def func(arg1, *args, kwarg1=None): pass',
    'def func(*args, kwarg1=None, **kwargs):  pass',
    'def func(arg1, kwarg1=None, **kwargs):  pass',
])
def test_that_different_types_of_args_can_pass_test_2(test_func):
    print(test_func)
    result = get_results(test_func)
    assert result == set()


@pytest.mark.parametrize('test_func', [
    'def func(arg1, *args, kwarg1=None, **kwargs): pass',
])
def test_that_different_types_of_args_can_not_pass_test_1(test_func):
    print(test_func)
    result = get_results(test_func)
    assert result != set()
