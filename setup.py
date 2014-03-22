from setuptools import setup
    
setup(
    name = "httpdo",
    py_modules = ["httpdo"],
    scripts = ["httpdo.py"],
    zip_safe=False,
    version = "0.3",
    license = "LGPL",
    install_requires=["tornado", "baker"],
    description = "a scriptable httpd",
    author = "karasuyamatengu",
    author_email = "karasuyamatengu@gmail.com",
    url = "https://github.com/tengu/py-httpdo",
    keywords = [],
    classifiers = [
        "License :: OSI Approved :: GNU Library or Lesser General Public License (LGPL)",
        "Programming Language :: Python",
        "Development Status :: 4 - Beta",
        "Environment :: Console",
        ],
    # long_description = """"""
    )
