from typing import Dict, List
import os
import lxml.etree as ET
import zipfile
from io import BytesIO


class PackageFile:
    def __init__(self, filename: str, xml: ET.Element):
        self.Filename: str = filename
        self.Xml: ET.Element = xml


def zip_package(package: Dict[str, PackageFile], entry_point: str) -> bytes:
    zip_bytes = BytesIO()
    zip_file = zipfile.ZipFile(zip_bytes, mode="w", compression=zipfile.ZIP_DEFLATED, allowZip64=True)
    zip_file.comment = bytes(entry_point, 'utf-8')
    for key in package.keys():
        package_file = package[key]
        package_file_str = ET.tostring(package_file.Xml, encoding="utf-8", method="xml")
        zip_file.writestr(package[key].Filename, package_file_str)
    zip_file.close()
    zip_bytes.seek(0)
    return zip_bytes.read()


def collect_package(path: str, collect_dependency_macros: bool = True) -> Dict[str, PackageFile]:
    path = path.lower()
    macro_paths = __generate_macro_paths(path)
    package: Dict[str, PackageFile] = {}
    filename = os.path.basename(path)
    parent = __collect_workflow(path, package, filename)
    if collect_dependency_macros:
        __collect_macros(parent, package, macro_paths)
    return package


def __generate_macro_paths(workflow_path: str) -> List[str]:
    paths: List[str] = []
    paths.append(os.path.dirname(workflow_path))
    return paths


def __collect_workflow(path: str, package: Dict[str, PackageFile], filename: str) -> ET.Element:
    contents = __read_file_to_string(path)
    parser = ET.XMLParser(remove_blank_text=True)
    xml: ET.Element = ET.XML(contents, parser)
    package[path] = PackageFile(filename, xml)
    return xml


def __read_file_to_string(path: str) -> str:
    with open(path, 'rt') as file:
        return file.read()


def __collect_macros(parent: ET.Element, package: Dict[str, PackageFile], macro_paths: List[str]):
    for node in parent.find('Nodes'):
        __collect_node(node, package, macro_paths)
        __collect_child_nodes(node, package, macro_paths)


def __collect_child_nodes(node: ET.Element, package: Dict[str, PackageFile], macro_paths: List[str]):
    child_nodes = node.find("ChildNodes")
    if child_nodes is not None:
        for child in child_nodes:
            __collect_node(child, package, macro_paths)


def __collect_node(node: ET.Element, package: Dict[str, PackageFile], macro_paths: List[str]):
    engine = node.find('EngineSettings')
    if engine is not None:
        macro = engine.get('Macro')
        if macro is not None:
            abs_path = __generate_absolute_path(macro, macro_paths)
            if abs_path == '':
                return
            filename = __calculate_filename(abs_path, package)
            engine.set('Macro', os.path.join('.', filename))
            if abs_path in package:
                return
            xml = __collect_workflow(abs_path, package, filename)
            __collect_macros(xml, package, macro_paths)


def __generate_absolute_path(path: str, macro_paths: List[str]) -> str:
    if os.path.isabs(path) and os.path.exists(path):
        return path.lower()
    for macro_path in macro_paths:
        abs_path = os.path.normpath(os.path.join(macro_path, path))
        if os.path.exists(abs_path):
            return abs_path.lower()
    return ""


def __calculate_filename(abs_path: str, package: Dict[str, PackageFile]) -> str:
    filename = os.path.basename(abs_path)
    collision_count = 0
    for key in package.keys():
        key_filename = os.path.basename(key)
        if filename == key_filename:
            collision_count += 1
    if collision_count > 0:
        filename_split = os.path.splitext(filename)
        filename = str(collision_count+1).join(filename_split)

    return filename
