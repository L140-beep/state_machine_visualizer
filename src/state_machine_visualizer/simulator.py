from copy import deepcopy
import ast
import xml.etree.ElementTree as ET
from dataclasses import dataclass, field
from typing import (
    List,
    Dict,
    Optional,
    Union,
    DefaultDict,
    Literal,
    TypeVar,
    Any,
    Callable
)
import re
from collections import defaultdict
import random
from collections import deque
from collections.abc import Iterable
from functools import partial
from abc import ABC
import time
import sys


# ============================================================================
# UTILS.PY
# ============================================================================

"""Utility functions for the simple parser."""

ListType = TypeVar('ListType')


def to_list(nodes: Union[List[ListType], None, ListType]) -> List[ListType]:
    """Return list of objects."""
    if nodes is None:
        return []
    if isinstance(nodes, list):
        return nodes
    else:
        return [nodes]


def is_vertex_type(value: str) -> bool:
    """Check if value is a valid vertex type."""
    vertex_types = ['choice', 'initial',
                    'final', 'terminate', 'shallowHistory']
    return value in vertex_types


def is_note_type(value: str) -> bool:
    """Check if value is a valid note type."""
    note_types = ['formal', 'informal']
    return value in note_types


def create_object_from_dict(cls, data_dict: dict):
    """
    Create an object from a dictionary.

    This replaces pydantic's automatic parsing functionality.
    """
    if not isinstance(data_dict, dict):
        return data_dict

    # Get the class annotations to understand expected types
    import inspect
    if hasattr(cls, '__annotations__'):
        annotations = cls.__annotations__
        kwargs = {}

        for field_name, field_type in annotations.items():
            # Handle field aliasing (like pydantic's Field(alias=...))
            dict_key = field_name

            # Handle special field name mappings
            if field_name == 'for_':
                dict_key = '@for'
            elif field_name in ['id', 'source', 'target', 'x', 'y', 'width', 'height', 'key', 'xmlns']:
                dict_key = f'@{field_name}'
            elif field_name == 'content':
                dict_key = '#text'

            if dict_key in data_dict:
                value = data_dict[dict_key]
                kwargs[field_name] = value
            elif field_name in data_dict:
                kwargs[field_name] = data_dict[field_name]

        # Handle remaining fields that might not be in annotations
        for key, value in data_dict.items():
            if key.startswith('@') and key[1:] in annotations:
                kwargs[key[1:]] = value
            elif key == '#text' and 'content' in annotations:
                kwargs['content'] = value

        return cls(**kwargs)
    else:
        return cls(**data_dict) if data_dict else cls()


# ============================================================================
# XML_PARSER.PY
# ============================================================================

"""Simple XML parser using only standard library."""


def parse_xml_to_dict(xml_string: str) -> Dict[str, Any]:
    """
    Parse XML string to dictionary structure.

    This function replaces xmltodict functionality using only standard library.
    """
    root = ET.fromstring(xml_string)
    # Remove namespace from root tag
    root_tag = root.tag
    if '}' in root_tag:
        root_tag = root_tag.split('}')[1]
    return {root_tag: _element_to_dict(root)}


def _element_to_dict(element: ET.Element) -> Dict[str, Any]:
    """Convert XML element to dictionary."""
    result = {}

    # Add attributes with @ prefix
    if element.attrib:
        for key, value in element.attrib.items():
            # Handle special attribute names
            if key == 'for':
                result['@for'] = value
            else:
                result[f'@{key}'] = value

    # Handle text content
    if element.text and element.text.strip():
        result['#text'] = element.text.strip()

    # Handle child elements
    children = list(element)
    if children:
        for child in children:
            child_dict = _element_to_dict(child)

            # Remove namespace from tag name
            tag_name = child.tag
            if '}' in tag_name:
                tag_name = tag_name.split('}')[1]

            if tag_name in result:
                # Multiple children with same tag - make it a list
                if not isinstance(result[tag_name], list):
                    result[tag_name] = [result[tag_name]]
                result[tag_name].append(child_dict)
            else:
                result[tag_name] = child_dict

    return result


def _convert_numeric_values(data: Any) -> Any:
    """Convert string values to appropriate numeric types where possible."""
    if isinstance(data, dict):
        return {key: _convert_numeric_values(value) for key,
                value in data.items()}
    elif isinstance(data, list):
        return [_convert_numeric_values(item) for item in data]
    elif isinstance(data, str):
        # Try to convert to float
        try:
            if '.' in data:
                return float(data)
            else:
                return int(data)
        except ValueError:
            return data
    return data


def parse(xml_string: str) -> Dict[str, Any]:
    """
    Main parse function that mimics xmltodict.parse().

    Args:
        xml_string: XML content as string

    Returns:
        Dictionary representation of XML
    """
    result = parse_xml_to_dict(xml_string)
    return _convert_numeric_values(result)


# ============================================================================
# CGML_TYPES.PY
# ============================================================================

"""Module contains types for CyberiadaML scheme using standard library only."""


# Type aliases
CGMLVertexType = Literal['choice', 'initial',
                         'final', 'terminate', 'shallowHistory']
CGMLNoteType = Literal['formal', 'informal']
AvailableKeys = DefaultDict[str, List['CGMLKeyNode']]


@dataclass
class Point:
    """Point data class."""
    x: float
    y: float


@dataclass
class Rectangle:
    """Rectangle data class."""
    x: float
    y: float
    width: float
    height: float


@dataclass
class CGMLRectNode:
    """The type represents <rect> node."""
    x: float
    y: float
    width: float
    height: float


@dataclass
class CGMLPointNode:
    """The type represents <point> node."""
    x: float
    y: float


@dataclass
class CGMLDataNode:
    """The type represents <data> node."""
    key: str
    content: Optional[str] = None
    rect: Optional[CGMLRectNode] = None
    point: Optional[Union[CGMLPointNode, List[CGMLPointNode]]] = None


@dataclass
class CGMLKeyNode:
    """The type represents <key> node."""
    id: str
    for_: str
    attr_name: Optional[str] = None
    attr_type: Optional[str] = None


@dataclass
class CGMLEdge:
    """The type represents <edge> node."""
    id: str
    source: str
    target: str
    data: Optional[Union[List[CGMLDataNode], CGMLDataNode]] = None


@dataclass
class CGMLGraph:
    """The type represents <graph> node."""
    id: str
    data: Union[List[CGMLDataNode], CGMLDataNode] = field(default_factory=list)
    edgedefault: Optional[str] = None
    node: Optional[Union[List['CGMLNode'], 'CGMLNode']] = None
    edge: Optional[Union[List[CGMLEdge], CGMLEdge]] = None


@dataclass
class CGMLNode:
    """The type represents <node> node."""
    id: str
    graph: Optional[Union[CGMLGraph, List[CGMLGraph]]] = None
    data: Optional[Union[List[CGMLDataNode], CGMLDataNode]] = None


@dataclass
class CGMLGraphml:
    """The type represents <graphml> node."""
    data: Union[CGMLDataNode, List[CGMLDataNode]]
    xmlns: str
    key: Optional[Union[List[CGMLKeyNode], CGMLKeyNode]] = None
    graph: Optional[Union[List[CGMLGraph], CGMLGraph]] = None


@dataclass
class CGML:
    """Root type of CyberiadaML scheme."""
    graphml: CGMLGraphml


@dataclass
class CGMLBaseVertex:
    """
    The type represents pseudo-nodes.

    type: content from nested <data>-node with key 'dVertex'.
    data: content from nested <data>-node with key 'dName'.
    position: content from nested <data>-node with key 'dGeometry'.
    parent: parent node id.
    """
    type: str
    data: Optional[str] = None
    position: Optional[Union[Point, Rectangle]] = None
    parent: Optional[str] = None


@dataclass
class CGMLState:
    """
    Data class with information about state.

    State is <node>, that not connected with meta node,
    doesn't have data node with key 'dNote'

    Parameters:
    name: content of data node with key 'dName'.
    actions: content of data node with key 'dData'.
    bounds: x, y, width, height properties of data node with key 'dGeometry'.
    parent: parent state id.
    color: content of data node with key 'dColor'.
    unknown_datanodes: all datanodes, whose information is not included in the type.
    """
    name: str
    actions: str
    unknown_datanodes: List[CGMLDataNode]
    parent: Optional[str] = None
    bounds: Optional[Union[Rectangle, Point]] = None
    color: Optional[str] = None


@dataclass
class CGMLComponent:
    """
    Data class with information about component.

    Component is formal note, that includes <data>-node with key 'dName'
    and content 'CGML_COMPONENT'.
    parameters: content of data node with key 'dData'.
    """
    id: str
    type: str
    parameters: Dict[str, str]


@dataclass
class CGMLInitialState(CGMLBaseVertex):
    """
    Data class with information about initial state (pseudo node).

    Initial state is <node>, that contains data node with key 'dVertex'
    and content 'initial'.
    """
    pass


@dataclass
class CGMLShallowHistory(CGMLBaseVertex):
    """
    Data class with information about shallow history node (pseudo node).

    Choice is <node>, that contains data node with key 'dVertex'
    and content 'shallowHistory'.
    """
    pass


@dataclass
class CGMLChoice(CGMLBaseVertex):
    """
    Data class with information about choice node (pseudo node).

    Choice is <node>, that contains data node with key 'dVertex'
    and content 'choice'.
    """
    pass


@dataclass
class CGMLTransition:
    """
    Data class with information about transition(<edge>).

    Parameters:
    source: <edge> source property's content.
    target: <edge> target property's content.
    actions: content of data node with 'dData' key.
    color: content of data node with 'dColor' key.
    position: x, y properties of data node with 'dGeometry' key.
    unknown_datanodes: all datanodes, whose information is not included in the type.
    """
    id: str
    source: str
    target: str
    actions: str
    unknown_datanodes: List[CGMLDataNode]
    color: Optional[str] = None
    position: List[Point] = field(default_factory=list)
    label_position: Optional[Point] = None
    pivot: Optional[str] = None


@dataclass
class CGMLNote:
    """
    Dataclass with information about note.

    Note is <node> containing data node with key 'dNote'
    type: content of <data key="dNote">
    text: content of <data key="dData">
    name: content of <data key="dName">
    position: properties <data key="dGeometry">'s child <point> or <rect>
    unknown_datanodes: all datanodes, whose information is not included in the type.
    """
    name: str
    position: Union[Point, Rectangle]
    text: str
    type: str
    unknown_datanodes: List[CGMLDataNode]
    parent: Optional[str] = None


@dataclass
class CGMLMeta:
    """
    The type represents meta-information from formal note with 'dName' CGML_META.

    id: meta-node id.
    values: information from meta node, exclude required parameters.
    """
    id: str
    values: Dict[str, str]


@dataclass
class CGMLFinal(CGMLBaseVertex):
    """
    The type represents final-states.

    Final state - <node>, that includes dVertex with content 'final'.
    """
    pass


@dataclass
class CGMLTerminate(CGMLBaseVertex):
    """
    The type represents terminate-states.

    Final state - <node>, that includes dVertex with content 'terminate'.
    """
    pass


@dataclass
class CGMLStateMachine:
    """
    The type represents state machine <graph>.

    Contains dict of CGMLStates, where the key is state's id.
    Also contains transitions, components, available keys, notes.

    States doesn't contain components nodes and pseudo-nodes.
    transitions doesn't contain component's transitions.
    """
    platform: str
    meta: CGMLMeta
    standard_version: str
    states: Dict[str, CGMLState]
    transitions: Dict[str, CGMLTransition]
    components: Dict[str, CGMLComponent]
    notes: Dict[str, CGMLNote]
    initial_states: Dict[str, CGMLInitialState]
    finals: Dict[str, CGMLFinal]
    choices: Dict[str, CGMLChoice]
    terminates: Dict[str, CGMLTerminate]
    shallow_history: Dict[str, CGMLShallowHistory]
    unknown_vertexes: Dict[str, CGMLBaseVertex]
    name: Optional[str] = None


@dataclass
class CGMLElements:
    """
    Dataclass with elements of parsed scheme.

    Parameters:
    meta: content of data node with key 'dData' inside meta-node.
    format: content of data node with key 'gFormat'.
    platform: content of meta-data
    keys: dict of KeyNodes, where the key is 'for' attribute.
        Example: { "node": [KeyNode, ...], "edge": [...] }
    """
    state_machines: Dict[str, CGMLStateMachine]
    format: str
    keys: AvailableKeys


