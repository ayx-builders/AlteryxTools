import unittest
import os
import xml

from CollectPackage import collect_package
import CollectPackageTestCases as Cases


class CollectPackageTests(unittest.TestCase):
    def test_CollectWithoutMacros(self):
        path = os.path.join(absroot, "No Macros.yxmd")
        package = collect_package(path)
        self.assertEqual(1, len(package))
        self.assertIsNot(None, package[path.lower()])
        self.assertEqual("no macros.yxmd", package[path.lower()].Filename)

    def test_CollectWithSingleMacro(self):
        path = os.path.join(absroot, "Single Absolute Macro.yxmd")
        macro_path = os.path.join(absroot, "Macro.yxmc").lower()
        package = collect_package(path)
        self.assertEqual(2, len(package))
        self.assertIsNot(None, package[path.lower()])
        self.assertIsNot(None, package[macro_path])
        self.assertEqual("single absolute macro.yxmd", package[path.lower()].Filename)
        self.assertEqual("macro.yxmc", package[macro_path].Filename)

    def test_CollectWithSingleMacroContainer(self):
        path = os.path.join(absroot, "Single Absolute Macro Container.yxmd")
        macro_path = os.path.join(absroot, "Macro.yxmc").lower()
        package = collect_package(path)
        self.assertEqual(2, len(package))
        self.assertIsNot(None, package[path.lower()])
        self.assertIsNot(None, package[macro_path])
        self.assertEqual("single absolute macro container.yxmd", package[path.lower()].Filename)
        self.assertEqual("macro.yxmc", package[macro_path].Filename)

    def test_CollectWithSingleRelativeMacro(self):
        path = os.path.join(absroot, "Single Relative Macro.yxmd").lower()
        macro_path = os.path.join(absroot, "Macro.yxmc").lower()
        package = collect_package(path)
        self.assertEqual(2, len(package))
        self.assertIsNot(None, package[macro_path])
        self.assertEqual("macro.yxmc", package[macro_path].Filename)

    def test_CollectWithSingleInvalidRelativeMacro(self):
        path = os.path.join(absroot, "Single Relative Macro Invalid.yxmd")
        package = collect_package(path)
        self.assertEqual(1, len(package))

    def test_CollectWithSingleInvalidAbsoluteMacro(self):
        path = os.path.join(absroot, "Single Absolute Macro Invalid.yxmd")
        package = collect_package(path)
        self.assertEqual(1, len(package))

    def test_CollectWithSingleMacroNoDependencies(self):
        path = os.path.join(absroot, "Single Absolute Macro.yxmd")
        package = collect_package(path, False)
        self.assertEqual(1, len(package))

    def test_CollectWithMacroNameCollision(self):
        path = os.path.join(absroot, "Macro Name Collision.yxmd")
        macro_path1 = os.path.join(absroot, "Macro.yxmc").lower()
        macro_path2 = os.path.join(absroot, os.path.join("Macros", "Macro.yxmc")).lower()
        package = collect_package(path)
        workflow_contents = xml.etree.ElementTree.tostring(package[path.lower()].Xml, encoding='unicode', method='xml')
        self.assertTrue(workflow_contents.find(".\\macro2.yxmc") != -1)
        self.assertEqual(3, len(package))
        self.assertEqual("macro.yxmc", package[macro_path1].Filename)
        self.assertEqual("macro2.yxmc", package[macro_path2].Filename)



def __write_test_case(path: str, contents: str):
    with open(os.path.join(absroot, path), 'w') as file:
        file.write(contents)


absroot = os.path.abspath("TestCases")
__write_test_case("Single Absolute Macro.yxmd", Cases.single_absolute_macro)
__write_test_case("Single Absolute Macro Container.yxmd", Cases.single_absolute_macro_container)
__write_test_case("Single Absolute Macro Invalid.yxmd", Cases.single_absolute_macro_invalid)


if __name__ == '__main__':
    unittest.main()
