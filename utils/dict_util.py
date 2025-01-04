import re


def dict_update(raw, new):
    dict_update_iter(raw, new)
    dict_add(raw, new)


def dict_update_iter(raw, new):
    for key in raw:
        if key not in new.keys():
            continue
        if isinstance(raw[key], dict) and isinstance(new[key], dict):
            dict_update(raw[key], new[key])
        else:
            raw[key] = new[key]


def dict_add(raw, new):
    update_dict = {}
    for key in new:
        if key not in raw.keys():
            update_dict[key] = new[key]
    raw.update(update_dict)


def dict_set(source, special_key, new):
    if isinstance(source, dict):
        if special_key in source.keys():
            source[special_key] = new[special_key]
            return
        for key in source:
            dict_set(source[key], special_key, new)


def get_value_by_refs(refs, source_dict):
    rs = re.findall(r'(\$\{[\w\.]+\})', refs)
    keys = []
    key_value = {}
    for r in rs:
        key_str = r[2:-1]
        keys.append(key_str)
        ks = key_str.split(".")
        _dict = source_dict
        for k in ks:
            v = _dict.get(k)
            key_value[k] = v
    return keys, key_value


if __name__ == '__main__':
    # out_dict = {"content": {'pullbackParams': {}}}
    # key = 'pullbackParams'
    # inner_dict = {'pullbackParams': ["eeee"]}
    # dict_set(out_dict, key, inner_dict)
    # print(inner_dict)
    # print(out_dict)
    d1 = {"a": 1, 'b': {'c': 3}}
    d2 = dict(d1)
    d2['a'] = 2
    d2['b']['c'] = 4
    print(d1)
    print(d2)
