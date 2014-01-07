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
        #sdi = SelectList(self.ds[0])
        sdi = disk_image_list(self.ds[0])
        self.assertEqual(len(sdi),3)
        self.assertEqual(sdi[0].name,'01-image1.img')
        self.assertEqual(sdi[0].directory,'/tmp/bakery_tests_1')
        self.assertEqual(sdi[1].name,'04-image4.img')
        self.assertEqual(sdi[1].directory,'/tmp/bakery_tests_1')
        self.assertEqual(sdi[2].name,'05-image5.img')
        self.assertEqual(sdi[2].directory,'/tmp/bakery_tests_1')

    def test_create_with_two_dirs(self):
        #sdi = SelectList(*self.ds)
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
        #sdi = SelectList(*self.ds)
        sdi = disk_image_list(*self.ds)
        self.assertEqual(sdi.current(), '[ ] 01-image1.img')

    def test_get_next_image(self):
        #sdi = SelectList(*self.ds)
        sdi = disk_image_list(*self.ds)
        self.assertEqual(sdi.next(), '[ ] 02-image2.img')
        self.assertEqual(sdi.current(), '[ ] 02-image2.img')
        self.assertEqual(sdi.next(), '[ ] 03-image3.img')
        self.assertEqual(sdi.current(), '[ ] 03-image3.img')
        self.assertEqual(sdi.next(), '[ ] 04-image4.img')
        self.assertEqual(sdi.current(), '[ ] 04-image4.img')
        self.assertEqual(sdi.next(), '[ ] 05-image5.img')
        self.assertEqual(sdi.current(), '[ ] 05-image5.img')
        self.assertEqual(sdi.next(), '[ ] 01-image1.img')
        self.assertEqual(sdi.current(), '[ ] 01-image1.img')

    def test_get_prev_image(self):
        #sdi = SelectList(*self.ds)
        sdi = disk_image_list(*self.ds)
        self.assertEqual(sdi.prev(), '[ ] 05-image5.img')
        self.assertEqual(sdi.current(), '[ ] 05-image5.img')
        self.assertEqual(sdi.prev(), '[ ] 04-image4.img')
        self.assertEqual(sdi.current(), '[ ] 04-image4.img')
        self.assertEqual(sdi.prev(), '[ ] 03-image3.img')
        self.assertEqual(sdi.current(), '[ ] 03-image3.img')
        self.assertEqual(sdi.prev(), '[ ] 02-image2.img')
        self.assertEqual(sdi.current(), '[ ] 02-image2.img')
        self.assertEqual(sdi.prev(), '[ ] 01-image1.img')
        self.assertEqual(sdi.current(), '[ ] 01-image1.img')

if __name__ == '__main__':
    unittest.main()
