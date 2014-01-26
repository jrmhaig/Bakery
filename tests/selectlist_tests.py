import os
import shutil
import unittest
from lib.selectlist import *

class SelectListTests(unittest.TestCase):

    def setUp(self):
        self.ds = [ '/tmp/bakery_tests_1',
                    '/tmp/bakery_tests_2', ]
        self.fs = [
                    [ '01-image1.img', '04-image4.img', '05-image5.img'],
                    [ '02-image2.img', '03-image3.img' ],
                  ]
        self.tearDown()
        for i in range(len(self.ds)):
            os.makedirs(self.ds[i])
            for fl in self.fs[i]:
                open(self.ds[i] + '/' + fl, 'a').close()

    def tearDown(self):
        for i in range(len(self.ds)):
            try:
                shutil.rmtree(self.ds[i])
            except OSError as e:
                pass

    def test_create_with_one_dir(self):
        sdi = disk_image_list(self.ds[0])
        self.assertEqual(len(sdi),3)
        self.assertEqual(sdi[0].name,'01-image1.img')
        self.assertEqual(sdi[0].directory,'/tmp/bakery_tests_1')
        self.assertEqual(sdi[1].name,'04-image4.img')
        self.assertEqual(sdi[1].directory,'/tmp/bakery_tests_1')
        self.assertEqual(sdi[2].name,'05-image5.img')
        self.assertEqual(sdi[2].directory,'/tmp/bakery_tests_1')

    def test_create_with_two_dirs(self):
        sdi = disk_image_list(*self.ds)
        self.assertEqual(len(sdi),5)
        self.assertEqual(sdi[0].name,'01-image1.img')
        self.assertEqual(sdi[0].directory,'/tmp/bakery_tests_1')
        self.assertEqual(sdi[1].name,'02-image2.img')
        self.assertEqual(sdi[1].directory,'/tmp/bakery_tests_2')
        self.assertEqual(sdi[2].name,'03-image3.img')
        self.assertEqual(sdi[2].directory,'/tmp/bakery_tests_2')
        self.assertEqual(sdi[3].name,'04-image4.img')
        self.assertEqual(sdi[3].directory,'/tmp/bakery_tests_1')
        self.assertEqual(sdi[4].name,'05-image5.img')
        self.assertEqual(sdi[4].directory,'/tmp/bakery_tests_1')

    def test_get_first_image(self):
        sdi = disk_image_list(*self.ds)
        self.assertEqual(sdi.current(), '01-image1.img')

    def test_get_next_image(self):
        sdi = disk_image_list(*self.ds)
        self.assertEqual(sdi.next(), '02-image2.img')
        self.assertEqual(sdi.current(), '02-image2.img')
        self.assertEqual(sdi.next(), '03-image3.img')
        self.assertEqual(sdi.current(), '03-image3.img')
        self.assertEqual(sdi.next(), '04-image4.img')
        self.assertEqual(sdi.current(), '04-image4.img')
        self.assertEqual(sdi.next(), '05-image5.img')
        self.assertEqual(sdi.current(), '05-image5.img')
        self.assertEqual(sdi.next(), '01-image1.img')
        self.assertEqual(sdi.current(), '01-image1.img')

    def test_get_prev_image(self):
        sdi = disk_image_list(*self.ds)
        self.assertEqual(sdi.prev(), '05-image5.img')
        self.assertEqual(sdi.current(), '05-image5.img')
        self.assertEqual(sdi.prev(), '04-image4.img')
        self.assertEqual(sdi.current(), '04-image4.img')
        self.assertEqual(sdi.prev(), '03-image3.img')
        self.assertEqual(sdi.current(), '03-image3.img')
        self.assertEqual(sdi.prev(), '02-image2.img')
        self.assertEqual(sdi.current(), '02-image2.img')
        self.assertEqual(sdi.prev(), '01-image1.img')
        self.assertEqual(sdi.current(), '01-image1.img')

    def test_no_image_selected(self):
        sdi = disk_image_list(*self.ds)
        self.assertIsNone(sdi.selected_full_path())

    def test_select_image(self):
        sdi = disk_image_list(*self.ds)
        sdi.select()
        self.assertEqual(sdi.selected_full_path(), '/tmp/bakery_tests_1/01-image1.img')

    def test_select_image_then_change(self):
        sdi = disk_image_list(*self.ds)
        sdi.select()
        sdi.next()
        self.assertEqual(sdi.selected_full_path(), '/tmp/bakery_tests_1/01-image1.img')

    def test_select_image_then_change_select_new(self):
        sdi = disk_image_list(*self.ds)
        sdi.select()
        sdi.next()
        sdi.select()
        self.assertEqual(sdi.selected_full_path(), '/tmp/bakery_tests_2/02-image2.img')

    def test_select_deselect_image(self):
        sdi = disk_image_list(*self.ds)
        sdi.select()
        sdi.select()
        self.assertIsNone(sdi.selected_full_path())

    def test_current_is_not_selected(self):
        sdi = disk_image_list(*self.ds)
        self.assertFalse(sdi.current_is_selected())

    def test_current_is_selected(self):
        sdi = disk_image_list(*self.ds)
        sdi.select()
        self.assertTrue(sdi.current_is_selected())

    def test_current_is_not_selected_after_change(self):
        sdi = disk_image_list(*self.ds)
        sdi.select()
        sdi.next()
        self.assertFalse(sdi.current_is_selected())
