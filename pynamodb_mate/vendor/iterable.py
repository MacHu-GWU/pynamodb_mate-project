# -*- coding: utf-8 -*-

"""
This module provides plenty of useful functions for iterable object manipulation.
"""

import typing as T
import random
import collections
import itertools

__version__ = "0.1.1"

def flatten(iterable: T.Iterable) -> T.Iterable:
    """
    Flatten one layer of nesting.

    Example::

        >>> list(flatten([[0, 1], [2, 3]])
        [0, 1, 2, 3]

        >>> list(flatten(["ab", "cd"])
        ["a", "b", "c", "d"]

    **中文文档**

    将二维列表压平成一维列表.
    """
    return itertools.chain.from_iterable(iterable)


def flatten_all(nested_iterable: T.Iterable) -> T.Iterable:
    """Flatten arbitrary depth of nesting. Good for unknown nesting structure
    iterable object.

    Example::

        >>> list(flatten_all([[1, 2], "abc", [3, ["x", "y", "z"]], 4]))
        [1, 2, "abc", 3, "x", "y", "z", 4]

    **中文文档**

    将任意维度的列表压平成一维列表.

    注: 使用 ``hasattr(i, "__iter__")`` 方法做是否是可循环对象的判断, 性能要高于其他
    任何方法, 例如: ``isinstance(i, collections.Iterable)``.
    """
    for item in nested_iterable:
        if hasattr(item, "__iter__") and not isinstance(item, str):
            for i in flatten_all(item):
                yield i
        else:
            yield item


def nth(iterable: T.Iterable, n: int, default=None):
    """
    Returns the nth item or a default value.

    Example::

        >>> nth([0, 1, 2], 1)
        1

        >>> nth([0, 1, 2], 100)
        None

    **中文文档**

    取出一个可循环对象中的第 n 个元素。等效于 ``list(iterable)[n]``, 但占用极小的内存.
    因为 ``list(iterable)`` 要将所有元素放在内存中并生成一个新列表. 该方法常用于
    那些无法做取 index 操作的可循环对象.
    """
    return next(itertools.islice(iterable, n, None), default)


def take(iterable: T.Iterable, n: int) -> T.Iterable:
    """
    Return first n items of the iterable as a list.

    Example::

        >>> take([0, 1, 2], 2)
        [0, 1]

    **中文文档**

    取出可循环对象中的前 n 个元素. 等效于 ``list(iterable)[:n]``, 但占用极小的内存.
    因为 ``list(iterable)`` 要将所有元素放在内存中并生成一个新列表. 该方法常用于
    那些无法做取 index 操作的可循环对象.
    """
    return list(itertools.islice(iterable, n))


def pull(iterable: T.Iterable, n: int) -> list:
    """Return last n items of the iterable as a list.

    Example::

        >>> pull([0, 1, 2], 3)
        [1, 2]

    **中文文档**

    取出可循环对象中的最后 n 个元素. 等效于 ``list(iterable)[-n:]``, 但占用极小的内存.
    因为 ``list(iterable)`` 要将所有元素放在内存中并生成一个新列表. 该方法常用于
    那些无法做取 index 操作的可循环对象.
    """
    fifo = collections.deque(maxlen=n)
    for i in iterable:
        fifo.append(i)
    return list(fifo)


def shuffled(lst: list) -> list:
    """Returns the shuffled iterable.

    Example::

        >>> shuffled([0, 1, 2])
        [2, 0, 1]

    **中文文档**

    打乱一个可循环对象中所有元素的顺序. 并打包成列表返回.
    """
    return random.sample(lst, len(lst))


def grouper(iterable: T.Iterable, n: int, fillvalue=None):
    """Collect data into fixed-length chunks or blocks.

    Example::

        >>> list(grouper(range(10), n=3, fillvalue=None))
        [(0, 1, 2), (3, 4, 5), (6, 7, 8), (9, None, None)]

    **中文文档**

    将一个序列按照尺寸 n, 依次打包输出, 如果元素不够 n 的包, 则用 ``fillvalue`` 中的值填充.
    """
    args = [iter(iterable)] * n
    return itertools.zip_longest(*args, fillvalue=fillvalue)


def grouper_list(iterable: T.Iterable, n: int) -> T.Iterable[list]:
    """Evenly divide list into fixed-length piece, no filled value if chunk
    size smaller than fixed-length.

    Example::

        >>> list(grouper(range(10), n=3)
        [[0, 1, 2], [3, 4, 5], [6, 7, 8], [9]]

    **中文文档**

    将一个列表按照尺寸 n, 依次打包输出, 有多少输出多少, 并不强制填充包的大小到 n.

    下列实现是按照性能从高到低进行排列的:

    - 方法1: 建立一个 counter, 在向 chunk 中添加元素时, 同时将 counter 与 n 比较,
        如果一致则 yield. 然后在最后将剩余的 item 视情况 yield.
    - 方法2: 建立一个 list, 每次添加一个元素, 并检查 size. (显然性能较差)
    - 方法3: 调用 grouper() 函数, 然后对里面的 None 元素进行清理.
    """
    chunk = list()
    counter = 0
    for item in iterable:
        counter += 1
        chunk.append(item)
        if counter == n:
            yield chunk
            chunk = list()
            counter = 0
    if len(chunk) > 0:
        yield chunk


