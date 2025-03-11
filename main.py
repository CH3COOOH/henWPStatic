import sys

from henWPStatic import HWPSTC

if __name__ == '__main__':
	homepage = sys.argv[1]
	sitemap = sys.argv[2]
	saveto = sys.argv[3]

	hwpstc = HWPSTC(homepage, sitemap, saveto)
	hwpstc.start()