# Union type for vertices
Vertex = Union[
    CGMLFinal,
    CGMLChoice,
    CGMLInitialState,
    CGMLTerminate,
    CGMLShallowHistory,
    CGMLBaseVertex
]

defaultSignals = ['unconditionalTransition', 'break']


# ============================================================================
# EVENT_LOOP.PY
# ============================================================================

class EventLoop:
    events: list = []
    called_events: list = []
    current_event_idx = 0
    insert_event_idx = 0

    @staticmethod
    def add_event(event: str, is_called=False):
        """
        Добавляет событие в цикл событий.

        is_called: события, которые будут проверяться в проверочной системе.
        """
        EventLoop.insert_event_idx += 1
        EventLoop.events.insert(
            EventLoop.insert_event_idx,
            event
        )
        if is_called:
            EventLoop.called_events.append(event)

    @staticmethod
    def clear():
        EventLoop.current_event_idx = 0
        EventLoop.events.clear()
        EventLoop.called_events.clear()

    @staticmethod
    def get_event():
        # обнулять где-то надо
        if EventLoop.current_event_idx < len(EventLoop.events):
            event = EventLoop.events[EventLoop.current_event_idx]
            EventLoop.current_event_idx += 1
            EventLoop.insert_event_idx = EventLoop.current_event_idx
            return event
        return None


# ============================================================================
# QHSM.PY
# ============================================================================


# qhsm.py

Q_MAX_DEPTH = 8

# Signals as string names
QEP_EMPTY_SIG_ = "QEP_EMPTY_SIG"
Q_ENTRY_SIG = "entry"
Q_EXIT_SIG = "exit"
Q_INIT_SIG = "Q_INIT_SIG"
Q_VERTEX_SIG = "Q_VERTEX_SIG"
Q_USER_SIG = "Q_USER_SIG"

# Return codes
Q_RET_SUPER = 0
Q_RET_UNHANDLED = 1
Q_RET_HANDLED = 2
Q_RET_IGNORED = 3
Q_RET_TRAN = 4


class QHsm:
    def __init__(self, initial: Optional[Callable[["QHsm", str], int]] = None):
        if initial is None:
            return
        self.current_: Callable[["QHsm", str], int] = initial
        self.effective_: Callable[["QHsm", str], int] = initial
        self.target_: Optional[Callable[["QHsm", str], int]] = None

    def post_init(self, initial: Callable[["QHsm", str], int]):
        self.current_: Callable[["QHsm", str], int] = initial
        self.effective_: Callable[["QHsm", str], int] = initial
        self.target_: Optional[Callable[["QHsm", str], int]] = None


def QHsm_top(me: "QHsm", event: str) -> int:
    return Q_RET_IGNORED


standard_events = [
    QEP_EMPTY_SIG_,
    Q_ENTRY_SIG,
    Q_EXIT_SIG,
    Q_INIT_SIG,
]


def do_transition(me: QHsm) -> None:
    source = me.current_
    effective = me.effective_
    target = me.target_

    while source != effective:
        source(me, standard_events[2])  # Q_EXIT_SIG
        source(me, standard_events[0])  # QEP_EMPTY_SIG
        source = me.effective_

    if source == target:
        source(me, standard_events[2])  # Q_EXIT_SIG
        target(me, standard_events[1])  # Q_ENTRY_SIG
        me.current_ = target
        me.effective_ = target
        me.target_ = None
        return

    path: list = [None] * Q_MAX_DEPTH
    top = 0
    lca = -1

    path[0] = target
    while target != QHsm_top:
        if target is not None:
            target(me, standard_events[0])  # QEP_EMPTY_SIG
            target = me.effective_
            top += 1
            path[top] = target
            if target == source:
                lca = top
                break
        else:
            break

    while lca == -1:
        source(me, standard_events[2])  # Q_EXIT_SIG
        source(me, standard_events[0])  # QEP_EMPTY_SIG
        source = me.effective_
        for i in range(top + 1):
            if path[i] == source:
                lca = i
                break

    target = path[lca]
    if lca == 0 and target is not None:
        target(me, standard_events[1])  # Q_ENTRY_SIG
    for i in range(lca - 1, -1, -1):
        target = path[i]
        if target is not None:
            target(me, standard_events[1])  # Q_ENTRY_SIG

    me.current_ = target
    me.effective_ = target
    me.target_ = None


def QHsm_ctor(me: QHsm, initial: Callable[[QHsm, str], int]) -> None:
    me.current_ = initial
    me.effective_ = initial
    me.target_ = None


def QMsm_init(me: QHsm, event: str) -> None:
    me.current_(me, event)
    me.effective_ = QHsm_top
    do_transition(me)


def QMsm_dispatch(me: QHsm, event: str) -> int:
    result = me.current_(me, event)
    while result == Q_RET_SUPER:
        result = me.effective_(me, event)
    if result == Q_RET_TRAN:
        do_transition(me)
    elif result in (Q_RET_HANDLED, Q_RET_UNHANDLED, Q_RET_IGNORED):
        me.effective_ = me.current_
    return result


def QMsm_simple_dispatch(me: QHsm, signal: str) -> int:
    return QMsm_dispatch(me, signal)

# --- Macro equivalents from qhsm.hpp as Python functions ---


def Q_UNHANDLED() -> int:
    return Q_RET_UNHANDLED


def Q_HANDLED() -> int:
    return Q_RET_HANDLED


def Q_TRAN(me: QHsm, target: Callable[[QHsm, str], int]) -> int:
    me.target_ = target
    return Q_RET_TRAN


def Q_SUPER(me: QHsm, super_handler: Callable[[QHsm, str], int]) -> int:
    me.effective_ = super_handler
    return Q_RET_SUPER


def QMSM_INIT(me: QHsm, event: str) -> None:
    QMsm_init(me, event)


def QMSM_DISPATCH(me: QHsm, event: str) -> int:
    return QMsm_dispatch(me, event)


def SIMPLE_DISPATCH(me: QHsm, sig: str) -> None:
    QMsm_dispatch(me, sig)


def SIGNAL_DISPATCH(me: QHsm, sig: str) -> None:
    QMsm_dispatch(me, sig)


def PASS_EVENT_TO(obj: QHsm, e: str) -> None:
    QMsm_dispatch(obj, e)


# ============================================================================
# COMPONENTS.PY
# ============================================================================
class SchemeComponent(ABC):
    def __init__(self, __name: str, **kwargs):
        self.name = __name

    def get_sm_options(self, options: dict):
        ...
        # raise NotImplementedError("This method should be overridden in subclasses")

    def loop_action(self):
        ...

# Все классы компонентов кладутся сюда


@dataclass
class CyberBearSignal:
    type: Literal['ears', 'ir']
    value: int


class CyberBear:
    """Класс для хранения состояния КиберМишки."""
    heart = [
        [0, 0, 0, 0, 0],
        [0, 0, 0, 0, 0],
        [0, 100, 0, 100, 0],
        [100, 100, 100, 100, 100],
        [0, 100, 100, 100, 0],
        [0, 0, 100, 0, 0],
        [0, 0, 0, 0, 0],
    ]
    sad = [
        [0, 0, 0, 0, 0],
        [0, 0, 0, 0, 0],
        [0, 100, 0, 100, 0],
        [0, 0, 0, 0, 0],
        [0, 100, 100, 100, 0],
        [100, 0, 0, 0, 100],
        [0, 0, 0, 0, 0],
    ]

    empty = [
        [0, 0, 0, 0, 0],
        [0, 0, 0, 0, 0],
        [0, 0, 0, 0, 0],
        [0, 0, 0, 0, 0],
        [0, 0, 0, 0, 0],
        [0, 0, 0, 0, 0],
        [0, 0, 0, 0, 0],
    ]

    def __init__(self):
        # Цвет левого глаза (RGBK)
        self.left_eye = [0, 0, 0, 0]

        # Цвет правого глаза (RGBK)
        self.right_eye = [0, 0, 0, 0]

        # Матрица светодиодов 7x5 (7 строк, 5 столбцов)
        # Создаем в правильном порядке: [rows][cols]
        self.matrix = [[0 for _ in range(5)] for _ in range(7)]

        # Callback для обновления визуализации
        self.on_state_changed: Optional[Callable[[], None]] = None
        self.__signals: Optional[List[CyberBearSignal]] = []

    # Сравнить текущую матрицу с полученной
    def is_matrix_equal(self, matrix: list):
        if (
            len(matrix) != len(self.matrix) or
            len(matrix[0]) != len(self.matrix[0])
        ):
            raise Exception('Размерности не совпадают!')

        for i in range(len(matrix)):
            for j in range(len(matrix[0])):
                if matrix[i][j] != self.matrix[i][j]:
                    return False
        return True

    def check_pattern(self):
        print('check pattern!')
        if self.is_matrix_equal(self.heart):
            print('heart!')
            EventLoop.add_event('heart', True)
        elif self.is_matrix_equal(self.sad):
            EventLoop.add_event('sad', True)
            print('sads!')
        elif self.is_matrix_equal(self.empty):
            EventLoop.add_event('empty', True)
            print('empty!')
        else:
            EventLoop.add_event('unknown pattern', True)
            print('unknown pattern!')

    def check_color(self):
        check_colors = [
            (Eyes.colors.get('&ColorGreen'), 'green'),
            (Eyes.colors.get('&ColorWhite'), 'white'),
            (Eyes.colors.get('&ColorRed'), 'red'),
        ]
        for color, signal in check_colors:
            left = False
            right = False
            if self.left_eye == color:
                left = True
            if self.right_eye == color:
                right = True
            if left and right:
                EventLoop.add_event(signal, True)
                print(f'detected {signal}!')
                return

    @property
    def signals(self):
        if self.__signals is None:
            raise Exception('Отсутствют сигналы')
        return self.__signals

    @signals.setter
    def signals(self, signals: List[CyberBearSignal]):
        self.__signals = signals

    def get_signal(self) -> CyberBearSignal | None:
        if len(self.signals) == 0:
            return None
        return self.signals.pop(0)

    def add_signal(self, signal: CyberBearSignal):
        self.signals.insert(0, signal)

    def set_left_eye(self, r: int, g: int, b: int, k: int):
        """Установить цвет левого глаза."""
        self.left_eye = [r, g, b, k]
        self.check_color()
        if self.on_state_changed:
            self.on_state_changed()

    def set_right_eye(self, r: int, g: int, b: int, k: int):
        """Установить цвет правого глаза."""
        self.right_eye = [r, g, b, k]
        self.check_color()
        if self.on_state_changed:
            self.on_state_changed()

    def set_matrix_pixel(self, row: int, col: int, value: int):
        """Установить значение пикселя матрицы."""
        if 0 <= row < 7 and 0 <= col < 5:
            self.matrix[row][col] = value

    def set_pattern(self, pattern: list):
        """Установить шаблон на матрицу из одномерного списка.
        Размер матрицы 7x5 (7 строк, 5 столбцов).
        Паттерн приходит как одномерный массив из 35 элементов.
        """
        print('set pattern!')
        if len(pattern) != 35:  # 7x5 = 35 элементов
            raise ValueError("Pattern must contain exactly 35 elements")

        # Конвертируем одномерный массив в двумерный построчно
        for i in range(35):
            row = i // 5  # Получаем индекс строки (0-6)
            col = i % 5   # Получаем индекс столбца (0-4)
            self.set_matrix_pixel(row, col, pattern[i])

        if self.on_state_changed:
            self.on_state_changed()

        self.check_pattern()

    def get_matrix_pixel(self, row: int, col: int) -> int:
        """Получить значение пикселя матрицы."""
        if 0 <= row < 7 and 0 <= col < 5:
            return self.matrix[row][col]
        raise Exception("Index is out of bounds!!")

    def clear_matrix(self):
        """Очистить матрицу."""
        self.matrix = [[0 for _ in range(5)] for _ in range(7)]
        self.check_pattern()
        if self.on_state_changed:
            self.on_state_changed()

    def clear_eyes(self):
        """Выключить оба глаза."""
        self.left_eye = [0, 0, 0, 0]
        self.right_eye = [0, 0, 0, 0]
        if self.on_state_changed:
            self.on_state_changed()


