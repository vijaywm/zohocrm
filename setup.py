from setuptools import setup, find_packages

with open("requirements.txt") as f:
	install_requires = f.read().strip().split("\n")

# get version from __version__ variable in zohocrm/__init__.py
from zohocrm import __version__ as version

setup(
	name="zohocrm",
	version=version,
	description="Frappe ZohoCRM Integration",
	author="Biztech",
	author_email="admin@biztech-integration.com",
	packages=find_packages(),
	zip_safe=False,
	include_package_data=True,
	install_requires=install_requires
)
