import sys

from henWPStatic import HWPSTC

if __name__ == '__main__':
	homepage = sys.argv[1]
	sitemap = sys.argv[2]

	if len(sys.argv) == 3:
		hwpstc = HWPSTC(homepage, sitemap)
		hwpstc.start()
	elif len(sys.argv) == 4:
		if sys.argv[3] == 'dig':
			print('** Run in DIG mode **')
			hwpstc = HWPSTC(homepage, sitemap, dig=True)
			hwpstc.start()
		else:
			url = sys.argv[2]
			hwpstc = HWPSTC(homepage, sitemap)
			hwpstc.save_res_from_url(url)
			hwpstc.save_res_from_urls(hwpstc.get_res_urls(url))


		
	