class Timer(SchemeComponent):
    """Component for working with time intervals."""

    def __init__(self, __name: str, **kwargs):
        super().__init__(__name, **kwargs)
        self._start_time = None
        self._interval = 0
        self._enabled = True
        self.millis = 0

    def start(self, interval: int):
        """Start timer with given interval in milliseconds."""
        if self._enabled:
            print('start!')
            self.millis = interval
            self._interval = interval / 1000.0  # Convert to seconds
            self._start_time = time.time()

    def stop(self):
        """Stop the timer."""
        self._start_time = None

    def pause(self):
        """Pause the timer."""
        self._enabled = False

    def resume(self):
        """Resume the timer."""
        self._enabled = True

    def reset(self):
        """Reset the timer to initial state."""
        self._start_time = None
        self._interval = 0
        self._enabled = True

    @property
    def time(self) -> float:
        """Get elapsed time in milliseconds."""
        if self._start_time is None:
            return 0
        return (time.time() - self._start_time) * 1000

    @property
    def difference(self) -> float:
        """Get remaining time in milliseconds."""
        if self._start_time is None:
            return 0
        elapsed = time.time() - self._start_time
        return max(0, (self._interval - elapsed) * 1000)

    @property
    def expired(self) -> bool:
        """Check if timer has expired."""
        if not self._enabled or self._start_time is None:
            return False
        return time.time() - self._start_time >= self._interval

    def timeout(self) -> None:
        if self.expired:
            EventLoop.add_event(f'{self.name}.timeout')
            self.start(int(self.millis))

    def loop_actions(self):
        self.timeout()


class Accel(SchemeComponent):
    """Компонент для определения положения."""

    def __init__(self, __name: str, **kwargs):
        super().__init__(__name, **kwargs)
        self.orientation = 0
        self.ACCEL_DIR_DN = 1  # На ушах
        self.ACCEL_DIR_UP = 2  # На ногах
        self.ACCEL_DIR_LEFT = 3  # На левом боку
        self.ACCEL_DIR_RIGHT = 4  # На правом боку
        self.ACCEL_DIR_FACE = 5  # На спине
        self.ACCEL_DIR_BACK = 6  # На животе

    def isOrientationChanged(self):
        # Событие когда положение меняется
        EventLoop.add_event(f'{self.name}.isOrientationChanged')


class Button(SchemeComponent):
    """Компонент кнопки."""

    def __init__(self, __name: str, **kwargs):
        super().__init__(__name, **kwargs)
        self.pin = kwargs.get('pin', 1)
        self.value = 0
        self._pressed = False
        self._released = False
        self._clicked = False

    def isPressed(self):
        if self._pressed:
            EventLoop.add_event(f'{self.name}.isPressed')
            return True
        return False

    def isReleased(self):
        if self._released:
            EventLoop.add_event(f'{self.name}.isReleased')
            return True
        return False

    def clicked(self):
        if self._clicked:
            EventLoop.add_event(f'{self.name}.clicked')
            return True
        return False


class EarsBytes(SchemeComponent):
    """Компонент для получения байтов по акустическому каналу"""

    def __init__(self, __name: str, **kwargs):
        super().__init__(__name, **kwargs)
        self.__bear: CyberBear | None = None
        self.value = 0

    @property
    def bear(self):
        if self.__bear is None:
            raise Exception('Нет инстанса CyberBear в компоненте Eyes')
        return self.__bear

    def get_sm_options(self, options: dict):
        """Инициализация компонента с параметрами из state machine."""
        self.__bear = options.get('CyberBear')
        if self.__bear is None:
            raise ValueError(
                "CyberBear instance is required for Ears component!")

    def loop_actions(self):
        signal = self.bear.get_signal()
        if signal is None:
            return
        if signal.type == 'ears':
            EventLoop.add_event(f'{self.name}.isByteReceived')
            self.value = int(signal.value)
        else:
            self.bear.add_signal(signal)


class PhotoDiodeBytes(SchemeComponent):
    """Компонент для получения байтов по инфрокрасному каналу"""

    def __init__(self, __name: str, **kwargs):
        super().__init__(__name, **kwargs)
        self.__bear: CyberBear | None = None
        self.value = 0

    @property
    def bear(self):
        if self.__bear is None:
            raise Exception('Нет инстанса CyberBear в компоненте IRBytes')
        return self.__bear

    def get_sm_options(self, options: dict):
        """Инициализация компонента с параметрами из state machine."""
        self.__bear = options.get('CyberBear')
        if self.__bear is None:
            raise ValueError(
                "CyberBear instance is required for Ears component!")

    def loop_actions(self):
        signal = self.bear.get_signal()
        if signal is None:
            return
        if signal.type == 'ir':
            print(f'{self.name}.isByteReceived!')
            EventLoop.add_event(f'{self.name}.isByteReceived')
            self.value = int(signal.value)
            print(self.value)
        else:
            self.bear.add_signal(signal)


class Speaker(SchemeComponent):
    """Компонент пищалки."""

    def __init__(self, __name: str, **kwargs):
        super().__init__(__name, **kwargs)
        self._playing = False

    def isNoteEnd(self):
        if not self._playing:
            EventLoop.add_event(f'{self.name}.isNoteEnd')
            return True
        return False

    def setupNote(self, note: str, amplitude: int, time: int):
        pass

    def setupFrequency(self, freq: int, amplitude: int, time: int):
        pass

    def play(self):
        self._playing = True

    def stop(self):
        self._playing = False


class SpeakerSound(SchemeComponent):
    """Компонент для готовых звуков."""

    def __init__(self, __name: str, **kwargs):
        super().__init__(__name, **kwargs)
        self._playing = False

    def isSoundEnd(self):
        if not self._playing:
            EventLoop.add_event(f'{self.name}.isSoundEnd')
            return True
        return False

    def setupSound(self, sound: str, time: int):
        pass

    def play(self):
        self._playing = True

    def stop(self):
        self._playing = False


class PhotoDiode(SchemeComponent):
    """Компонент ИК-фотодиода (нос)."""

    def __init__(self, __name: str, **kwargs):
        super().__init__(__name, **kwargs)
        self.value = 0
        self.threshold = 0
        self._enabled = True

    def isThresholdValue(self):
        if self._enabled and self.value >= self.threshold:
            EventLoop.add_event(f'{self.name}.isThresholdValue')
            return True
        return False

    def setupEvent(self, threshold: int):
        self.threshold = threshold

    def off(self):
        self._enabled = False

    def on(self):
        self._enabled = True

    def get_sm_options(self, options: dict):
        self.threshold = options.get('photodiode_threshold', self.threshold)


class Eyes(SchemeComponent):
    """Компонент светодиодных глаз."""

    colors: dict[str, tuple[int, int, int, int]] = {
        "&ColorRed": (14, 0, 0, 0),
        "&ColorReddish": (1, 0, 0, 50),
        "&ColorOrange": (21, 1, 0, 0),
        "&ColorGreen": (0, 10, 0, 0),
        "&ColorLime": (6, 4, 0, 0),
        "&ColorBlue": (0, 0, 20, 0),
        "&ColorCyan": (0, 12, 10, 0),
        "&ColorPink": (10, 0, 2, 0),
        "&ColorPurple": (6, 0, 10, 0),
        "&ColorYellow": (10,  2,  0,  0),
        "&ColorWhite": (15, 4, 1, 0),
        "&ColorBlack": (0, 0, 0, 99),
        "&ColorPerfectWhite": (10, 10, 10, 0)
    }

    def __init__(self, __name: str, **kwargs):
        super().__init__(__name, **kwargs)
        pin = kwargs.get('pin', 1)
        self.is_left = pin == 2  # Пин 2 - левый глаз, Пин 1 - правый глаз
        self.__bear: CyberBear | None = None
        self.pin = int(pin)

    @property
    def bear(self):
        if self.__bear is None:
            raise Exception('Нет инстанса CyberBear в компоненте Eyes')
        return self.__bear

    def get_sm_options(self, options: dict):
        """Инициализация компонента с параметрами из state machine."""
        self.__bear = options.get('CyberBear')
        if self.__bear is None:
            raise ValueError(
                "CyberBear instance is required for Eyes component!")

    def setColorPalette(self, color: str):
        rgbk_color = self.colors.get(color)
        if rgbk_color is None:
            return
        r, g, b, k = rgbk_color
        if self.pin == 2:
            print('set_left_eye!')
            self.bear.set_left_eye(r, g, b, k)
        elif self.pin == 1:
            print('set_right_eye!')
            self.bear.set_right_eye(r, g, b, k)

    def setColor(self, r: int, g: int, b: int, k: int):
        # Пин 1 - правый глаз, Пин 2 - левый глаз
        if self.pin == 2:
            self.bear.set_left_eye(r, g, b, k)
        elif self.pin == 1:
            self.bear.set_right_eye(r, g, b, k)

    def off(self):
        # Пин 1 - правый глаз, Пин 2 - левый глаз
        if self.pin == 2:
            self.bear.set_left_eye(0, 0, 0, 0)
        elif self.pin == 1:
            self.bear.set_right_eye(0, 0, 0, 0)


class Microphone(SchemeComponent):
    """Компонент микрофона."""

    def __init__(self, __name: str, **kwargs):
        super().__init__(__name, **kwargs)
        self.value = 0
        self._threshold = 0
        self._cooldown = 0
        self._enabled = True

    def isLoudSound(self):
        if self._enabled and self.value >= self._threshold:
            EventLoop.add_event(f'{self.name}.isLoudSound')
            return True
        return False

    def setCooldown(self, interval: int):
        self._cooldown = interval

    def setupEvent(self, volume: int):
        self._threshold = volume

    def off(self):
        self._enabled = False

    def on(self):
        self._enabled = True

    def get_sm_options(self, options: dict):
        self.value = options.get('microphone_value', self.value)


class IR(SchemeComponent):
    """Компонент ИК-светодиода."""

    def __init__(self, __name: str, **kwargs):
        super().__init__(__name, **kwargs)
        self._enabled = False

    def on(self):
        self._enabled = True

    def off(self):
        self._enabled = False


class Matrix(SchemeComponent):
    """Компонент матрицы светодиодов."""

    def __init__(self, __name: str, **kwargs):
        super().__init__(__name, **kwargs)
        self.__bear: CyberBear | None = None

    @property
    def bear(self):
        if self.__bear is None:
            raise Exception('Нет инстанса CyberBear в компоненте Matrix')
        return self.__bear

    def get_sm_options(self, options: dict):
        """Инициализация компонента с параметрами из state machine."""
        self.__bear = options.get('CyberBear')
        if self.__bear is None:
            raise ValueError(
                "CyberBear instance is required for Matrix component!")

    def setPixel(self, row: int, col: int, brightness: int):
        if 0 <= row < 5 and 0 <= col < 7:
            self.bear.set_matrix_pixel(row, col, brightness)
        else:
            raise Exception('Matrix - out of bounds!')

    def setPattern(self, pattern: list[int]):
        """Установить шаблон на матрицу.

        Args:
            pattern: Одномерный список из 35 элементов (5 строк x 7 столбцов)
        """
        print('set pattern!!!')
        if self.bear is None:
            return
        self.bear.set_pattern(pattern)
        print(f'Установлен паттерн на матрице {pattern}')

    def changePatternBright(self, mode: str, brightness: int):
        for row in range(5):
            for col in range(7):
                current = self.bear.get_matrix_pixel(row, col)
                if mode == "ALL_LEDS" or \
                   (mode == "ON_LEDS" and current > 0) or \
                   (mode == "OFF_LEDS" and current == 0):
                    self.bear.set_matrix_pixel(row, col, brightness)

    def clear(self):
        print('clear!!!')
        self.bear.clear_matrix()


class MatrixMask(SchemeComponent):
    """Компонент для масок матрицы."""

    def __init__(self, __name: str, **kwargs):
        super().__init__(__name, **kwargs)
        self.__bear: CyberBear | None = None

    @property
    def bear(self):
        if self.__bear is None:
            raise Exception('Нет инстанса CyberBear в компоненте Matrix')
        return self.__bear

    def get_sm_options(self, options: dict):
        """Инициализация компонента с параметрами из state machine."""
        self.__bear = options.get('CyberBear')
        if self.__bear is None:
            raise ValueError(
                "CyberBear instance is required for MatrixMask component!")

    def maskPixel(self, row: int, col: int, value: int, op: str):
        if 0 <= row < 5 and 0 <= col < 7:
            current = self.bear.get_matrix_pixel(row, col)
            if op == "AND":
                self.bear.set_matrix_pixel(row, col, current & value)
            elif op == "OR":
                self.bear.set_matrix_pixel(row, col, current | value)
            elif op == "XOR":
                self.bear.set_matrix_pixel(row, col, current ^ value)

    def maskPattern(self, pattern, op: str):
        # Предполагается, что pattern - это список списков 5x7
        for row in range(5):
            for col in range(7):
                if row < len(pattern) and col < len(pattern[row]):
                    self.maskPixel(row, col, pattern[row][col], op)
        print(pattern)