def grouper_dict(dct: dict, n: int, dict_type=dict) -> T.Iterable[dict]:
    """
    Evenly divide dictionary into fixed-length piece, no filled value if
    chunk size smaller than fixed-length. Notice: dict is unordered in python,
    this method suits better for collections.OrdereDict.

    Example::
        >>> d = {"a": 1, "b": 2, "c": 3, "d": 4, "e": 5}
        >>> list(grouper_dict(d, 2)
        [{"a": 1, "b": 2}, {"c": 3, "d": 4}, {"e": 5}]

    **中文文档**

    将一个字典按照尺寸 n, 依次打包输出, 有多少输出多少, 并不强制填充包的大小到 n.
    """
    chunk = dict_type()
    counter = 0
    for k, v in dct.items():
        counter += 1
        chunk[k] = v
        if counter == n:
            yield chunk
            chunk = dict_type()
            counter = 0
    if len(chunk) > 0:
        yield chunk


# --- Window ---
def running_window(lst: list, size: int):
    """
    Generate n-size running window.

    Example::

        >>> for i in running_window([1, 2, 3, 4, 5], size=3):
        ...     print(i)
        [1, 2, 3]
        [2, 3, 4]
        [3, 4, 5]

    **中文文档**

    简单滑窗函数.
    """
    if size > len(lst):
        raise ValueError("size can not be greater than length of iterable.")

    fifo = collections.deque(maxlen=size)
    for i in lst:
        fifo.append(i)
        if len(fifo) == size:
            yield list(fifo)


def cycle_running_window(lst: list, size: int) -> list:
    """
    Generate n-size cycle running window.

    Example::

        >>> for i in cycle_running_window([1, 2, 3, 4, 5], size=3):
        ...     print(i)
        [1, 2, 3]
        [2, 3, 4]
        [3, 4, 5]
        [4, 5, 1]
        [5, 1, 2]

    **中文文档**

    循环位移滑窗函数.
    """
    if size > len(lst):
        raise ValueError("size can not be greater than length of iterable.")

    fifo = collections.deque(maxlen=size)
    cycle = itertools.cycle(lst)
    counter = itertools.count(1)
    length = len(lst)
    for i in cycle:
        fifo.append(i)
        if len(fifo) == size:
            yield list(fifo)
            if next(counter) == length:
                break


# --- Cycle ---
def cycle_slice(sliceable: list, start: int, end: int) -> list:
    """
    Given a list, return the right-hand cycle direction slice from start to end.

    Example::

        >>> array = [0, 1, 2, 3]
        >>> cycle_slice(array, 1, 3) # from array[1] to array[3]
        [1, 2]

        >>> cycle_slice(array, 3, 1) # from array[3] to array[1]
        [3, 0]
    """
    length = len(sliceable)

    if length == 0:
        raise ValueError("sliceable cannot be empty!")
    start = start % length
    end = end % length

    if end > start:
        return sliceable[start:end]
    elif end <= start:
        return sliceable[start:] + sliceable[:end]


def cycle_dist(
    x: T.Union[int, float],
    y: T.Union[int, float],
    perimeter: T.Union[int, float],
) -> T.Union[int, float]:
    """Find Distance between x, y by means of a n-length cycle.

    :param x:
    :param y:
    :param perimeter:

    Example:

        >>> cycle_dist(1, 23, 24)
        2

        >>> cycle_dist(5, 13, 24)
        8

        >>> cycle_dist(0.0, 2.4, 1.0)
        0.4

        >>> cycle_dist(0.0, 2.6, 1.0)
        0.4

    **中文文档**

    假设坐标轴是一个环, 计算两点之间在环上的最短距离.
    """
    dist = abs(x - y) % perimeter
    if dist > 0.5 * perimeter:
        dist = perimeter - dist
    return dist


# --- Shift ---
def cyclic_shift(array: list, shift: int) -> list:
    """

    :params array: list like iterable object
    :params shift: number of movement

    Example::

        >>> cyclic_shift([0, 1, 2], 1)
        [2, 0, 1]

        >>> cyclic_shift([0, 1, 2], -1)
        [1, 2, 0]

    **中文文档**

    循环位移函数.
    """
    shift = shift % len(array)
    return array[-shift:] + array[:-shift]


