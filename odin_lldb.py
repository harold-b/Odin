import lldb
import math
import logging

# See: https://lldb.llvm.org/python_api/lldb.SBType.html#lldb.SBType
#      https://lldb.llvm.org/python_api/lldb.SBValue.html#lldb.SBValue

log = logging.getLogger(__name__)

def is_span_type(t, internal_dict):
    return t.name.startswith("Array<")

def span_summary(value, internal_dict):
    value  = value.GetNonSyntheticValue()
    length = value.GetChildMemberWithName("count").unsigned
    data   = value.GetChildMemberWithName("data")

    pointee   = data.deref
    type_name = pointee.type.GetDisplayTypeName()

    return f"[{length}]{type_name}"


class SpanChildProvider:
    CHUNK_COUNT = 2000

    def __init__(self, val, dict):
        self.val = val
        self.update()

    def update(self):
        val = self.val

        self.len        = val.GetChildMemberWithName("count").unsigned
        self.data_val   = val.GetChildMemberWithName("data")
        assert self.data_val.type.is_pointer

        is_chunked       = self.len > SpanChildProvider.CHUNK_COUNT
        self.chunked_len = 0 if not is_chunked else math.ceil(self.len / SpanChildProvider.CHUNK_COUNT)

        return False

    def num_children(self):
        return self.chunked_len if self.chunked_len > 0 else self.len

    def get_child_at_index(self, index):
        length = self.num_children()
        assert index >= 0 and index < length

        first = self.data_val.deref

        if self.chunked_len > 0:
            chunk_size = SpanChildProvider.CHUNK_COUNT

            array_len = min(chunk_size, self.len - index * chunk_size)
            arr_type  = first.type.GetArrayType(array_len)
            offset    = index * first.size * chunk_size

            range_start = index * chunk_size

            return self.data_val.CreateChildAtOffset(f"[{range_start}..<{range_start+array_len}]", offset, arr_type)

        offset = index * first.size
        return self.data_val.CreateChildAtOffset(f"[{index}]", offset, first.type)


def is_fixed_array_type(t, internal_dict):
    return t.name.startswith("FixedArray<")

def fixed_array_summary(value, internal_dict):
    value     = value.GetNonSyntheticValue()
    data      = value.GetChildMemberWithName("data")
    data_type = data.GetType()
    elem_type = data_type.GetArrayElementType()

    data_total_size = data_type.GetByteSize()
    array_length    = int(data_total_size / elem_type.GetByteSize())

    # Show the first ten values
    preview_length  = int(min(array_length, 10))
    preview_elements = ""

    if preview_length > 0:
        for i in range(preview_length):
            e = data.GetChildAtIndex(i).GetNonSyntheticValue()
            preview_elements += f"{e.value}"

            if i + 1 < preview_length:
                preview_elements += ", "

        if preview_length < array_length:
            preview_elements += ", ..."

    return f"[{array_length}] {elem_type.GetDisplayTypeName()}{{{preview_elements}}}"

class FixedArrayChildProvider:
    CHUNK_COUNT = 2000

    def __init__(self, val, dict):
        self.val = val
        self.update()

    def update(self):
        val = self.val.GetNonSyntheticValue()

        data = val.GetChildMemberWithName("data")

        data_type = data.GetType()
        elem_type = data_type.GetArrayElementType()

        data_total_size = data_type.GetByteSize()
        array_length    = int(data_total_size / elem_type.GetByteSize())
        is_chunked      = array_length > FixedArrayChildProvider.CHUNK_COUNT

        self.data_val    = data
        self.len         = array_length
        self.elem_type   = elem_type
        self.chunked_len = 0 if not is_chunked else math.ceil(array_length / FixedArrayChildProvider.CHUNK_COUNT)

        # log.info(f"LENGTH: {array_length} | CHUNKED: {is_chunked} | CHUNK_COUN: {self.chunked_len}")

        return False

    def num_children(self):
        return self.chunked_len if self.chunked_len > 0 else self.len

    def get_child_at_index(self, index):
        length = self.num_children()
        assert index >= 0 and index < length

        elem_size = self.elem_type.GetByteSize()

        # first = self.data_val.deref

        if self.chunked_len > 0:
            chunk_size = FixedArrayChildProvider.CHUNK_COUNT

            array_len = min(chunk_size, self.len - index * chunk_size)
            arr_type  = self.elem_type.GetArrayType(array_len)
            offset    = index * elem_size * chunk_size

            range_start = index * chunk_size

            return self.data_val.CreateChildAtOffset(f"[{range_start}..<{range_start+array_len}]", offset, arr_type)

        offset = index * elem_size
        return self.data_val.CreateChildAtOffset(f"[{index}]", offset, self.elem_type)


def is_string_type(t, internal_dict):
    return t.name == "String"

def string_summary(value, internal_dict):
    pointer = value.GetChildMemberWithName("text").GetValueAsUnsigned(0)
    length = value.GetChildMemberWithName("len").GetValueAsSigned(0)
    if pointer == 0:
        return False
    if length == 0:
        return '""'
    error = lldb.SBError()
    string_data = value.process.ReadMemory(pointer, length, error)
    return '"{}"'.format(string_data.decode("utf-8"))


def __lldb_init_module(debugger, unused):
    debugger.HandleCommand(
        "type summary add --recognizer-function --python-function pos2.string_summary odin_lldb.is_string_type"
    )
    debugger.HandleCommand(
        "type synth add --recognizer-function --python-class pos2.SpanChildProvider odin_lldb.is_span_type"
    )
    debugger.HandleCommand(
        "type summary add --recognizer-function --python-function pos2.span_summary odin_lldb.is_span_type"
    )
    # debugger.HandleCommand(
    #     "type summary add --recognizer-function --python-function pos2.fixed_array_summary odin_lldb.is_fixed_array_type"
    # )
    # debugger.HandleCommand(
    #     "type synth add --recognizer-function --python-class pos2.FixedArrayChildProvider odin_lldb.is_fixed_array_type"
    # )
    