# TODO: Матрица анимация


class MatrixAnimation(SchemeComponent):
    """Компонент для анимации матрицы."""

    def __init__(self, __name: str, **kwargs):
        super().__init__(__name, **kwargs)
        self._animation_finished = False

    def AnimationFinished(self):
        if self._animation_finished:
            EventLoop.add_event(f'{self.name}.AnimationFinished')
            return True
        return False

    def setFrame(self, pattern, time: int):
        # Установка кадра анимации
        pass


class MatrixPicture(SchemeComponent):
    """Компонент для готовых картинок на матрице."""
    pictures: dict[str, list[int]] = {
        "heart": [
            0, 0, 0, 0, 0,
            0, 100, 0, 100, 0,
            100, 100, 100, 100, 100,
            100, 100, 100, 100, 100,
            0, 100, 100, 100, 0,
            0, 0, 100, 0, 0,
            0, 0, 0, 0, 0,
        ],
        "note": [
            0, 0, 0, 0, 0,
            0, 0, 100, 0, 0,
            0, 0, 100, 100, 0,
            0, 0, 100, 0, 100,
            100, 100, 100, 0, 0,
            100, 100, 100, 0, 0,
            0, 0, 0, 0, 0,
        ],
        "smile": [
            0, 0, 0, 0, 0,
            0, 0, 0, 0, 0,
            0, 100, 0, 100, 0,
            0, 0, 0, 0, 0,
            100, 0, 0, 0, 100,
            0, 100, 100, 100, 0,
            0, 0, 0, 0, 0,
        ],
        "sadness": [
            0, 0, 0, 0, 0,
            0, 0, 0, 0, 0,
            0, 100, 0, 100, 0,
            0, 0, 0, 0, 0,
            0, 100, 100, 100, 0,
            100, 0, 0, 0, 100,
            0, 0, 0, 0, 0,
        ],
        "cross": [
            0, 0, 0, 0, 0,
            100, 0, 0, 0, 100,
            0, 100, 0, 100, 0,
            0, 0, 100, 0, 0,
            0, 100, 0, 100, 0,
            100, 0, 0, 0, 100,
            0, 0, 0, 0, 0,
        ],
        "square": [
            100, 100, 100, 100, 100,
            100, 0, 0, 0, 100,
            100, 0, 0, 0, 100,
            100, 0, 0, 0, 100,
            100, 0, 0, 0, 100,
            100, 0, 0, 0, 100,
            100, 100, 100, 100, 100,
        ],
        "rhombus": [
            0, 0, 0, 0, 0,
            0, 0, 100, 0, 0,
            0, 100, 0, 100, 0,
            100, 0, 0, 0, 100,
            0, 100, 0, 100, 0,
            0, 0, 100, 0, 0,
            0, 0, 0, 0, 0,
        ]
    }

    def __init__(self, __name: str, **kwargs):
        super().__init__(__name, **kwargs)
        self._current_picture = None
        self.__bear: CyberBear | None = None

    def get_sm_options(self, options: dict):
        """Инициализация компонента с параметрами из state machine."""
        self.__bear = options.get('CyberBear')
        if self.__bear is None:
            raise ValueError(
                "CyberBear instance is required for MatrixPicture component!")

    @property
    def bear(self):
        if self.__bear is None:
            raise Exception('Нет инстанса CyberBear в компоненте Matrix')
        return self.__bear

    def draw(self, picture: str):
        pattern = self.pictures.get(picture)
        if pattern is None:
            return
        self.bear.set_pattern(pattern)
        print(f'Draw {picture}')


class Random(SchemeComponent):
    """Компонент генератора случайных чисел."""

    def __init__(self, __name: str, **kwargs):
        super().__init__(__name, **kwargs)
        self.value = 0  # Со знаком
        self.uValue = 0  # Без знака
        self._seed = None

    def setSeed(self, seed: int):
        self._seed = seed
        random.seed(seed)

    def doRandom(self):
        self.value = random.randint(-2147483648, 2147483647)
        self.uValue = random.randint(0, 4294967295)

    def doRangeRandom(self, start: int, end: int):
        self.value = random.randint(start, end-1)
        self.uValue = self.value if self.value >= 0 else 0


class CalcInt(SchemeComponent):
    """Компонент калькулятора целых чисел."""

    def __init__(self, __name: str, **kwargs):
        super().__init__(__name, **kwargs)
        self.value = 0

    def set(self, value: int):
        self.value = value

    def add(self, x: int):
        try:
            result = self.value + x
            if -2147483648 <= result <= 2147483647:
                self.value = result
            else:
                EventLoop.add_event(f'{self.name}.isOverflow')
        except OverflowError:
            EventLoop.add_event(f'{self.name}.isOverflow')

    def sub(self, x: int):
        try:
            result = self.value - x
            if -2147483648 <= result <= 2147483647:
                self.value = result
            else:
                EventLoop.add_event(f'{self.name}.isOverflow')
        except OverflowError:
            EventLoop.add_event(f'{self.name}.isOverflow')

    def mul(self, x: int):
        try:
            result = self.value * x
            if -2147483648 <= result <= 2147483647:
                self.value = result
            else:
                EventLoop.add_event(f'{self.name}.isOverflow')
        except OverflowError:
            EventLoop.add_event(f'{self.name}.isOverflow')

    def div(self, x: int):
        if x == 0:
            EventLoop.add_event(f'{self.name}.isZeroDivision')
        else:
            self.value //= x

    def mod(self, x: int):
        if x == 0:
            EventLoop.add_event(f'{self.name}.isZeroDivision')
        else:
            self.value %= x

    def neg(self):
        try:
            result = -self.value
            if -2147483648 <= result <= 2147483647:
                self.value = result
            else:
                self._overflow = True
        except OverflowError:
            EventLoop.add_event(f'{self.name}.isOverflow')

    def abs(self):
        try:
            result = abs(self.value)
            if result <= 2147483647:
                self.value = result
            else:
                self._overflow = True
        except OverflowError:
            EventLoop.add_event(f'{self.name}.isOverflow')

    def bitAnd(self, x: int):
        self.value &= x

    def bitOr(self, x: int):
        self.value |= x

    def bitXor(self, x: int):
        self.value ^= x

    def bitNot(self):
        self.value = ~self.value

    def shiftLeft(self, n: int):
        try:
            result = self.value << n
            if -2147483648 <= result <= 2147483647:
                self.value = result
            else:
                EventLoop.add_event(f'{self.name}.isOverflow')
        except OverflowError:
            EventLoop.add_event(f'{self.name}.isOverflow')

    def shiftRight(self, n: int):
        self.value >>= n

# Компонент Считыватель:
# Действие «Принять символ»
# Событие «Есть символ»
# Событие «Строка закончилась»
# Атрибут «Принятый символ»

# Компонент Сигнал:
# Действие «Импульс А»
# Действие «Импульс Б»
# Действие «Импульс В»

# Компонент Счётчик:
# Действие «Установить»
# Действие «Увеличить»
# Действие «Уменьшить»
# Действие «Очистить»
# Атрибут «Значение»


class Reader(SchemeComponent):
    # signals: char_accepted
    # signals: line_finished
    def __init__(self, __name: str, **kwargs):
        super().__init__(__name, **kwargs)
        self.message = ''
        self.current_char = ''
        self.index = 0

    def get_sm_options(self, options: dict):
        self.message = options['message']
        # self.current_char = self.message[0]

    def read(self):
        if self.index < len(self.message):
            self.current_char = self.message[self.index]
            self.index += 1
            EventLoop.add_event(f'{self.name}.char_accepted')
            return True
        else:
            EventLoop.add_event(f'{self.name}.line_finished')
            return False


class Impulse(SchemeComponent):
    def impulseA(self):
        # print('impulseA')
        EventLoop.add_event('impulseA', True)

    def impulseB(self):
        # print('impulseB')
        EventLoop.add_event('impulseB', True)

    def impulseC(self):
        # print('impulseC')
        EventLoop.add_event('impulseC', True)


class Counter(SchemeComponent):
    def __init__(self, __name: str, **kwargs):
        super().__init__(__name, **kwargs)
        self.value = 0

    def set(self, value: int):
        self.value = int(value)

    def add(self, value: int):
        self.value += int(value)

    def sub(self, value: int):
        self.value -= int(value)

    def clear(self):
        self.value = 0

# Компонент Свое событие
# Событие Вызвано
# Действие Вызвать

# Компонент Компас
# Атрибут Ориентация (С, Ю, З, В)
# Атрибут Координата X
# Атрибут Координата Y

# Компонент Цветы
# Действие Высадить, параметр Тип [роза, мята, василек]

# Компонент Движение
# Действие Вперёд
# Действие Назад
# Действие Повернуть влево
# Действие Повернуть вправо

# Компонент Сенсор
# Действие Осмотреть стены
# Действия Осмотреть растение
# Событие Растение осмотрено
# Событие Стена спереди
# Событие Стена сзади
# Событие Стена слева
# Событие Стена справа
# Атрибут Стена спереди = 1/0
# Атрибут Стена сзади = 1/0
# Атрибут Стена слева = 1/0
# Атрибут Стена справа = 1/0
# Атрибут Высаженные цветы = 0/1/2/3 (нет/роза/мята/василек)


class GardenerCrashException(Exception):
    ...


class Gardener:

    def __init__(self, N: int, M: int, with_walls: bool = False):
        self.N = N
        self.M = M
        self.field = [[0 for _ in range(N)] for _ in range(M)]
        # if with_walls:
        #     self.generate_walls()
        self.SOUTH = 0
        self.NORTH = 1
        self.WEST = 2
        self.EAST = 3

        self.ROSE = 1
        self.MINT = 2
        self.VASILEK = 3
        self.EMPTY = 0

        self.orientation = self.SOUTH
        self.x = 0
        self.y = 0

        # Атрибуты наличия стен
        self.wall_left_value = 0
        self.wall_right_value = 0
        self.wall_straight_value = 0
        self.wall_back_value = 0

    def set_field(self, field: list):
        self.field = deepcopy(field)
        self.M = len(field)
        self.N = len(field[0])

    def generate_walls(self, wall_fraction: float = 0.2, max_attempts: int = 1000):
        N, M = self.N, self.M
        total_cells = N * M
        num_walls = int(total_cells * wall_fraction)
        attempts = 0
        walls_placed = 0
        # Список всех координат кроме стартовой (0,0)
        coords = [(i, j) for i in range(M)
                  for j in range(N) if not (i == 0 and j == 0)]
        random.shuffle(coords)

        def is_connected(field):
            # BFS из (0,0), считаем количество достижимых клеток
            visited = [[False for _ in range(N)] for _ in range(M)]
            q = deque()
            q.append((0, 0))
            visited[0][0] = True
            reachable = 1
            while q:
                x, y = q.popleft()
                for dx, dy in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
                    nx, ny = x+dx, y+dy
                    if 0 <= ny < M and 0 <= nx < N and not visited[ny][nx] and field[ny][nx] != -1:
                        visited[ny][nx] = True
                        q.append((nx, ny))
                        reachable += 1
            # Количество пустых клеток
            empty_cells = sum(field[i][j] != -1 for i in range(M)
                              for j in range(N))
            return reachable == empty_cells
        for x, y in coords:
            if walls_placed >= num_walls or attempts >= max_attempts:
                break
            if self.field[y][x] == 0:
                self.field[y][x] = -1
                if is_connected(self.field):
                    walls_placed += 1
                else:
                    self.field[y][x] = 0
            attempts += 1
        # print(f"Walls placed: {walls_placed}")

    def update_walls(self):
        # Обновляет значения wall_left_value, wall_right_value, wall_straight_value, wall_back_value
        dir_left = {
            self.NORTH: self.WEST,
            self.WEST: self.SOUTH,
            self.SOUTH: self.EAST,
            self.EAST: self.NORTH
        }[self.orientation]
        dir_right = {
            self.NORTH: self.EAST,
            self.EAST: self.SOUTH,
            self.SOUTH: self.WEST,
            self.WEST: self.NORTH
        }[self.orientation]
        dir_back = {
            self.NORTH: self.SOUTH,
            self.SOUTH: self.NORTH,
            self.EAST: self.WEST,
            self.WEST: self.EAST
        }[self.orientation]
        self.wall_left_value = 1 if self._wall_in_direction(dir_left) else 0
        self.wall_right_value = 1 if self._wall_in_direction(dir_right) else 0
        self.wall_straight_value = 1 if self._wall_in_direction(
            self.orientation) else 0
        self.wall_back_value = 1 if self._wall_in_direction(dir_back) else 0

    def wall_left(self):
        return self.wall_left_value == 1

    def wall_right(self):
        return self.wall_right_value == 1

    def wall_straight(self):
        return self.wall_straight_value == 1

    def wall_back(self):
        return self.wall_back_value == 1

    def get_current_flower(self):
        return self.field[self.y][self.x]

    def _wall_in_direction(self, direction):
        dx, dy = 0, 0
        if direction == self.NORTH:
            dx, dy = 0, -1
        elif direction == self.SOUTH:
            dx, dy = 0, 1
        elif direction == self.WEST:
            dx, dy = -1, 0
        elif direction == self.EAST:
            dx, dy = 1, 0
        nx, ny = self.x + dx, self.y + dy
        if 0 <= ny < self.M and 0 <= nx < self.N:
            return self.field[ny][nx] == -1
        else:
            return True