def shift_and_trim(array: list, shift: int) -> list:
    """
    Shift and trim unneeded item.

    :params array: list like iterable object
    :params shift: number of movement

    Example::

        >>> array = [0, 1, 2]

        >>> shift_and_trim(array, 0)
        [0, 1, 2]

        >>> shift_and_trim(array, 1)
        [0, 1]

        >>> shift_and_trim(array, -1)
        [1, 2]

        >>> shift_and_trim(array, 3)
        []

        >>> shift_and_trim(array, -3)
        []
    """
    length = len(array)
    if length == 0:
        return []

    if (shift >= length) or (shift <= -length):
        return []
    elif shift < 0:
        return array[-shift:]
    elif shift > 0:
        return array[:-shift]
    else:
        return list(array)


def shift_and_pad(array: list, shift: int, pad: T.Any = "__null__") -> list:
    """
    Shift and pad with item.

    :params array: list like iterable object
    :params shift: number of movement
    :params pad: any value

    Example::

        >>> array = [0, 1, 2]

        >>> shift_and_pad(array, 0)
        [0, 1, 2]

        >>> shift_and_pad(array, 1)
        [0, 0, 1]

        >>> shift_and_pad(array, -1)
        [1, 2, 2]

        >>> shift_and_pad(array, 3)
        [0, 0, 0]

        >>> shift_and_pad(array, -3)
        [2, 2, 2]

        >>> shift_and_pad(array, -1, None)
        [None, 0, 1]
    """
    length = len(array)
    if length == 0:
        return []

    if pad == "__null__":
        if shift > 0:
            padding_item = array[0]
        elif shift < 0:
            padding_item = array[-1]
        else:
            padding_item = None
    else:
        padding_item = pad

    if abs(shift) >= length:
        return length * [
            padding_item,
        ]
    elif shift == 0:
        return list(array)
    elif shift > 0:
        return [
            padding_item,
        ] * shift + array[:-shift]
    elif shift < 0:
        return (
            array[-shift:]
            + [
                padding_item,
            ]
            * -shift
        )
    else:  # pragma: no cover
        raise NotImplementedError


def size_of_generator(generator: T.Iterable, memory_efficient=True) -> int:
    """Get number of items in a generator function.

    - memory_efficient = True, 3 times slower, but memory_efficient.
    - memory_efficient = False, faster, but cost more memory.

    **中文文档**

    计算一个生成器函数中的元素的个数。使用memory_efficient=True的方法可以避免将生成器中的
    所有元素放入内存, 但是速度稍慢于memory_efficient=False的方法。
    """
    if memory_efficient:
        counter = 0
        for _ in generator:
            counter += 1
        return counter
    else:
        return len(list(generator))


def difference(array: list, k: int = 1) -> list:
    """
    简单差分函数.

    Example::

        >>> difference([0, 1, 3, 6, 10], 0)
        [0, 0, 0, 0, 0]

        >>> difference([0, 1, 3, 6, 10], 1)
        [1, 2, 3, 4]

        >>> difference([0, 1, 3, 6, 10], 2)
        [3, 5, 7]
    """
    if (len(array) - k) < 1:
        raise ValueError()
    if k < 0:
        raise ValueError("k has to be greater or equal than zero!")
    elif k == 0:
        return [i - i for i in array]
    else:
        return [j - i for i, j in zip(array[:-k], array[k:])]


KT = T.TypeVar("KT")
VT = T.TypeVar("VT")

def group_by(
    iterable: T.Iterable[VT],
    get_key: T.Callable[[VT], KT],
) -> T.Dict[KT, T.List[VT]]:
    """
    Group items by it's key, with type hint.

    Example::

        >>> class Record:
        ...     def __init__(self, product: str, date: str, sale: int):
        ...         self.product = product
        ...         self.date = date
        ...         self.sale = sale

        >>> records = [
        ...     Record("apple", "2020-01-01", 10),
        ...     Record("apple", "2020-01-02", 20),
        ...     Record("apple", "2020-01-03", 30),
        ...     Record("banana", "2020-01-01", 10),
        ...     Record("banana", "2020-01-02", 20),
        ...     Record("banana", "2020-01-03", 30),
        ... ]

        >>> group_by(records, lambda x: x.product)
        {
            "apple": [
                Record("apple", "2020-01-01", 10),
                Record("apple", "2020-01-02", 20),
                Record("apple", "2020-01-03", 30),
            ],
            "banana": [
                Record("banana", "2020-01-01", 10),
                Record("banana", "2020-01-02", 20),
                Record("banana", "2020-01-03", 30),
            ],
        }
    """
    grouped = dict()
    for item in iterable:
        key = get_key(item)
        try:
            grouped[key].append(item)
        except KeyError:
            grouped[key] = [item]
    return grouped
