from typing import Any, Dict, List


class Transformer:
    def __call__(self, data: Dict[str, Any], frame: Any) -> Dict[str, Any]:
        raise NotImplementedError


class MaskTransformer(Transformer):
    def __init__(self, fields_to_mask: List[str]):
        self.fields_to_mask = fields_to_mask

    def __call__(self, data, frame):
        for field in self.fields_to_mask:
            if field in data:
                data[field] = None
        return data


class ReduceTransformer(Transformer):
    def __init__(self, reducer_fn):
        self.reducer_fn = reducer_fn

    def __call__(self, data, frame):
        return self.reducer_fn(data)


class MergeTransformer(Transformer):
    def __init__(self, other_axis_data):
        self.other_axis_data = other_axis_data

    def __call__(self, data, frame):
        data.update(self.other_axis_data)
        return data


class FocusCheckTransformer(Transformer):
    def __init__(self, focus):
        self.focus = focus

    def __call__(self, data, frame):
        return {
            k: v for k, v in data.items()
            if self.focus.allows(k)
        }


class ClampTransformer(Transformer):
    def __init__(self, field, min_value, max_value):
        self.field = field
        self.min_value = min_value
        self.max_value = max_value

    def __call__(self, data, frame):
        value = data.get(self.field)
        if value is not None:
            data[self.field] = max(
                self.min_value, min(self.max_value, value))
        return data


class MathTransformer(Transformer):
    def __init__(self, target_field, op, operand_fields):
        self.target_field = target_field
        self.op = op
        self.operand_fields = operand_fields

    def __call__(self, data, frame):
        operands = [data[f] for f in self.operand_fields]
        if self.op == 'ADD':
            data[self.target_field] = sum(operands)
        elif self.op == 'MUL':
            result = 1
            for o in operands:
                result *= o
            data[self.target_field] = result
        return data