class Sensor(SchemeComponent):
    def __init__(self, __name: str, **kwargs):
        super().__init__(__name, **kwargs)
        self.gardener = None
        self.flower = -1

    @property
    def rose(self):
        if self.gardener is None:
            raise ValueError('Gardener is None!')
        return self.gardener.ROSE

    @property
    def mint(self):
        if self.gardener is None:
            raise ValueError('Gardener is None!')
        return self.gardener.MINT

    @property
    def vasilek(self):
        if self.gardener is None:
            raise ValueError('Gardener is None!')
        return self.gardener.VASILEK

    @property
    def empty(self):
        if self.gardener is None:
            raise ValueError('Gardener is None!')
        return self.gardener.EMPTY

    @property
    def wall_back(self):
        if self.gardener is None:
            raise ValueError('Gardener is required for Compass work!')
        return self.gardener.wall_back_value

    @property
    def wall_left(self):
        if self.gardener is None:
            raise ValueError('Gardener is required for Compass work!')
        return self.gardener.wall_left_value

    @property
    def wall_straight(self):
        if self.gardener is None:
            raise ValueError('Gardener is required for Compass work!')
        return self.gardener.wall_straight_value

    @property
    def wall_right(self):
        if self.gardener is None:
            raise ValueError('Gardener is required for Compass work!')
        return self.gardener.wall_right_value

    @property
    def north(self):
        if self.gardener is None:
            raise ValueError('Gardener is required for Compass work!')
        return self.gardener.NORTH

    def get_sm_options(self, options: dict):
        gardener = options.get('gardener')

        if gardener is None:
            raise ValueError('Gardener is None!')

        self.gardener = gardener
        self.flower = gardener.get_current_flower()

    def search_walls(self):
        if self.gardener is None:
            raise ValueError('Gardener is None!')
        self.gardener.update_walls()
        got_walls = False
        if self.gardener.wall_right():
            # EventLoop.add_event(f'{self.name}.wall_right')
            got_walls = True
        if self.gardener.wall_back():
            # EventLoop.add_event(f'{self.name}.wall_back')
            got_walls = True
        if self.gardener.wall_left():
            # EventLoop.add_event(f'{self.name}.wall_left')
            got_walls = True
        if self.gardener.wall_straight():
            # EventLoop.add_event(f'{self.name}.wall_straight')
            got_walls = True
        if got_walls:
            EventLoop.add_event(f'{self.name}.got_walls')
        else:
            EventLoop.add_event(f'{self.name}.no_walls')

    def search_flowers(self):
        if self.gardener is None:
            raise ValueError('Gardener is None!')
        self.flower = self.gardener.get_current_flower()
        EventLoop.add_event(f'{self.name}.flowers_scanned')


class UserSignal(SchemeComponent):
    def __init__(self, __name: str, **kwargs):
        super().__init__(__name, **kwargs)

    def call(self):
        EventLoop.add_event(f'{self.name}.isCalled', True)


class Flower(SchemeComponent):
    def __init__(self, __name: str, **kwargs):
        super().__init__(__name, **kwargs)
        self.gardener = None

    def get_sm_options(self, options: dict):
        gardener = options.get('gardener')

        if gardener is None:
            raise ValueError('Gardener is None!')

        self.gardener = gardener

    def plant(self, flower: int):
        if self.gardener is None:
            raise ValueError('Gardener is None!')
        # print('---------')
        # pprint(self.gardener.field)

        if self.gardener.field[self.gardener.y][self.gardener.x] != 0:
            raise Exception('Ошибка! Клетка уже засажена')
        self.gardener.field[self.gardener.y][self.gardener.x] = flower
        # pprint(self.gardener.field)
# Компонент Движение
# Действие Вперёд
# Действие Назад
# Действие Повернуть влево
# Действие Повернуть вправо


class Mover(SchemeComponent):
    def __init__(self, __name: str, **kwargs):
        super().__init__(__name, **kwargs)
        self.gardener = None

    def get_sm_options(self, options: dict):
        gardener = options.get('gardener')

        if gardener is None:
            raise ValueError('Gardener is None!')

        self.gardener = gardener

    def move_forward(self):
        if self.gardener is None:
            raise ValueError('Gardener is None!')
        dx, dy = 0, 0
        if self.gardener.orientation == self.gardener.NORTH:
            dx, dy = 0, -1
        elif self.gardener.orientation == self.gardener.SOUTH:
            dx, dy = 0, 1
        elif self.gardener.orientation == self.gardener.WEST:
            dx, dy = -1, 0
        elif self.gardener.orientation == self.gardener.EAST:
            dx, dy = 1, 0
        nx, ny = self.gardener.x + dx, self.gardener.y + dy
        # import pprint; pprint.pprint(self.gardener.field); print(nx, ny)
        if 0 <= nx < self.gardener.N and 0 <= ny < self.gardener.M:
            if self.gardener.field[ny][nx] != -1:
                self.gardener.x = nx
                self.gardener.y = ny
            else:
                raise GardenerCrashException('Crash: hit a wall!')
        else:
            raise GardenerCrashException('Crash: out of bounds!')

    def move_backward(self):
        if self.gardener is None:
            raise ValueError('Gardener is None!')
        dx, dy = 0, 0
        if self.gardener.orientation == self.gardener.NORTH:
            dx, dy = 0, 1
        elif self.gardener.orientation == self.gardener.SOUTH:
            dx, dy = 0, -1
        elif self.gardener.orientation == self.gardener.WEST:
            dx, dy = 1, 0
        elif self.gardener.orientation == self.gardener.EAST:
            dx, dy = -1, 0
        nx, ny = self.gardener.x + dx, self.gardener.y + dy
        if 0 <= nx < self.gardener.N and 0 <= ny < self.gardener.M:
            if self.gardener.field[ny][nx] != -1:
                self.gardener.x = nx
                self.gardener.y = ny
            else:
                raise GardenerCrashException('Crash: hit a wall!')
        else:
            raise GardenerCrashException('Crash: out of bounds!')

    def turn_left(self):
        if self.gardener is None:
            raise ValueError('Gardener is None!')
        # Поворот против часовой стрелки
        self.gardener.orientation = {
            self.gardener.NORTH: self.gardener.WEST,
            self.gardener.WEST: self.gardener.SOUTH,
            self.gardener.SOUTH: self.gardener.EAST,
            self.gardener.EAST: self.gardener.NORTH
        }[self.gardener.orientation]

    def turn_right(self):
        if self.gardener is None:
            raise ValueError('Gardener is None!')
        # Поворот по часовой стрелке
        self.gardener.orientation = {
            self.gardener.NORTH: self.gardener.EAST,
            self.gardener.EAST: self.gardener.SOUTH,
            self.gardener.SOUTH: self.gardener.WEST,
            self.gardener.WEST: self.gardener.NORTH
        }[self.gardener.orientation]


class Compass(SchemeComponent):
    def __init__(self, __name: str, **kwargs):
        super().__init__(__name, **kwargs)
        self.gardener = None

    def get_sm_options(self, options: dict):
        gardener = options.get('gardener')

        if gardener is None:
            raise ValueError('Gardener is required for Compass work!')

        self.gardener = gardener

    @property
    def x(self):
        if self.gardener is None:
            raise ValueError('Gardener is required for Compass work!')
        return self.gardener.x

    @property
    def y(self):
        if self.gardener is None:
            raise ValueError('Gardener is required for Compass work!')
        return self.gardener.y

    @property
    def south(self):
        if self.gardener is None:
            raise ValueError('Gardener is required for Compass work!')
        return self.gardener.SOUTH

    @property
    def north(self):
        if self.gardener is None:
            raise ValueError('Gardener is required for Compass work!')
        return self.gardener.NORTH

    @property
    def west(self):
        if self.gardener is None:
            raise ValueError('Gardener is required for Compass work!')
        return self.gardener.WEST

    @property
    def east(self):
        if self.gardener is None:
            raise ValueError('Gardener is required for Compass work!')
        return self.gardener.EAST

    @property
    def orientation(self):
        if self.gardener is None:
            raise ValueError('Gardener is required for Compass work!')
        return self.gardener.orientation


# ============================================================================
# SIMPLE_PARSER.PY
# ============================================================================

"""Simple CyberiadaML parser using only standard libraries."""


class CGMLParserException(Exception):
    """Logical errors during parsing CGML scheme."""
    pass


def create_empty_elements() -> CGMLElements:
    """Create CGMLElements with empty fields."""
    return CGMLElements(
        state_machines={},
        format='',
        keys=defaultdict(list)
    )


def create_empty_state_machine() -> CGMLStateMachine:
    """Create CGMLStateMachine with empty fields."""
    return CGMLStateMachine(
        standard_version='',
        platform='',
        meta=CGMLMeta(id='', values={}),
        states={},
        transitions={},
        finals={},
        choices={},
        terminates={},
        initial_states={},
        components={},
        notes={},
        shallow_history={},
        unknown_vertexes={}
    )


def _is_empty_meta(meta: CGMLMeta) -> bool:
    return meta.values == {} and meta.id == ''


def _parse_data_node(data_dict: dict) -> CGMLDataNode:
    """Parse dictionary into CGMLDataNode."""
    key = data_dict.get('@key', '')
    content = data_dict.get('#text')

    rect = None
    if 'rect' in data_dict:
        rect_data = data_dict['rect']
        rect = CGMLRectNode(
            x=rect_data.get('@x', 0.0),
            y=rect_data.get('@y', 0.0),
            width=rect_data.get('@width', 0.0),
            height=rect_data.get('@height', 0.0)
        )

    point = None
    if 'point' in data_dict:
        point_data = data_dict['point']
        if isinstance(point_data, list):
            point = [CGMLPointNode(
                x=p.get('@x', 0.0), y=p.get('@y', 0.0)) for p in point_data]
        else:
            point = CGMLPointNode(x=point_data.get(
                '@x', 0.0), y=point_data.get('@y', 0.0))

    return CGMLDataNode(key=key, content=content, rect=rect, point=point)


def _parse_key_node(key_dict: dict) -> CGMLKeyNode:
    """Parse dictionary into CGMLKeyNode."""
    return CGMLKeyNode(
        id=key_dict.get('@id', ''),
        for_=key_dict.get('@for', ''),
        attr_name=key_dict.get('@attr.name'),
        attr_type=key_dict.get('@attr.type')
    )


def _parse_edge(edge_dict: dict) -> CGMLEdge:
    """Parse dictionary into CGMLEdge."""
    data = None
    if 'data' in edge_dict:
        data_list = edge_dict['data']
        if isinstance(data_list, list):
            data = [_parse_data_node(d) for d in data_list]
        else:
            data = _parse_data_node(data_list)

    return CGMLEdge(
        id=edge_dict.get('@id', ''),
        source=edge_dict.get('@source', ''),
        target=edge_dict.get('@target', ''),
        data=data
    )


def _parse_node(node_dict: dict) -> CGMLNode:
    """Parse dictionary into CGMLNode."""
    data = None
    if 'data' in node_dict:
        data_list = node_dict['data']
        if isinstance(data_list, list):
            data = [_parse_data_node(d) for d in data_list]
        else:
            data = _parse_data_node(data_list)

    graph = None
    if 'graph' in node_dict:
        graph_data = node_dict['graph']
        if isinstance(graph_data, list):
            graph = [_parse_graph(g) for g in graph_data]
        else:
            graph = _parse_graph(graph_data)

    return CGMLNode(
        id=node_dict.get('@id', ''),
        graph=graph,
        data=data
    )


