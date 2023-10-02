# NOTE:
#   omni.kit.test - std python's unittest module with additional wrapping to add suport for async/await tests
#   For most things refer to unittest docs: https://docs.python.org/3/library/unittest.html
import omni.kit.test
import omni.usd

# Import extension python module we are testing with absolute import path, as if we are external user (other extension)
from pathlib import Path
from pxr import Usd, UsdGeom
import os
import asyncio


TEST_SERVER = "omniverse://kit-test-content.ov.nvidia.com/Projects/PointClouds/"


async def wait(count=20):
    for i in range(count):
        await omni.kit.app.get_app().next_update_async()

# Having a test class dervived from omni.kit.test.AsyncTestCase declared on the root of module will make it auto-discoverable by omni.kit.test
class Test(omni.kit.test.AsyncTestCase):
    # Before running each test
    async def setUp(self):
        pass

    # After running each test
    async def tearDown(self):
        pass

    def __set_omni_credentials(self):
        # Save the environment to be able to restore it
        self.__OMNI_USER = os.environ.get("OMNI_USER", None)
        self.__OMNI_PASS = os.environ.get("OMNI_PASS", None)

        username = os.getenv("OMNI_USER", default="test")
        password = os.getenv("OMNI_PASS", default=username)

        # Set the credentials
        os.environ["OMNI_USER"] = username
        os.environ["OMNI_PASS"] = password

    def __restore_omni_credentials(self):
        if self.__OMNI_USER is not None:
            os.environ["OMNI_USER"] = self.__OMNI_USER
        else:
            os.environ.pop("OMNI_USER")
        if self.__OMNI_PASS is not None:
            os.environ["OMNI_PASS"] = self.__OMNI_PASS
        else:
            os.environ.pop("OMNI_PASS")

    async def test_open(self):
        current_path = Path(__file__).parent
        data_path = current_path.parent.parent.parent.parent.joinpath("data")
        test_data_path = str(data_path.joinpath("bunnyDouble.e57"))
        self.assertTrue(os.path.exists(test_data_path))

        context = omni.usd.get_context()
        await context.open_stage_async(test_data_path)
        await wait()

        stage = context.get_stage()
        self.assertTrue(stage)

        xform_prim = stage.GetPrimAtPath("/data3D")
        self.assertTrue(xform_prim)

        prim = stage.GetPrimAtPath("/data3D/_0000_bunny/scan")
        self.assertTrue(prim)

    async def test_open_url(self):      # OM-93104
        # self.__set_omni_credentials()

        context = omni.usd.get_context()
        await context.open_stage_async(TEST_SERVER + "bunnyDouble.e57")
        await wait()

        stage = context.get_stage()
        self.assertTrue(stage)

        xform_prim = stage.GetPrimAtPath("/data3D")
        self.assertTrue(xform_prim)

        prim = stage.GetPrimAtPath("/data3D/_0000_bunny/scan")
        self.assertTrue(prim)

        # self.__restore_omni_credentials()

    async def test_interpolation_type(self):    # OM-72158
        current_path = Path(__file__).parent
        data_path = current_path.parent.parent.parent.parent.joinpath("data")
        test_data_path = str(data_path.joinpath("bunnyDouble.e57"))
        self.assertTrue(os.path.exists(test_data_path))

        context = omni.usd.get_context()
        await context.open_stage_async(test_data_path)
        await wait()

        stage = context.get_stage()
        self.assertTrue(stage)

        prim = stage.GetPrimAtPath("/data3D/_0000_bunny/scan")
        self.assertTrue(prim)

        attr = UsdGeom.Points(prim).GetDisplayColorAttr()
        self.assertTrue(attr)
        self.assertTrue(attr.HasValue())
        self.assertTrue(attr.HasMetadata("interpolation"))

        self.assertEqual(attr.GetMetadata("interpolation"), "vertex")
