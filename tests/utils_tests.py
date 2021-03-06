import os
import shutil
import unittest
from lib.utils import *

class SelectListTests(unittest.TestCase):

    def setUp(self):
        self.ds = [ '/tmp/bakery_tests_1',
                    '/tmp/bakery_tests_2', ]
        self.sd = [
                    [ '01-image1', '04-image4', '05-image5' ],
                    [ '02-image2', '03-image3' ],
                  ]
        self.post = [ [ 3, 0, 0 ], [ 0, 0 ] ]
        self.tearDown()
        for i in range(len(self.ds)):
            os.makedirs(self.ds[i])
            #for img in self.sd[i]:
                #os.makedirs(self.ds[i] + '/' + img)
                #open(self.ds[i] + '/' + img + '/' + img + '.img.gz', 'a').close()
            for j in range(len(self.sd[i])):
                dr = self.ds[i] + '/' + self.sd[i][j]
                os.makedirs(self.ds[i] + '/' + self.sd[i][j])
                open(dr + '/' + self.sd[i][j] + '.img.gz', 'a').close()
                for k in range(self.post[i][j]):
                    open(dr + '/' + self.sd[i][j] + '.post.' + str(k), 'a').close()

    def tearDown(self):
        for i in range(len(self.ds)):
            try:
                shutil.rmtree(self.ds[i])
            except OSError as e:
                pass

    def test_create_with_one_dir(self):
        sdi = disk_image_list(self.ds[0])
        self.assertEqual(len(sdi),3)
        self.assertEqual(sdi[0].name,'01-image1')
        self.assertEqual(sdi[0].directory,'/tmp/bakery_tests_1/01-image1')
        self.assertEqual(sdi[1].name,'04-image4')
        self.assertEqual(sdi[1].directory,'/tmp/bakery_tests_1/04-image4')
        self.assertEqual(sdi[2].name,'05-image5')
        self.assertEqual(sdi[2].directory,'/tmp/bakery_tests_1/05-image5')

    def test_create_with_two_dirs(self):
        sdi = disk_image_list(*self.ds)
        self.assertEqual(len(sdi),5)
        self.assertEqual(sdi[0].name,'01-image1')
        self.assertEqual(sdi[0].directory,'/tmp/bakery_tests_1/01-image1')
        self.assertEqual(sdi[1].name,'02-image2')
        self.assertEqual(sdi[1].directory,'/tmp/bakery_tests_2/02-image2')
        self.assertEqual(sdi[2].name,'03-image3')
        self.assertEqual(sdi[2].directory,'/tmp/bakery_tests_2/03-image3')
        self.assertEqual(sdi[3].name,'04-image4')
        self.assertEqual(sdi[3].directory,'/tmp/bakery_tests_1/04-image4')
        self.assertEqual(sdi[4].name,'05-image5')
        self.assertEqual(sdi[4].directory,'/tmp/bakery_tests_1/05-image5')

    def test_get_first_image(self):
        sdi = disk_image_list(*self.ds)
        self.assertEqual(sdi.current(), '01-image1')

    def test_get_next_image(self):
        sdi = disk_image_list(*self.ds)
        self.assertEqual(sdi.next(), '02-image2')
        self.assertEqual(sdi.current(), '02-image2')
        self.assertEqual(sdi.next(), '03-image3')
        self.assertEqual(sdi.current(), '03-image3')
        self.assertEqual(sdi.next(), '04-image4')
        self.assertEqual(sdi.current(), '04-image4')
        self.assertEqual(sdi.next(), '05-image5')
        self.assertEqual(sdi.current(), '05-image5')
        self.assertEqual(sdi.next(), '01-image1')
        self.assertEqual(sdi.current(), '01-image1')

    def test_get_prev_image(self):
        sdi = disk_image_list(*self.ds)
        self.assertEqual(sdi.prev(), '05-image5')
        self.assertEqual(sdi.current(), '05-image5')
        self.assertEqual(sdi.prev(), '04-image4')
        self.assertEqual(sdi.current(), '04-image4')
        self.assertEqual(sdi.prev(), '03-image3')
        self.assertEqual(sdi.current(), '03-image3')
        self.assertEqual(sdi.prev(), '02-image2')
        self.assertEqual(sdi.current(), '02-image2')
        self.assertEqual(sdi.prev(), '01-image1')
        self.assertEqual(sdi.current(), '01-image1')

    # These tests need re-writing. SelectList no long knows about images
    #def test_no_image_selected(self):
    #    sdi = disk_image_list(*self.ds)
    #    self.assertIsNone(sdi.selected_image_file())

    #def test_select_image(self):
    #    sdi = disk_image_list(*self.ds)
    #    sdi.select()
    #    self.assertEqual(sdi.selected_image_file(), '/tmp/bakery_tests_1/01-image1/01-image1.img.gz')

    #def test_select_image_then_change(self):
    #    sdi = disk_image_list(*self.ds)
    #    sdi.select()
    #    sdi.next()
    #    self.assertEqual(sdi.selected_image_file(), '/tmp/bakery_tests_1/01-image1/01-image1.img.gz')

    #def test_select_image_then_change_select_new(self):
    #    sdi = disk_image_list(*self.ds)
    #    sdi.select()
    #    sdi.next()
    #    sdi.select()
    #    self.assertEqual(sdi.selected_image_file(), '/tmp/bakery_tests_2/02-image2/02-image2.img.gz')

    #def test_select_deselect_image(self):
    #    sdi = disk_image_list(*self.ds)
    #    sdi.select()
    #    sdi.select()
    #    self.assertIsNone(sdi.selected_image_file())

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

    # These tests need re-writing. SelectList no long knows about images
    def test_post_script_list(self):
        sdi = disk_image_list(*self.ds)
        scripts = sdi.get_current().post_scripts()
        self.assertEqual(len(scripts), 3)
        for i in range(len(scripts)):
            self.assertEqual(scripts[i], '/tmp/bakery_tests_1/01-image1/01-image1.post.' + str(i))

    def test_no_post_scripts(self):
        sdi = disk_image_list(*self.ds)
        sdi.next()
        scripts = sdi.get_current().post_scripts()
        self.assertEqual(len(scripts), 0)

    def test_get_current(self):
        sdi = disk_image_list(*self.ds)
        item = sdi.get_current()
        self.assertIsInstance(item, DiskImage)
        self.assertEqual(str(item), '/tmp/bakery_tests_1/01-image1/01-image1.img.gz')

    def test_get_next_current(self):
        sdi = disk_image_list(*self.ds)
        sdi.next()
        self.assertEqual(str(sdi.get_current()), '/tmp/bakery_tests_2/02-image2/02-image2.img.gz')
        sdi.next()
        self.assertEqual(str(sdi.get_current()), '/tmp/bakery_tests_2/03-image3/03-image3.img.gz')
        sdi.next()
        self.assertEqual(str(sdi.get_current()), '/tmp/bakery_tests_1/04-image4/04-image4.img.gz')
        sdi.next()
        self.assertEqual(str(sdi.get_current()), '/tmp/bakery_tests_1/05-image5/05-image5.img.gz')

    def test_get_prev_current(self):
        sdi = disk_image_list(*self.ds)
        sdi.prev()
        self.assertEqual(str(sdi.get_current()), '/tmp/bakery_tests_1/05-image5/05-image5.img.gz')
        sdi.prev()
        self.assertEqual(str(sdi.get_current()), '/tmp/bakery_tests_1/04-image4/04-image4.img.gz')
        sdi.prev()
        self.assertEqual(str(sdi.get_current()), '/tmp/bakery_tests_2/03-image3/03-image3.img.gz')
        sdi.prev()
        self.assertEqual(str(sdi.get_current()), '/tmp/bakery_tests_2/02-image2/02-image2.img.gz')