def _parse_graph(graph_dict: dict) -> CGMLGraph:
    """Parse dictionary into CGMLGraph."""
    data = []
    if 'data' in graph_dict:
        data_list = graph_dict['data']
        if isinstance(data_list, list):
            data = [_parse_data_node(d) for d in data_list]
        else:
            data = _parse_data_node(data_list)

    node = None
    if 'node' in graph_dict:
        node_data = graph_dict['node']
        if isinstance(node_data, list):
            node = [_parse_node(n) for n in node_data]
        else:
            node = _parse_node(node_data)

    edge = None
    if 'edge' in graph_dict:
        edge_data = graph_dict['edge']
        if isinstance(edge_data, list):
            edge = [_parse_edge(e) for e in edge_data]
        else:
            edge = _parse_edge(edge_data)

    return CGMLGraph(
        id=graph_dict.get('@id', ''),
        data=data,
        edgedefault=graph_dict.get('@edgedefault'),
        node=node,
        edge=edge
    )


def _parse_graphml(graphml_dict: dict) -> CGMLGraphml:
    """Parse dictionary into CGMLGraphml."""
    data = []
    if 'data' in graphml_dict:
        data_list = graphml_dict['data']
        if isinstance(data_list, list):
            data = [_parse_data_node(d) for d in data_list]
        else:
            data = _parse_data_node(data_list)

    key = None
    if 'key' in graphml_dict:
        key_data = graphml_dict['key']
        if isinstance(key_data, list):
            key = [_parse_key_node(k) for k in key_data]
        else:
            key = _parse_key_node(key_data)

    graph = None
    if 'graph' in graphml_dict:
        graph_data = graphml_dict['graph']
        if isinstance(graph_data, list):
            graph = [_parse_graph(g) for g in graph_data]
        else:
            graph = _parse_graph(graph_data)

    return CGMLGraphml(
        data=data,
        xmlns=graphml_dict.get('@xmlns', ''),
        key=key,
        graph=graph
    )


class CGMLParser:
    """Class that contains functions for parsing CyberiadaML."""

    def __init__(self) -> None:
        self.elements: CGMLElements = create_empty_elements()

    def parse_cgml(self, graphml: str) -> CGMLElements:
        """
        Parse CyberiadaGraphml scheme.

        Args:
            graphml (str): CyberiadaML scheme.

        Returns:
            CGMLElements: notes, states, transitions, initial state and components
        """
        self.elements = create_empty_elements()
        parsed_dict = parse(graphml)

        # Create CGML object manually
        graphml_data = parsed_dict['graphml']
        cgml = CGML(graphml=_parse_graphml(graphml_data))

        graphs: List[CGMLGraph] = to_list(cgml.graphml.graph)
        format_str: str = self._get_format(cgml)

        for graph in graphs:
            keys: AvailableKeys = self._get_available_keys(cgml)
            platform = ''
            standard_version = ''
            meta: CGMLMeta = CGMLMeta(id='', values={})
            states: Dict[str, CGMLState] = {}
            transitions: Dict[str, CGMLTransition] = {}
            notes: Dict[str, CGMLNote] = {}
            terminates: Dict[str, CGMLTerminate] = {}
            finals: Dict[str, CGMLFinal] = {}
            choices: Dict[str, CGMLChoice] = {}
            initials: Dict[str, CGMLInitialState] = {}
            unknown_vertexes: Dict[str, CGMLBaseVertex] = {}
            components: Dict[str, CGMLComponent] = {}
            shallow_history: Dict[str, CGMLShallowHistory] = {}

            vertex_dicts = {
                'initial': (initials, CGMLInitialState),
                'choice': (choices, CGMLChoice),
                'final': (finals, CGMLFinal),
                'terminate': (terminates, CGMLTerminate),
                'shallowHistory': (shallow_history, CGMLShallowHistory)
            }

            states = self._parse_graph_nodes(graph)
            transitions = self._parse_graph_edges(graph)

            for state_id in list(states.keys()):
                state = self._process_state_data(states[state_id])
                if isinstance(state, CGMLNote):
                    note = state
                    del states[state_id]
                    if note.type == 'informal':
                        notes[state_id] = state
                        continue
                    if note.name == 'CGML_META':
                        if not _is_empty_meta(meta):
                            raise CGMLParserException('Double meta nodes!')
                        meta.id = state_id
                        meta.values = self._parse_meta(note.text)
                        try:
                            platform = meta.values['platform']
                            standard_version = meta.values['standardVersion']
                        except KeyError:
                            raise CGMLParserException(
                                'No platform or standardVersion.')
                    elif note.name == 'CGML_COMPONENT':
                        component_parameters: Dict[str, str] = self._parse_meta(
                            note.text)
                        try:
                            component_id = component_parameters['id'].strip()
                            component_type = component_parameters['type'].strip(
                            )
                            del component_parameters['id']
                            del component_parameters['type']
                        except KeyError:
                            raise CGMLParserException(
                                "Component doesn't have type or id.")
                        components[state_id] = CGMLComponent(
                            id=component_id,
                            type=component_type,
                            parameters=component_parameters
                        )
                elif isinstance(state, CGMLState):
                    states[state_id] = state
                elif isinstance(state, CGMLBaseVertex):
                    vertex = state
                    del states[state_id]
                    if is_vertex_type(vertex.type):
                        vertex_dict, vertex_type = vertex_dicts[vertex.type]
                        vertex_dict[state_id] = vertex_type(
                            type=vertex.type,
                            data=vertex.data,
                            position=vertex.position,
                            parent=vertex.parent
                        )
                    else:
                        unknown_vertexes[state_id] = CGMLBaseVertex(
                            type=vertex.type,
                            data=vertex.data,
                            position=vertex.position,
                            parent=vertex.parent
                        )
                else:
                    raise CGMLParserException(
                        'Internal error: Unknown type of node')

            component_ids: List[str] = []
            for transition in list(transitions.values()):
                processed_transition: CGMLTransition = self._process_edge_data(
                    transition)
                if transition.source == meta.id:
                    component_ids.append(transition.id)
                else:
                    transitions[transition.id] = processed_transition

            for component_id in component_ids:
                del transitions[component_id]

            self.elements.state_machines[graph.id] = CGMLStateMachine(
                states=states,
                transitions=transitions,
                components=components,
                initial_states=initials,
                finals=finals,
                unknown_vertexes=unknown_vertexes,
                terminates=terminates,
                notes=notes,
                choices=choices,
                name=self._get_state_machine_name(graph),
                meta=meta,
                shallow_history=shallow_history,
                platform=platform,
                standard_version=standard_version,
            )

        self.elements.keys = keys
        self.elements.format = format_str
        return self.elements

    def _get_state_machine_name(self, graph: CGMLGraph) -> Optional[str]:
        graph_datas = to_list(graph.data)
        name: Optional[str] = None
        is_state_machine = False
        for graph_data in graph_datas:
            if graph_data.key == 'dName':
                name = graph_data.content
            if graph_data.key == 'dStateMachine':
                is_state_machine = True
        if not is_state_machine:
            raise CGMLParserException(
                "First level graph doesn't contain <data> with dStateMachine key!")
        return name

    def _parse_meta(self, meta: str) -> Dict[str, str]:
        splited_parameters: List[str] = meta.split('\n\n')
        parameters: Dict[str, str] = {}
        for parameter in splited_parameters:
            if '/' in parameter:
                parameter_name, parameter_value = parameter.split('/', 1)
                parameters[parameter_name.strip()] = parameter_value.strip()
        return parameters

    def _get_data_content(self, data_node: CGMLDataNode) -> str:
        return data_node.content if data_node.content is not None else ''

    def _process_edge_data(self, transition: CGMLTransition) -> CGMLTransition:
        new_transition = CGMLTransition(
            position=[],
            id=transition.id,
            source=transition.source,
            target=transition.target,
            actions=transition.actions,
            unknown_datanodes=[]
        )
        for data_node in transition.unknown_datanodes:
            if data_node.key == 'dData':
                new_transition.actions = self._get_data_content(data_node)
            elif data_node.key == 'dGeometry':
                if data_node.point is None:
                    raise CGMLParserException(
                        'Edge with key dGeometry doesnt have <point> node.')
                points: List[CGMLPointNode] = to_list(data_node.point)
                for point in points:
                    new_transition.position.append(Point(x=point.x, y=point.y))
            elif data_node.key == 'dColor':
                new_transition.color = self._get_data_content(data_node)
            elif data_node.key == 'dLabelGeometry':
                if data_node.point is None:
                    raise CGMLParserException(
                        'Edge with key dGeometry doesnt have <point> node.')
                if isinstance(data_node.point, list):
                    raise CGMLParserException(
                        'dLabelGeometry with several points!')
                point = data_node.point
                new_transition.label_position = Point(x=point.x, y=point.y)
            else:
                new_transition.unknown_datanodes.append(data_node)
        return new_transition

    def _get_note_type(self, value: str) -> str:
        if is_note_type(value):
            return value
        raise CGMLParserException(
            f'Unknown type of note! Expect formal or informal.')

    def _process_state_data(self, state: CGMLState) -> Union[CGMLState, CGMLNote, CGMLBaseVertex]:
        """Return CGMLState, CGMLNote, or CGMLBaseVertex."""
        new_state = CGMLState(
            name=state.name,
            actions=state.actions,
            unknown_datanodes=[],
            bounds=state.bounds,
            parent=state.parent
        )
        note_type: Optional[str] = None
        vertex_type: Optional[str] = None
        is_note = False
        is_vertex = False

        for data_node in state.unknown_datanodes:
            if data_node.key == 'dName':
                new_state.name = self._get_data_content(data_node)
            elif data_node.key == 'dGeometry':
                if data_node.rect is None and data_node.point is None:
                    raise CGMLParserException(
                        'Node with key dGeometry doesnt have rect or point child')
                if data_node.point is not None:
                    if isinstance(data_node.point, list):
                        raise CGMLParserException(
                            "State doesn't support several points.")
                    new_state.bounds = Point(
                        x=data_node.point.x, y=data_node.point.y)
                    continue
                if data_node.rect is not None:
                    new_state.bounds = Rectangle(
                        x=data_node.rect.x,
                        y=data_node.rect.y,
                        width=data_node.rect.width,
                        height=data_node.rect.height
                    )
            elif data_node.key == 'dVertex':
                is_vertex = True
                vertex_type = self._get_data_content(data_node)
            elif data_node.key == 'dData':
                new_state.actions = self._get_data_content(data_node)
            elif data_node.key == 'dNote':
                is_note = True
                if data_node.content is None:
                    note_type = 'informal'
                else:
                    note_type = self._get_note_type(
                        self._get_data_content(data_node))
            elif data_node.key == 'dColor':
                new_state.color = self._get_data_content(data_node)
            else:
                new_state.unknown_datanodes.append(data_node)

        if is_note and note_type is not None:
            bounds: Optional[Union[Rectangle, Point]] = new_state.bounds
            x = 0.0
            y = 0.0
            if bounds is None:
                if note_type == 'informal':
                    raise CGMLParserException('No position for note!')
            else:
                x = bounds.x
                y = bounds.y
            return CGMLNote(
                parent=new_state.parent,
                name=new_state.name,
                position=Point(x=x, y=y),
                type=note_type,
                text=new_state.actions,
                unknown_datanodes=new_state.unknown_datanodes
            )

        if is_vertex and vertex_type is not None:
            return CGMLBaseVertex(
                type=vertex_type,
                position=new_state.bounds,
                parent=new_state.parent
            )

        return new_state

    def _parse_graph_edges(self, root: CGMLGraph) -> Dict[str, CGMLTransition]:
        def _parse_edge(edge: CGMLEdge, cgml_transitions: Dict[str, CGMLTransition]) -> None:
            cgml_transitions[edge.id] = CGMLTransition(
                id=edge.id,
                source=edge.source,
                target=edge.target,
                actions='',
                unknown_datanodes=to_list(edge.data),
            )

        cgml_transitions: Dict[str, CGMLTransition] = {}
        if root.edge is not None:
            if isinstance(root.edge, Iterable) and not isinstance(root.edge, str):
                for edge in root.edge:
                    _parse_edge(edge, cgml_transitions)
            else:
                _parse_edge(root.edge, cgml_transitions)
        return cgml_transitions

    def _parse_graph_nodes(self, root: CGMLGraph, parent: Optional[str] = None) -> Dict[str, CGMLState]:
        def parse_node(node: CGMLNode) -> Dict[str, CGMLState]:
            cgml_states: Dict[str, CGMLState] = {}
            cgml_states[node.id] = CGMLState(
                name='',
                actions='',
                unknown_datanodes=to_list(node.data),
            )
            if parent is not None:
                cgml_states[node.id].parent = parent
            graphs: List[CGMLGraph] = to_list(node.graph)
            for graph in graphs:
                cgml_states = {**cgml_states, **self._parse_graph_nodes(
                    graph, node.id)}
            return cgml_states

        cgml_states: Dict[str, CGMLState] = {}
        if root.node is not None:
            if isinstance(root.node, Iterable) and not isinstance(root.node, str):
                for node in root.node:
                    cgml_states = {**cgml_states, **parse_node(node)}
            else:
                cgml_states = {**cgml_states, **parse_node(root.node)}
        return cgml_states

    def _get_available_keys(self, cgml: CGML) -> AvailableKeys:
        key_node_dict: AvailableKeys = defaultdict(list)
        if cgml.graphml.key is not None:
            if isinstance(cgml.graphml.key, Iterable) and not isinstance(cgml.graphml.key, str):
                for key_node in cgml.graphml.key:
                    key_node_dict[key_node.for_].append(key_node)
            else:
                key_node_dict[cgml.graphml.key.for_].append(cgml.graphml.key)
        return key_node_dict

    def _get_format(self, cgml: CGML) -> str:
        if isinstance(cgml.graphml.data, Iterable) and not isinstance(cgml.graphml.data, str):
            for data_node in cgml.graphml.data:
                if data_node.key == 'gFormat':
                    if data_node.content is not None:
                        return data_node.content
                    raise CGMLParserException(
                        'Data node with key "gFormat" is empty')
        else:
            if cgml.graphml.data.key == 'gFormat':
                if cgml.graphml.data.content is not None:
                    return cgml.graphml.data.content
                raise CGMLParserException(
                    'Data node with key "gFormat" is empty')
        raise CGMLParserException('Data node with key "gFormat" is missing')


