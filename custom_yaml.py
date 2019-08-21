import codecs
import logging
import yaml
from collections import OrderedDict

# -----------------------------------------------------------------------------
# Reading and saving files
# -----------------------------------------------------------------------------


def represent_odict(dump, tag, mapping, flow_style=None):
    """
    Like BaseRepresenter.represent_mapping, but does not issue the sort().
    """

    value = []
    node = yaml.MappingNode(tag, value, flow_style=flow_style)
    if dump.alias_key is not None:
        dump.represented_objects[dump.alias_key] = node
    best_style = True
    if hasattr(mapping, 'items'):
        mapping = mapping.items()
    for item_key, item_value in mapping:
        n_key = dump.represent_data(item_key)
        n_val = dump.represent_data(item_value)
        if not (isinstance(n_key, yaml.ScalarNode) and not n_key.style):
            best_style = False
        if not (isinstance(n_val, yaml.ScalarNode) and not n_val.style):
            best_style = False
        value.append((n_key, n_val))
    if flow_style is None:
        if dump.default_flow_style is not None:
            node.flow_style = dump.default_flow_style
        else:
            node.flow_style = best_style
    return node


def representer(dumper, value):
    return represent_odict(dumper, u'tag:yaml.org,2002:map', value)


yaml.SafeDumper.add_representer(OrderedDict, representer)


def ordered_load(stream, Loader=yaml.Loader, object_pairs_hook=OrderedDict):
    class OrderedLoader(Loader):
        pass

    def construct_mapping(loader, node):
        loader.flatten_mapping(node)
        return object_pairs_hook(loader.construct_pairs(node))
    OrderedLoader.add_constructor(
        yaml.resolver.BaseResolver.DEFAULT_MAPPING_TAG,
        construct_mapping)
    return yaml.load(stream, OrderedLoader)


def load_yaml(path):
    """
    Load data from YAML file.
    """

    with codecs.open(path, "r", encoding="utf-8") as f:
        try:
            data = ordered_load(f, yaml.SafeLoader)
        except yaml.YAMLError as exc:
            logging.warning(exc)
    return data


def save_yaml(data, path, allow_unicode=True, default_flow_style=False):
    """
    Save data to YAML file.
    """

    # load data
    with open(path, "w", encoding="utf-8") as f:
        try:
            yaml.safe_dump(data, f, allow_unicode=allow_unicode,
                           default_flow_style=default_flow_style)
        except yaml.YAMLError as exc:
            logging.warning(exc)
