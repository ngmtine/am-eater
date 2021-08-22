from setuptools import setup, find_packages

setup(
	name = "AmEater",
	version = "0.0.1",
	packages = find_packages(),
    author = "ngmtine",
    url = "https://github.com/ngmtine/am-eater",
	description = "Downloader for am-our.com",
	long_description = open('README.md').read(),
	long_description_content_type = 'text/markdown',
	python_requires = ">=3.8.2",
	install_requires = ["requests", "beautifulsoup4", "lxml"],
	package_data = {"AmEater": ["settings.ini"]},
)