# ============================================================================
# CGML_SIGNAL.PY
# ============================================================================


@dataclass
class Component:
    id: str
    type: str
    obj: object


@dataclass
class Action:
    component: str
    action: str
    args: list


@dataclass
class Signal:
    condition: str
    action: str
    status: Callable[..., int]

    def __str__(self):
        cond = f"[{self.condition}]" if self.condition else ""
        # статус не выводим, он всегда функция
        return f"Signal{cond}/ {self.action}"


@dataclass
class ChoiceSignal(Signal):
    target: str


class StateMachine:
    def __init__(
        self,
        sm: CGMLStateMachine,
        sm_parameters: dict
    ):
        self.components = init_components(sm.components, sm_parameters)
        self.inital_states = init_initial_states(
            self, sm.initial_states, sm.transitions)
        self.final_states = init_final_states(self, sm.finals)
        self.choice_states = init_choice_states(
            self, sm.choices, sm.transitions)
        self.qhsm = QHsm()
        self.states = init_states(
            self.qhsm,
            self,
            self.inital_states,
            self.final_states,
            self.choice_states,
            sm.states,
            sm.transitions
        )
        post_init_choice_states(
            self, self.choice_states, self.states, self.inital_states, self.final_states)
        self.initial = find_highest_level_initial_state(self.inital_states)
        if self.initial is None:
            raise ValueError("No initial state found in the state machine.")
        self.qhsm.post_init(self.initial.execute_signal)

    def intepreter_condition(self, condition: str) -> bool:
        """
        Интерпретирует простые условные выражения вида:
        timer.difference > 0
        12 > 0
        3 == timer.difference
        timer.difference == timer.difference
        """
        if not condition or condition.strip() == "":
            return True
        # Поддержка: <, >, ==, !=, <=, >=
        import operator
        ops = {
            '>': operator.gt,
            '<': operator.lt,
            '==': operator.eq,
            '!=': operator.ne,
            '>=': operator.ge,
            '<=': operator.le,
        }
        # Поиск оператора
        for op_str in sorted(ops.keys(), key=len, reverse=True):
            if op_str in condition:
                left, right = condition.split(op_str, 1)
                left = left.strip()
                right = right.strip()
                op_func = ops[op_str]
                # Попытка привести к числу

                def resolve(val):
                    def safe_eval(val: str):
                        try:
                            tree = ast.parse(val)
                        except SyntaxError:
                            return val
                        for node in tree.body:
                            if isinstance(node, ast.Expr):
                                if isinstance(node.value, ast.Constant):
                                    return ast.literal_eval(node.value)
                        return val
                    try:
                        return float(val) if '.' in val else int(val)
                    except ValueError:
                        # Попытка получить значение из компонента
                        if '.' in val:
                            comp_name, attr = val.split('.', 1)
                            comp = self.components.get(comp_name)
                            if comp and hasattr(comp.obj, attr):
                                return getattr(comp.obj, attr)
                        return safe_eval(val)
                left_val = resolve(left)
                right_val = resolve(right)
                return op_func(left_val, right_val)
        # Если не найден оператор, просто сравниваем на True
        return bool(condition)

    def __parse_args(self, args_str: str) -> list:
        """
        Парсит строку аргументов, учитывая\
            сложные структуры в фигурных скобках.

        Примеры:
        "1, 2, 3" -> [1, 2, 3]
        "{1, 2, 3}, 4" -> [[1, 2, 3], 4]
        "text, {1, 2}, 3" -> ["text", [1, 2], 3]

        Args:
            args_str: Строка с аргументами

        Returns:
            Список распарсенных аргументов
        """
        def parse_set(set_str: str) -> list:
            """Парсит содержимое фигурных скобок в список."""
            # Убираем фигурные скобки и разбиваем по запятым
            content = set_str[1:-1].strip()
            if not content:
                return []
            return [parse_value(x.strip()) for x in content.split(',')]

        def parse_value(val: str) -> Any:
            """Парсит отдельное значение, пытаясь преобразовать его в число."""
            val = val.strip()
            # Если это множество в фигурных скобках
            if val.startswith('{') and val.endswith('}'):
                return parse_set(val)
            # Пытаемся преобразовать в число
            try:
                if '.' in val:
                    return float(val)
                return int(val)
            except ValueError:
                return val

        def split_args(args_str: str) -> list:
            """Разбивает строку на аргументы с учетом вложенных структур."""
            result = []
            current = []
            nesting_level = 0

            for char in args_str:
                if char == '{':
                    nesting_level += 1
                    current.append(char)
                elif char == '}':
                    nesting_level -= 1
                    current.append(char)
                elif char == ',' and nesting_level == 0:
                    result.append(''.join(current).strip())
                    current = []
                else:
                    current.append(char)

            if current:
                result.append(''.join(current).strip())

            return result

        if not args_str:
            return []

        # Разбиваем строку на аргументы
        args = split_args(args_str)
        # Парсим каждый аргумент
        return [parse_value(arg) for arg in args]

    def __parse_action(self, actions: str) -> list:
        """
        Парсит строку или строки вида
        'компонент.действие(арг1, ...)'\n'компонент2.действие2(...)'\n...
        в список объектов Action.
        """
        result = []
        for action in actions.strip().splitlines():
            action = action.strip()
            if not action:
                continue
            pattern = r'^(?P<component>\w+)\.(?P<method>\w+)\((?P<args>.*)\)'
            match = re.match(pattern, action)
            if not match:
                raise ValueError(f"Invalid action format: {action}")
            component = match.group('component')
            method = match.group('method')
            args_str = match.group('args').strip()
            args = self.__parse_args(args_str) if args_str else []
            result.append(Action(
                component=component, action=method, args=args))
        return result

    def intepreter_action(self, action: str):
        def resolve(val):
            if isinstance(val, list):
                return val
            elif isinstance(val, int):
                return val

            try:
                return float(val) if '.' in val else int(val)
            except Exception as e:
                # Попытка получить значение из компонента
                if '.' in val:
                    comp_name, attr = val.split('.', 1)
                    comp = self.components.get(comp_name)
                    if comp and hasattr(comp.obj, attr):
                        return getattr(comp.obj, attr)
                return val
        # если не компонентная структура кода, то просто делаем eval здесь
        actions_obj = self.__parse_action(action)
        for action_obj in actions_obj:
            component = self.components.get(action_obj.component)
            if component:
                method = getattr(component.obj, action_obj.action, None)
                args = []
                for arg in action_obj.args:
                    args.append(resolve(arg))
                if callable(method):
                    method(*args)
                else:
                    raise ValueError(
                        f"Action {action_obj.action} not \
                            callable on {component.type}")


class Element(ABC):
    def execute_signal(self, qhsm: QHsm, signal_name: str) -> int:
        raise NotImplementedError("Subclasses should implement this method.")


class InitialState(Element):
    def __init__(
        self,
        sm: StateMachine,
        target: str,
        parent=None
    ):
        self.sm = sm
        self.target = target
        self.parent = parent

    def execute_signal(self, qhsm: QHsm, signal_name: str) -> int:
        if signal_name == 'entry':
            EventLoop.add_event('noconditionTransition')
            return Q_HANDLED()
        if signal_name == 'noconditionTransition':
            return Q_TRAN(qhsm, self.sm.states[self.target].execute_signal)

        if self.parent:
            return Q_SUPER(qhsm, self.sm.states[self.parent].execute_signal)
        else:
            return Q_SUPER(qhsm, QHsm_top)


class ChoiceState(Element):
    def __init__(self, sm: StateMachine, parent=None):
        self.sm = sm
        self.parent = parent
        self.conditions: list[ChoiceSignal] = []

    def execute_signal(self, qhsm: QHsm, signal_name: str) -> int:
        if signal_name == 'entry':
            EventLoop.add_event('noconditionTransition')
            return Q_HANDLED()
        else_signal = None
        if signal_name == 'noconditionTransition':
            for signal in self.conditions:
                signal_condition = signal.condition
                signal_action = signal.action
                if (signal_condition == "else"):
                    else_signal = signal
                    continue
                if self.sm.intepreter_condition(signal_condition):
                    self.sm.intepreter_action(signal_action)
                    status = signal.status()
                    return status
            if else_signal is not None:
                self.sm.intepreter_action(else_signal.action)
                status = else_signal.status()
                return status
        else:
            if self.parent:
                return Q_SUPER(qhsm, self.sm.states[self.parent].execute_signal)
            else:
                return Q_SUPER(qhsm, QHsm_top)


class FinalState(Element):
    def __init__(self, sm: StateMachine, parent=None):
        self.sm = sm
        self.parent = parent

    def execute_signal(self, qhsm: QHsm, signal_name: str) -> int:
        if signal_name == 'entry':
            EventLoop.add_event('break')
            return Q_HANDLED()
        # Final state does not handle any other signals
        return Q_SUPER(qhsm, QHsm_top)


class State(Element):
    def __init__(
        self,
        id: str,
        sm: StateMachine,
        signals: dict,
        parent=None
    ):
        self.id = id
        self.signals = signals
        self.parent = parent
        self.sm = sm

    def __str__(self):
        signals_str = []
        for event, siglist in self.signals.items():
            for sig in siglist:
                signals_str.append(f"  {event}: {sig}")
        parent_str = f", parent={self.parent}" if self.parent else ""
        return f"State(signals=[\n" + "\n".join(signals_str) + f"\n]{parent_str})"

    def has_initial_state_child(self) -> Optional[InitialState]:
        for id, initial in self.sm.inital_states.items():
            if initial.parent == self.id:
                return self.sm.inital_states[id]

        return None

    def execute_signal(self, qhsm: QHsm, signal_name: str) -> int:
        signals = self.signals.get(signal_name)
        if signal_name == 'entry' and self.has_initial_state_child() is not None:
            EventLoop.add_event('noconditionTransition')
        if signal_name == 'noconditionTransition':
            child = self.has_initial_state_child()
            if child is None:
                return Q_HANDLED()
            return Q_TRAN(qhsm, child.execute_signal)
        if signals:
            else_signal = None
            for signal in signals:
                if signal.condition == "else":
                    else_signal = signal
                    continue
                if self.sm.intepreter_condition(signal.condition):
                    self.sm.intepreter_action(signal.action)
                    status = signal.status()
                    return status
            if else_signal is not None:
                self.sm.intepreter_action(else_signal.action)
                status = else_signal.status()
                return status
        if self.parent:
            return Q_SUPER(qhsm, self.sm.states[self.parent].execute_signal)
        else:
            return Q_SUPER(qhsm, QHsm_top)


def parse_actions_block(actions: str) -> dict:
    """Парсит блок событий и действий из строки actions. Поддерживает несколько условий для одного события."""
    signals: dict = {}
    if not actions:
        return signals
    blocks = actions.strip().split('\n\n')
    for block in blocks:
        lines = [line for line in block.strip().splitlines() if line.strip()]
        if not lines:
            continue
        header = lines[0]
        body = lines[1:]
        # событие[условие]/
        if '/' in header:
            event_part, _ = header.split('/', 1)
            if '[' in event_part and ']' in event_part:
                event_name = event_part.split('[')[0].strip()
                condition = event_part.split('[')[1].split(']')[0].strip()
            else:
                event_name = event_part.strip()
                condition = ""
        else:
            event_name = header.strip()
            condition = ""
        action = '\n'.join(body)
        signal = Signal(
            condition=condition, action=action, status=Q_HANDLED)
        if event_name not in signals:
            signals[event_name] = []
        signals[event_name].append(signal)
    return signals


def init_choice_states(
    sm: StateMachine,
    cgml_choice_states: dict,
    cgml_transitions: dict
) -> dict:
    """Initialize choice states from CGMLChoice data. Для каждого состояния выбора ищет все исходящие переходы и парсит их в список Signal."""
    initialized_states: dict = {}
    for state_id, cgml_choice in cgml_choice_states.items():
        choice_state = ChoiceState(sm, parent=cgml_choice.parent)
        conditions: list = []
        for trans in cgml_transitions.values():
            if trans.source != state_id:
                continue
            trigger = trans.actions
            condition = ""
            action = ""
            if '/' in trigger:
                cond_part, action_part = trigger.split('/', 1)
                if '[' in cond_part and ']' in cond_part:
                    condition = cond_part.split('[')[1].split(']')[0].strip()
                else:
                    condition = ""
                action = action_part.strip()
            else:
                condition = ""
                action = ""
            signal = ChoiceSignal(
                condition=condition,
                action=action,
                status=Q_HANDLED,
                target=trans.target
            )
            conditions.append(signal)
        choice_state.conditions = conditions
        initialized_states[state_id] = choice_state
    return initialized_states


def post_init_choice_states(
    sm: StateMachine,
    choice_states: dict,
    states: dict,
    initials: dict,
    finals: dict
):
    """
    Для каждого ChoiceState обновляет status у Signal в conditions на partial(Q_TRAN, qhsm, target_func),
    где target_func — execute_signal целевого состояния (State, InitialState, FinalState, ChoiceState).
    """
    qhsm = sm.qhsm
    for choice_state in choice_states.values():
        for signal in choice_state.conditions:
            # Определяем целевое состояние по target
            target_func = None
            if signal.target in states:
                target_func = states[signal.target].execute_signal
            elif signal.target in initials:
                target_func = initials[signal.target].execute_signal
            elif signal.target in finals:
                target_func = finals[signal.target].execute_signal
            elif signal.target in choice_states:
                target_func = choice_states[signal.target].execute_signal
            else:
                raise ValueError(
                    f"Target state '{signal.target}' not found for choice transition.")
            signal.status = partial(Q_TRAN, qhsm, target_func)


def init_states(
        qhsm: QHsm,
        sm: 'StateMachine',
        initials: dict,
        finals: dict,
        choices: dict,
        cgml_states: dict,
        cgml_transition: dict,
) -> dict:
    """Initialize states from CGMLState data."""
    initialized_states: dict = {}
    for state_id, cgml_state in cgml_states.items():
        signals = parse_actions_block(cgml_state.actions)
        initialized_states[state_id] = State(
            state_id, sm, signals, cgml_state.parent)
    # transitions
    for trans in cgml_transition.values():
        trigger = trans.actions
        condition = ""
        action = ""
        if '/' in trigger:
            event_part, action_part = trigger.split('/', 1)
            if '[' in event_part and ']' in event_part:
                event_name = event_part.split('[')[0].strip()
                condition = event_part.split('[')[1].split(']')[0].strip()
            else:
                event_name = event_part.strip()
                condition = ""
            action = action_part.strip()
        else:
            event_name = trigger.strip()
            condition = ""
            action = ""
        if trans.source in initialized_states:
            target = initialized_states.get(trans.target) or initials.get(
                trans.target) or finals.get(trans.target) or choices.get(trans.target)
            if target is None:
                continue
            target_func = target.execute_signal
            status_func = partial(Q_TRAN, qhsm, target_func)
            signal = Signal(
                condition=condition,
                action=action,
                status=status_func
            )
            if event_name not in initialized_states[trans.source].signals:
                initialized_states[trans.source].signals[event_name] = []
            initialized_states[trans.source].signals[event_name].append(signal)
    return initialized_states


def init_final_states(sm: StateMachine, cgml_final_states: dict):
    """Initialize final states from CGMLFinalState data."""
    initialized_states: dict = {}
    for state_id, cgml_final in cgml_final_states.items():
        initialized_states[state_id] = FinalState(
            sm,  # StateMachine not needed here, but can be set later
            parent=cgml_final.parent
        )
    return initialized_states


def init_components(
    cgml_components: dict,
    sm_parameters: dict
) -> dict:
    """Initialize components from CGMLComponent data."""
    initialized_components = {}
    for cgml_comp in cgml_components.values():
        # Get component class from globals
        component_class = globals().get(cgml_comp.type)
        if component_class:
            # Передаем параметры компонента как kwargs
            parameters = cgml_comp.parameters if hasattr(
                cgml_comp, 'parameters') else {}
            # Также передаем все глобальные параметры
            parameters.update(sm_parameters)
            # Создаем экземпляр с параметрами
            component_instance = component_class(cgml_comp.id, **parameters)
            component_instance.get_sm_options(sm_parameters)
            initialized_components[cgml_comp.id] = Component(
                id=cgml_comp.id,
                type=cgml_comp.type,
                obj=component_instance
            )
        else:
            raise ValueError(f"Component type {cgml_comp.type} not found.")
    return initialized_components


def init_initial_states(
    sm: 'StateMachine',
    cgml_initial_states: dict,
    cgml_transitions: dict
) -> dict:
    """Initialize initial states from CGMLInitialState data."""
    initial_states = {}
    for state_id, initial_state in cgml_initial_states.items():
        trans = find_transitions_for_state(state_id, cgml_transitions)
        if len(trans) != 1:
            continue
        initial_states[state_id] = InitialState(
            sm,
            target=trans[0].target,
            parent=initial_state.parent
        )
    return initial_states


def find_transitions_for_state(
    state_id: str,
    cgml_transitions: dict
) -> list:
    """Возвращает список переходов, у которых source == state_id."""
    return [
        trans for trans in cgml_transitions.values()
        if trans.source == state_id
    ]


def find_highest_level_initial_state(
    initial_states: dict
):
    """Находит начальное состояние с самым высоким уровнем."""
    for initial_state in initial_states.values():
        if initial_state.parent is None:
            return initial_state

    return None


@dataclass
class StateMachineResult:
    timeout: bool
    signals: list
    called_signals: list
    components: dict


def run_state_machine(
        sm: StateMachine,
        signals: list,
        timeout_sec: float = 100000.0,
        isInfinite: bool = False
) -> StateMachineResult:
    """
    Запускает машину состояний на основе CGML XML и списка сигналов.
    Возвращает StateMachineResult: был ли выход по таймауту, список сигналов, компоненты.
    """
    default_signals = ['noconditionTransition', 'entry', 'exit']
    EventLoop.clear()
    qhsm = sm.qhsm
    qhsm.current_(qhsm, 'entry')

    for event in signals:
        EventLoop.add_event(event)

    timeout = False
    start_time = time.time()

    while True:
        # Execute loop_actions for each component
        event = EventLoop.get_event()
        while event in default_signals:
            SIMPLE_DISPATCH(qhsm, event)
            event = EventLoop.get_event()
            continue
        for component in sm.components.values():
            if hasattr(component.obj, 'loop_actions'):
                component.obj.loop_actions()
        event = EventLoop.get_event()
        if event is None:
            if isInfinite:
                time.sleep(0.1)
                continue
            break
        if event == 'break':
            break
        SIMPLE_DISPATCH(qhsm, event)

    return StateMachineResult(
        timeout,
        EventLoop.events,
        EventLoop.called_events,
        sm.components
    )

# ============================================================================
# ORBITA.PY
# ============================================================================

# Подключение библиотек
# В данном случае мы работаем со стандартным вводом и выводом, а тестовые данные у нас в формате JSON


def get_log(user_exception_str=None):
    return '\n'.join([s for s in [sys.stdout.getvalue(), user_exception_str] if s])

# Функция, формирующая в случае ошибки результат с начислением 0 баллов и соответствующим "достижением"


def return_user_error(user_error, user_exception_str=None):
    return {'score': 0, 'message': user_error, 'log': get_log(user_exception_str)}

# ============================================================================
# TEST READER FUNCTIONS
# ============================================================================


def check_reader(result: StateMachineResult, answer_signals: list) -> tuple:
    if result.timeout:
        return ('Машина состояний работает слишком долго!', False)

    if len(answer_signals) != len(result.called_signals):
        return ('Вызвано неверное количество событий!', False)

    for i in range(len(answer_signals)):
        if answer_signals[i] != result.called_signals[i]:
            return (f'Неверное событие {result.called_signals[i]}', False)
    return ('', True)


def check_gardener(result: StateMachineResult, gardener: Gardener, answer_state: list, required_position: Optional[set],) -> tuple:
    if result.timeout:
        return ('Машина состояний работает слишком долго!', False)
    # from pprint import pprint
    # pprint(gardener.field)
    for i in range(len(gardener.field)):
        for j in range(len(gardener.field[0])):
            if gardener.field[i][j] != answer_state[i][j]:
                return ('Неверный ответ', False)
    if required_position:
        x, y = required_position
        if not (gardener.x == x and gardener.y == y):
            return ('Неверная позиция садовника', False)
    return ('', True)


def auto_test_reader(
    cgml_sm: CGMLStateMachine,
    sm_parameters: dict,
    entry_signals: list,
    answer_signals: list,
    ignored_signals: list,
    timeout: int = 5
):
    sm = StateMachine(
        cgml_sm,
        sm_parameters=sm_parameters,
    )
    result = run_state_machine(sm, entry_signals, timeout)
    check_result = check_reader(result, answer_signals)
    return check_result, result


def auto_test_gardener(
    cgml_sm: CGMLStateMachine,
    gardener: Gardener,
    entry_signals: list,
    answer_gardener_state: list,
    ignored_signals: list,
    required_position: Optional[set],
    timeout: int = 5
):
    sm = StateMachine(
        cgml_sm,
        sm_parameters={
            'gardener': gardener
        },
    )
    result = run_state_machine(sm, entry_signals, timeout)
    check_result = check_gardener(
        result, gardener, answer_gardener_state, required_position)
    return check_result, result


def extract_state_machine(code: str):
    tree = ast.parse(code)

    for node in tree.body:
        if isinstance(node, ast.Assign):
            # проверяем, что это именно state_machine
            for target in node.targets:
                if isinstance(target, ast.Name) and target.id == 'state_machine':
                    # пытаемся безопасно достать значение
                    return ast.literal_eval(node.value)

    return None


def parse_test_string(test_str: str) -> tuple[list, list, Union[tuple, None]]:
    """Parse a test string in format 'firstarray;secondarray;condition' into components.

    Args:
        test_str: String in format "[[1,2],[3,4]];[[5,6],[7,8]];(1,2)" or similar

    Returns:
        Tuple of (first array, second array, condition string)
        Arrays are nested lists, condition is string representation of position or None
    """
    try:
        # Split by semicolon
        parts = test_str.split(';')
        if len(parts) != 3:
            raise ValueError(
                "Test string must have exactly 3 parts separated by semicolons")

        # Parse the arrays using ast.literal_eval for safety
        first_array = ast.literal_eval(parts[0])
        second_array = ast.literal_eval(parts[1])

        # Parse condition - can be None or a position tuple
        condition = None if parts[2].lower(
        ) == 'none' else ast.literal_eval(parts[2])

        return first_array, second_array, condition

    except Exception as e:
        raise ValueError(f"Failed to parse test string: {e}")


def create_test_string(first: list, second: list, condition: Optional[tuple]) -> str:
    """Create a test string from arrays and condition.

    Args:
        first: First nested list array
        second: Second nested list array
        condition: Optional position tuple or None

    Returns:
        Formatted string in 'firstarray;secondarray;condition' format
    """
    try:
        # Convert arrays to string representation
        first_str = str(first)
        second_str = str(second)

        # Convert condition to string
        condition_str = 'None' if condition is None else str(condition)

        # Join with semicolons
        return f"{first_str};{second_str};{condition_str}"

    except Exception as e:
        raise ValueError(f"Failed to create test string: {e}")
